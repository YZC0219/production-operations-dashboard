"""S7-1200 实时数据采集服务。

默认使用 simulation 驱动，方便在没有 PLC 时验证整套实时链路。
现场调试完成后，把 settings/plc_devices.json 中 driver 改为 s7 即可。
本服务只读取 PLC，不执行任何写入操作。
"""
import json
import random
import struct
import threading
import time
from datetime import datetime
from pathlib import Path

from database import transaction

SETTINGS_PATH = Path(__file__).resolve().parents[1] / "settings" / "plc_devices.json"
STATUS_MAP = {1: "运行", 2: "停机", 3: "故障"}


def load_settings():
    with SETTINGS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def decode_s7_data(raw, mapping):
    """按西门子大端字节序解析 DB 数据。"""
    status = STATUS_MAP.get(raw[mapping["status_byte"]], "停机")
    return {
        "status": status,
        "actual_quantity": struct.unpack_from(">i", raw, mapping["actual_quantity_dint"])[0],
        "qualified_quantity": struct.unpack_from(">i", raw, mapping["qualified_quantity_dint"])[0],
        "defective_quantity": struct.unpack_from(">i", raw, mapping["defective_quantity_dint"])[0],
        "fault_code": 1 if status == "故障" else 0,
    }


class PLCCollector:
    def __init__(self):
        self._thread = None
        self._stop = threading.Event()
        self._clients = {}
        self._simulation = {}

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="plc-collector", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        for client in self._clients.values():
            try: client.disconnect()
            except Exception: pass
        self._clients.clear()

    def _read_simulation(self, device):
        code = device["machine_code"]
        state = self._simulation.setdefault(code, {"actual": 80, "defective": 2})
        state["actual"] += random.choice([0, 0, 1, 1, 2])
        if random.random() < 0.03: state["defective"] += 1
        return {"status": "运行", "actual_quantity": state["actual"],
                "qualified_quantity": max(0, state["actual"]-state["defective"]),
                "defective_quantity": state["defective"], "fault_code": 0}

    def _read_s7(self, device):
        try:
            from s7 import Client
        except ImportError as exc:
            raise RuntimeError("未安装 python-snap7，请重新安装 requirements.txt") from exc
        code = device["machine_code"]
        client = self._clients.get(code)
        if client is None:
            client = Client(auto_reconnect=True, max_retries=2)
            client.connect(device["ip"], device.get("rack", 0), device.get("slot", 1),
                           tcp_port=device.get("tcp_port", 102))
            self._clients[code] = client
        raw = client.db_read(device["db_number"], device.get("read_start", 0), device["read_size"])
        return decode_s7_data(raw, device["mapping"])

    def _save(self, device, values, connection="在线", error=""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        source = "PLC" if device["driver"] == "s7" else "模拟"
        with transaction() as conn:
            conn.execute("""INSERT INTO machine_realtime
                (machine_code,status,actual_quantity,qualified_quantity,defective_quantity,fault_code,collected_at,data_source,connection_status,last_error)
                VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(machine_code) DO UPDATE SET
                status=excluded.status,actual_quantity=excluded.actual_quantity,
                qualified_quantity=excluded.qualified_quantity,defective_quantity=excluded.defective_quantity,
                fault_code=excluded.fault_code,collected_at=excluded.collected_at,
                data_source=excluded.data_source,connection_status=excluded.connection_status,last_error=excluded.last_error""",
                (device["machine_code"], values["status"], values["actual_quantity"],
                 values["qualified_quantity"], values["defective_quantity"], values["fault_code"],
                 now, source, connection, error))
            conn.execute("UPDATE machines SET status=?,updated_at=? WHERE machine_code=?",
                         (values["status"], now, device["machine_code"]))
            conn.execute("INSERT INTO machine_samples(machine_code,status,actual_quantity,qualified_quantity,defective_quantity,connection_status,collected_at) VALUES(?,?,?,?,?,?,?)",
                         (device["machine_code"],values["status"],values["actual_quantity"],values["qualified_quantity"],values["defective_quantity"],connection,now))
            conn.execute("DELETE FROM machine_samples WHERE collected_at<datetime('now','localtime','-90 days')")
        from services.alarm_service import evaluate
        evaluate(device["machine_code"],values["status"],connection,values["fault_code"])

    def _save_error(self, device, message):
        previous = {"status":"故障", "actual_quantity":0, "qualified_quantity":0,
                    "defective_quantity":0, "fault_code":-1}
        self._clients.pop(device["machine_code"], None)
        self._save(device, previous, "离线", str(message)[:200])

    def collect_once(self):
        settings = load_settings()
        for device in settings.get("devices", []):
            if not device.get("enabled", False): continue
            try:
                values = self._read_s7(device) if device["driver"] == "s7" else self._read_simulation(device)
                self._save(device, values)
            except Exception as exc:
                self._save_error(device, exc)

    def _run(self):
        while not self._stop.is_set():
            started = time.monotonic()
            try: self.collect_once()
            except Exception: pass
            interval = load_settings().get("poll_interval_seconds", 2)
            self._stop.wait(max(0.2, interval - (time.monotonic()-started)))


collector = PLCCollector()
