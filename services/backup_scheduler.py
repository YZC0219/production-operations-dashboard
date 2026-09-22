import json,threading,time
from datetime import datetime
from pathlib import Path
from config import BASE_DIR
from database import transaction
from services.admin_service import create_backup

CONFIG_PATH=BASE_DIR/"settings"/"backup.json"
DEFAULT={"enabled":True,"hour":2,"retention_days":30}

def load_backup_config():
    if not CONFIG_PATH.exists(): return DEFAULT.copy()
    return {**DEFAULT,**json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}

def save_backup_config(data):
    cfg={"enabled":bool(data.get("enabled",True)),"hour":int(data.get("hour",2)),"retention_days":int(data.get("retention_days",30))}
    if not 0<=cfg["hour"]<=23 or not 1<=cfg["retention_days"]<=365: raise ValueError("备份时间或保留天数无效。")
    CONFIG_PATH.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8"); return cfg

def run_backup():
    try:
        path=create_backup(); result="成功"; detail=str(path)
        cutoff=time.time()-load_backup_config()["retention_days"]*86400
        for old in path.parent.glob("production_*.db"):
            if old.stat().st_mtime<cutoff: old.unlink()
    except Exception as exc: result="失败"; detail=str(exc)
    with transaction() as c:c.execute("INSERT INTO backup_runs(filename,result,detail,created_at) VALUES(?,?,?,?)",(Path(detail).name if result=="成功" else "",result,detail,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

class BackupScheduler:
    def __init__(self):self.stop_event=threading.Event();self.thread=None;self.last_date=None
    def start(self):
        if self.thread and self.thread.is_alive():return
        self.thread=threading.Thread(target=self._run,daemon=True,name="backup-scheduler");self.thread.start()
    def _run(self):
        while not self.stop_event.wait(30):
            cfg=load_backup_config(); now=datetime.now(); today=now.date().isoformat()
            if cfg["enabled"] and now.hour==cfg["hour"] and self.last_date!=today: run_backup();self.last_date=today

scheduler=BackupScheduler()
