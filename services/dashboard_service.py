from datetime import date, timedelta
from database import connect
from services.calculations import quality_rate, defective_rate, completion_rate, inventory_status, order_warning

def rows(sql,args=()):
    c=connect()
    try: return [dict(x) for x in c.execute(sql,args).fetchall()]
    finally: c.close()

def summary():
    today=date.today().isoformat(); ms=rows("SELECT status,COUNT(*) count FROM machines GROUP BY status")
    statuses={x['status']:x['count'] for x in ms}; prod=rows("SELECT COALESCE(SUM(planned_quantity),0) p,COALESCE(SUM(actual_quantity),0) a,COALESCE(SUM(qualified_quantity),0) q,COALESCE(SUM(defective_quantity),0) d FROM production_records WHERE record_date=?",(today,))[0]
    orders=rows("SELECT COUNT(*) count FROM orders WHERE status!='已完成'")[0]['count']
    inv=sum(inventory_status(x['current_stock'],x['safety_stock'],x['maximum_stock'])!='正常' for x in rows("SELECT * FROM inventory"))
    return {"设备总数":sum(statuses.values()),"运行设备数":statuses.get("运行",0),"停机设备数":statuses.get("停机",0),"故障设备数":statuses.get("故障",0),"今日计划产量":prod['p'],"今日实际产量":prod['a'],"今日合格率":quality_rate(prod['q'],prod['a']),"今日报废率":defective_rate(prod['d'],prod['a']),"未完成订单数":orders,"库存预警数量":inv}

def dashboard_data():
    today=date.today(); start=(today-timedelta(days=6)).isoformat()
    machines=rows("SELECT m.machine_code,m.machine_name,m.status,COALESCE(SUM(r.actual_quantity),0) value FROM machines m LEFT JOIN production_records r ON m.machine_code=r.machine_code AND r.record_date=? GROUP BY m.machine_code",(today.isoformat(),))
    trend=rows("SELECT record_date, SUM(planned_quantity) planned,SUM(actual_quantity) actual,SUM(qualified_quantity) qualified,SUM(defective_quantity) defective FROM production_records WHERE record_date>=? GROUP BY record_date ORDER BY record_date",(start,))
    for x in trend: x.update(quality=quality_rate(x['qualified'],x['actual']),defective_rate=defective_rate(x['defective'],x['actual']))
    order_dist=rows("SELECT status name,COUNT(*) value FROM orders GROUP BY status")
    inv_dist=rows("SELECT material_type name,SUM(current_stock) value FROM inventory GROUP BY material_type")
    return {"summary":summary(),"machines":machines,"trend":trend,"orders":order_dist,"inventory":inv_dist}

def machine_list():
    data=rows("""SELECT m.*,w.workshop_name,
      COALESCE(r.planned_quantity,0) planned_quantity,
      COALESCE(rt.actual_quantity,r.actual_quantity,0) actual_quantity,
      COALESCE(rt.qualified_quantity,r.qualified_quantity,0) qualified_quantity,
      COALESCE(rt.defective_quantity,r.defective_quantity,0) defective_quantity,
      COALESCE(rt.data_source,'数据库') data_source,
      COALESCE(rt.connection_status,'未配置') connection_status,
      COALESCE(rt.collected_at,m.updated_at) collected_at,
      COALESCE(rt.last_error,'') last_error
      FROM machines m LEFT JOIN workshops w ON m.workshop_code=w.workshop_code
      LEFT JOIN production_records r ON m.machine_code=r.machine_code AND r.record_date=?
      LEFT JOIN machine_realtime rt ON m.machine_code=rt.machine_code ORDER BY m.machine_code""",(date.today().isoformat(),))
    for x in data: x.update(quality_rate=quality_rate(x['qualified_quantity'],x['actual_quantity']),defective_rate=defective_rate(x['defective_quantity'],x['actual_quantity']))
    return data

def realtime_status():
    return rows("SELECT * FROM machine_realtime ORDER BY machine_code")

def plan_list():
    data=rows("SELECT p.*,pr.product_name FROM production_plans p LEFT JOIN products pr ON p.product_code=pr.product_code ORDER BY plan_date DESC")
    for x in data: x['completion_rate']=completion_rate(x['completed_quantity'],x['planned_quantity'])
    return data

def order_list():
    data=rows("SELECT o.*,p.product_name FROM orders o LEFT JOIN products p ON o.product_code=p.product_code ORDER BY delivery_date")
    for x in data: x['warning'],x['remaining_days']=order_warning(x['delivery_date'],x['status'])
    return data

def inventory_list():
    data=rows("SELECT * FROM inventory ORDER BY material_code")
    for x in data: x['inventory_status']=inventory_status(x['current_stock'],x['safety_stock'],x['maximum_stock'])
    return data
