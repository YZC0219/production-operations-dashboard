import json, socket, threading
from pathlib import Path
from services.plc_collector import SETTINGS_PATH

_lock=threading.Lock()
DEFAULT_MAPPING={"status_byte":0,"actual_quantity_dint":2,"qualified_quantity_dint":6,"defective_quantity_dint":10}

def get_config():
    with _lock:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))

def save_config(data):
    interval=int(data.get("poll_interval_seconds",2))
    if not 1<=interval<=3600: raise ValueError("采集周期必须在1到3600秒之间。")
    devices=[]; codes=set()
    for item in data.get("devices",[]):
        code=str(item.get("machine_code","")).strip(); ip=str(item.get("ip","")).strip()
        if not code or not ip or code in codes: raise ValueError("设备编号和IP不能为空，设备编号不能重复。")
        codes.add(code); driver=item.get("driver","simulation")
        if driver not in ("simulation","s7"): raise ValueError("驱动类型只能是 simulation 或 s7。")
        devices.append({"enabled":bool(item.get("enabled",True)),"driver":driver,"machine_code":code,
          "name":str(item.get("name",code)),"ip":ip,"rack":int(item.get("rack",0)),"slot":int(item.get("slot",1)),
          "tcp_port":int(item.get("tcp_port",102)),"db_number":int(item.get("db_number",1)),
          "read_start":int(item.get("read_start",0)),"read_size":int(item.get("read_size",14)),
          "mapping":item.get("mapping") or DEFAULT_MAPPING.copy()})
    payload={"poll_interval_seconds":interval,"offline_after_seconds":max(interval*4,8),"devices":devices}
    temporary=SETTINGS_PATH.with_suffix(".tmp")
    with _lock:
        temporary.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        temporary.replace(SETTINGS_PATH)
    return payload

def test_tcp(ip,port=102,timeout=2):
    started=__import__('time').monotonic()
    try:
        with socket.create_connection((ip,int(port)),timeout=timeout): pass
        return {"success":True,"message":"TCP连接成功","latency_ms":round((__import__('time').monotonic()-started)*1000)}
    except OSError as exc:
        return {"success":False,"message":f"连接失败：{exc}","latency_ms":None}
