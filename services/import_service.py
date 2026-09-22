from pathlib import Path
import pandas as pd
from database import transaction

SHEETS={
 "设备信息":["设备编号","设备名称","车间编号","当前状态","当前生产产品","更新时间"],
 "生产记录":["记录日期","设备编号","产品编号","计划数量","实际数量","合格品数量","报废品数量","开始时间","结束时间"],
 "生产计划":["计划编号","计划日期","设备编号","产品编号","计划数量","已完成数量","计划状态"],
 "订单信息":["订单编号","客户名称","产品编号","订单数量","已生产数量","已交付数量","下单日期","计划交付日期","订单状态"],
 "库存信息":["物料编号","物料名称","物料类型","当前库存","安全库存","最大库存","计量单位","仓库位置","更新时间"]}

class ImportValidationError(ValueError): pass

def _clean(v):
    if pd.isna(v): return ""
    if hasattr(v,"strftime"): return v.strftime("%Y-%m-%d %H:%M:%S")
    return str(v).strip()

def read_and_validate(path):
    if Path(path).suffix.lower() != ".xlsx": raise ImportValidationError("仅支持 .xlsx 格式文件。")
    try:
        with pd.ExcelFile(path,engine="openpyxl") as book:
            missing=[s for s in SHEETS if s not in book.sheet_names]
            if missing: raise ImportValidationError("缺少必要工作表："+"、".join(missing))
            result={}
            for sheet, required in SHEETS.items():
                df=pd.read_excel(book,sheet_name=sheet)
                absent=[c for c in required if c not in df.columns]
                if absent: raise ImportValidationError(f"工作表“{sheet}”缺少字段："+"、".join(absent))
                df=df[required].dropna(how="all")
                if df[required[0]].isna().any(): raise ImportValidationError(f"工作表“{sheet}”存在空的{required[0]}。")
                result[sheet]=df
    except ImportValidationError: raise
    except Exception as e: raise ImportValidationError("文件无法读取，请确认它是有效的 Excel 文件。") from e
    return result

def preview(path):
    data=read_and_validate(path)
    return {name:{"总行数":len(df),"预览":df.head(5).fillna("").astype(str).to_dict("records")} for name,df in data.items()}

def import_excel(path):
    data=read_and_validate(path)
    with transaction() as c:
        for _,r in data["设备信息"].iterrows():
            vals=tuple(_clean(r[x]) for x in SHEETS["设备信息"])
            c.execute("INSERT INTO machines(machine_code,machine_name,workshop_code,status,current_product,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(machine_code) DO UPDATE SET machine_name=excluded.machine_name,workshop_code=excluded.workshop_code,status=excluded.status,current_product=excluded.current_product,updated_at=excluded.updated_at",vals)
        mappings={
          "生产记录":("production_records",["record_date","machine_code","product_code","planned_quantity","actual_quantity","qualified_quantity","defective_quantity","start_time","end_time"],["record_date","machine_code","product_code"]),
          "生产计划":("production_plans",["plan_code","plan_date","machine_code","product_code","planned_quantity","completed_quantity","status"],["plan_code"]),
          "订单信息":("orders",["order_code","customer_name","product_code","order_quantity","produced_quantity","delivered_quantity","order_date","delivery_date","status"],["order_code"]),
          "库存信息":("inventory",["material_code","material_name","material_type","current_stock","safety_stock","maximum_stock","unit","warehouse_location","updated_at"],["material_code"])}
        for sheet,(table,cols,keys) in mappings.items():
            for _,r in data[sheet].iterrows():
                vals=tuple(_clean(r[x]) for x in SHEETS[sheet])
                assigns=",".join(f"{x}=excluded.{x}" for x in cols if x not in keys)
                c.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?'*len(cols))}) ON CONFLICT({','.join(keys)}) DO UPDATE SET {assigns}",vals)
    return {name:len(df) for name,df in data.items()}
