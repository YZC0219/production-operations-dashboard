import random, sys
from datetime import date, datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import init_database, transaction
from config import TEMPLATE_PATH
import pandas as pd

random.seed(20250921)
TODAY = date.today()
workshops = [("WS01","机加工车间"),("WS02","装配车间"),("WS03","包装车间")]
products = [(f"P{i:03d}", n, c, "件") for i,(n,c) in enumerate([
    ("精密齿轮","机械件"),("传动轴","机械件"),("铝合金外壳","结构件"),("控制面板","电子件"),
    ("液压阀","液压件"),("电机组件","组件"),("工业泵","成品"),("减速器","成品")],1)]

def make_data():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    machines=[]
    states=["运行"]*7+["停机"]*3+["故障"]*2
    for i in range(12):
        machines.append((f"M{i+1:03d}",f"{['数控机床','装配工位','包装设备'][i//4]}-{i%4+1}",workshops[i//4][0],states[i],products[i%8][1] if states[i]=="运行" else "",now))
    records=[]
    for d in range(30):
        day=(TODAY-timedelta(days=d)).isoformat()
        for i,m in enumerate(machines):
            plan=random.randint(70,150); actual=max(0,plan+random.randint(-25,12)); defect=random.randint(0,max(1,int(actual*.06)))
            records.append((day,m[0],products[i%8][0],plan,actual,actual-defect,defect,"08:00","17:00"))
    plans=[]
    pstatus=["未开始","生产中","已完成","延期"]
    for i in range(15):
        qty=random.randint(200,800); st=pstatus[i%4]; done={"未开始":0,"生产中":int(qty*.55),"已完成":qty,"延期":int(qty*.7)}[st]
        plans.append((f"PL{TODAY:%Y%m}{i+1:03d}",(TODAY+timedelta(days=i-4)).isoformat(),machines[i%12][0],products[i%8][0],qty,done,st))
    orders=[]
    ost=["待生产","生产中","待交付","已完成","已逾期"]
    for i in range(20):
        st=ost[i%5]; qty=random.randint(300,1500); produced=qty if st in ("待交付","已完成") else (0 if st=="待生产" else int(qty*.6)); delivered=qty if st=="已完成" else 0
        offset=-random.randint(1,8) if st=="已逾期" else (i%7-2)
        orders.append((f"SO{TODAY:%Y%m}{i+1:03d}",f"客户{chr(65+i%8)}",products[i%8][0],qty,produced,delivered,(TODAY-timedelta(days=15+i)).isoformat(),(TODAY+timedelta(days=offset)).isoformat(),st))
    inv=[]
    types=["原材料","半成品","成品"]
    for i in range(20):
        safety=random.randint(50,100); maximum=random.randint(250,400)
        current=(safety-15 if i%5==0 else maximum+40 if i%7==0 else random.randint(safety,maximum))
        inv.append((f"MAT{i+1:03d}",f"物料-{i+1:02d}",types[i%3],current,safety,maximum,"件",f"{chr(65+i%3)}区-{i%6+1:02d}",now))
    return machines,records,plans,orders,inv

def write_template(machines, records, plans, orders, inv):
    TEMPLATE_PATH.parent.mkdir(parents=True,exist_ok=True)
    sheets={
      "设备信息":pd.DataFrame(machines,columns=["设备编号","设备名称","车间编号","当前状态","当前生产产品","更新时间"]),
      "生产记录":pd.DataFrame(records[:24],columns=["记录日期","设备编号","产品编号","计划数量","实际数量","合格品数量","报废品数量","开始时间","结束时间"]),
      "生产计划":pd.DataFrame(plans,columns=["计划编号","计划日期","设备编号","产品编号","计划数量","已完成数量","计划状态"]),
      "订单信息":pd.DataFrame(orders,columns=["订单编号","客户名称","产品编号","订单数量","已生产数量","已交付数量","下单日期","计划交付日期","订单状态"]),
      "库存信息":pd.DataFrame(inv,columns=["物料编号","物料名称","物料类型","当前库存","安全库存","最大库存","计量单位","仓库位置","更新时间"])}
    with pd.ExcelWriter(TEMPLATE_PATH,engine="openpyxl") as writer:
        for name,df in sheets.items(): df.to_excel(writer,sheet_name=name,index=False)

def generate():
    init_database(); machines,records,plans,orders,inv=make_data()
    with transaction() as c:
        for table in ["machine_realtime","production_records","production_plans","orders","inventory","machines","products","workshops"]: c.execute(f"DELETE FROM {table}")
        c.executemany("INSERT INTO workshops(workshop_code,workshop_name) VALUES(?,?)",workshops)
        c.executemany("INSERT INTO products(product_code,product_name,product_category,unit) VALUES(?,?,?,?)",products)
        c.executemany("INSERT INTO machines(machine_code,machine_name,workshop_code,status,current_product,updated_at) VALUES(?,?,?,?,?,?)",machines)
        c.executemany("INSERT INTO production_records(record_date,machine_code,product_code,planned_quantity,actual_quantity,qualified_quantity,defective_quantity,start_time,end_time) VALUES(?,?,?,?,?,?,?,?,?)",records)
        c.executemany("INSERT INTO production_plans(plan_code,plan_date,machine_code,product_code,planned_quantity,completed_quantity,status) VALUES(?,?,?,?,?,?,?)",plans)
        c.executemany("INSERT INTO orders(order_code,customer_name,product_code,order_quantity,produced_quantity,delivered_quantity,order_date,delivery_date,status) VALUES(?,?,?,?,?,?,?,?,?)",orders)
        c.executemany("INSERT INTO inventory(material_code,material_name,material_type,current_stock,safety_stock,maximum_stock,unit,warehouse_location,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",inv)
    write_template(machines,records,plans,orders,inv)
    print("模拟数据和 Excel 模板生成完成。")

if __name__ == "__main__": generate()
