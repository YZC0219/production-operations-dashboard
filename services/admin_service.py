import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
from config import BASE_DIR,DATABASE_PATH
from database import connect,transaction

MASTER={
 "workshops":(["workshop_code","workshop_name"],"workshop_code"),
 "products":(["product_code","product_name","product_category","unit"],"product_code"),
 "machines":(["machine_code","machine_name","workshop_code","status","current_product","updated_at"],"machine_code")}

def master_data():
    c=connect()
    try: return {t:[dict(x) for x in c.execute(f"SELECT * FROM {t} ORDER BY {key}")] for t,(_,key) in MASTER.items()}
    finally:c.close()

def save_master(table,data):
    if table not in MASTER: raise ValueError("不支持的主数据类型。")
    cols,key=MASTER[table]; vals=[str(data.get(x,"")).strip() for x in cols]
    if not vals[0]: raise ValueError("编号不能为空。")
    assigns=",".join(f"{x}=excluded.{x}" for x in cols if x!=key)
    with transaction() as c: c.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?'*len(cols))}) ON CONFLICT({key}) DO UPDATE SET {assigns}",vals)
    return vals[0]

def logs(limit=500):
    c=connect()
    try:return [dict(x) for x in c.execute("SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?",(limit,))]
    finally:c.close()

def export_report(report):
    queries={"machines":"SELECT * FROM machines","production":"SELECT * FROM production_records","plans":"SELECT * FROM production_plans","orders":"SELECT * FROM orders","inventory":"SELECT * FROM inventory","audit":"SELECT * FROM operation_logs ORDER BY id DESC"}
    if report not in queries: raise ValueError("未知报表类型。")
    export_dir=BASE_DIR/"exports"; export_dir.mkdir(exist_ok=True)
    path=export_dir/f"{report}_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    c=connect()
    try: pd.read_sql_query(queries[report],c).to_excel(path,index=False)
    finally:c.close()
    return path

def create_backup():
    folder=BASE_DIR/"backups"; folder.mkdir(exist_ok=True)
    path=folder/f"production_{datetime.now():%Y%m%d_%H%M%S}.db"
    source=connect(); target=__import__('sqlite3').connect(path)
    try: source.backup(target)
    finally: source.close(); target.close()
    return path

def security_checks():
    c=connect()
    try:
        admins=c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND enabled=1").fetchone()[0]
        forced=c.execute("SELECT COUNT(*) FROM users WHERE must_change_password=1").fetchone()[0]
        logs_count=c.execute("SELECT COUNT(*) FROM operation_logs").fetchone()[0]
    finally:c.close()
    backups=list((BASE_DIR/"backups").glob("*.db")) if (BASE_DIR/"backups").exists() else []
    return [{"item":"有效管理员账户","ok":admins>0,"detail":f"{admins} 个"},{"item":"需要修改初始密码","ok":forced==0,"detail":f"{forced} 个账户"},{"item":"操作审计记录","ok":logs_count>0,"detail":f"{logs_count} 条"},{"item":"数据库备份","ok":bool(backups),"detail":f"{len(backups)} 个"}]
