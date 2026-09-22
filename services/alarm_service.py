from datetime import datetime
from database import connect,transaction

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def evaluate(machine_code,status,connection,fault_code=0):
    conditions=[]
    if connection=="离线": conditions.append(("离线","严重",f"{machine_code} PLC通信中断"))
    if status=="故障" or fault_code>0: conditions.append(("设备故障","严重",f"{machine_code} 设备故障，代码 {fault_code}"))
    active_keys=set()
    with transaction() as c:
        for alarm_type,level,message in conditions:
            key=f"{machine_code}:{alarm_type}"; active_keys.add(key)
            c.execute("""INSERT INTO alarms(alarm_key,machine_code,alarm_type,level,message,status,started_at)
              VALUES(?,?,?,?,?,'活动',?) ON CONFLICT(alarm_key) DO UPDATE SET
              message=excluded.message,level=excluded.level,
              status=CASE WHEN alarms.status='已恢复' THEN '活动' ELSE alarms.status END,
              started_at=CASE WHEN alarms.status='已恢复' THEN excluded.started_at ELSE alarms.started_at END,
              recovered_at=CASE WHEN alarms.status='已恢复' THEN NULL ELSE alarms.recovered_at END""",
              (key,machine_code,alarm_type,level,message,now()))
        rows=c.execute("SELECT alarm_key FROM alarms WHERE machine_code=? AND status!='已恢复'",(machine_code,)).fetchall()
        for row in rows:
            if row[0] not in active_keys: c.execute("UPDATE alarms SET status='已恢复',recovered_at=? WHERE alarm_key=?",(now(),row[0]))

def list_alarms():
    c=connect()
    try:return [dict(x) for x in c.execute("SELECT * FROM alarms ORDER BY CASE status WHEN '活动' THEN 0 WHEN '已确认' THEN 1 ELSE 2 END,id DESC LIMIT 500")]
    finally:c.close()

def acknowledge(alarm_id,username,note):
    with transaction() as c:
        c.execute("UPDATE alarms SET status=CASE WHEN status='活动' THEN '已确认' ELSE status END,acknowledged_at=?,acknowledged_by=?,handling_note=? WHERE id=?",
                  (now(),username,str(note)[:300],alarm_id))

def oee_data():
    c=connect()
    try:
        machines=[dict(x) for x in c.execute("SELECT machine_code,machine_name FROM machines ORDER BY machine_code")]
        for m in machines:
            samples=c.execute("SELECT status,actual_quantity,qualified_quantity,defective_quantity,collected_at FROM machine_samples WHERE machine_code=? AND collected_at>=datetime('now','localtime','-24 hours') ORDER BY id",(m['machine_code'],)).fetchall()
            total=len(samples); running=sum(x['status']=='运行' for x in samples)
            last=samples[-1] if samples else None
            planned=c.execute("SELECT COALESCE(SUM(planned_quantity),0) FROM production_records WHERE machine_code=? AND record_date=date('now','localtime')",(m['machine_code'],)).fetchone()[0]
            actual=last['actual_quantity'] if last else 0; qualified=last['qualified_quantity'] if last else 0
            availability=round(running/total*100,2) if total else 0
            performance=round(min(actual/planned,1)*100,2) if planned else 0
            quality=round(qualified/actual*100,2) if actual else 0
            m.update(availability=availability,performance=performance,quality=quality,oee=round(availability*performance*quality/10000,2),samples=total)
        return machines
    finally:c.close()
