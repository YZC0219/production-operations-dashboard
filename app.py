from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file
from uuid import uuid4
from config import MAX_CONTENT_LENGTH, TEMPLATE_PATH, UPLOAD_FOLDER
from database import init_database
from services import dashboard_service as ds
from services.import_service import preview, import_excel, ImportValidationError
from services.plc_collector import collector, load_settings

app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"]=MAX_CONTENT_LENGTH
app.config["SECRET_KEY"]="production-dashboard-local-key"
init_database()
collector.start()

def ok(data=None,message="查询成功"): return jsonify(success=True,message=message,data=data or {})
def fail(message,status=400): return jsonify(success=False,message=message,data={}),status

@app.get("/")
def dashboard(): return render_template("dashboard.html",active="dashboard",title="生产总览")
@app.get("/machines")
def machines(): return render_template("machines.html",active="machines",title="设备状态")
@app.get("/plans")
def plans(): return render_template("plans.html",active="plans",title="生产计划")
@app.get("/orders")
def orders(): return render_template("orders.html",active="orders",title="订单管理")
@app.get("/inventory")
def inventory(): return render_template("inventory.html",active="inventory",title="库存管理")
@app.get("/import")
def import_page(): return render_template("import_data.html",active="import",title="数据导入")

@app.get("/api/dashboard/summary")
def api_summary(): return ok(ds.summary())
@app.get("/api/dashboard/production-trend")
def api_production(): return ok(ds.dashboard_data()["trend"])
@app.get("/api/dashboard/quality-trend")
def api_quality(): return ok(ds.dashboard_data()["trend"])
@app.get("/api/dashboard/all")
def api_dashboard(): return ok(ds.dashboard_data())
@app.get("/api/machines")
def api_machines(): return ok(ds.machine_list())
@app.get("/api/realtime/status")
def api_realtime_status():
    settings=load_settings()
    devices=[{k:v for k,v in device.items() if k != "mapping"} for device in settings.get("devices",[])]
    return ok({"poll_interval_seconds":settings.get("poll_interval_seconds",2),
               "devices":devices,"latest":ds.realtime_status()})
@app.get("/api/plans")
def api_plans(): return ok(ds.plan_list())
@app.get("/api/orders")
def api_orders(): return ok(ds.order_list())
@app.get("/api/inventory")
def api_inventory(): return ok(ds.inventory_list())
@app.get("/download-template")
def download_template(): return send_file(TEMPLATE_PATH,as_attachment=True,download_name="生产运营数据模板.xlsx")

@app.post("/api/import")
def api_import():
    file=request.files.get("file"); action=request.form.get("action","preview")
    if not file or not file.filename: return fail("请选择要上传的 Excel 文件。")
    if Path(file.filename).suffix.lower()!=".xlsx": return fail("仅支持 .xlsx 格式文件。")
    # 中文文件名经过安全化后可能只剩“xlsx”，因此使用随机名称并保留扩展名。
    UPLOAD_FOLDER.mkdir(parents=True,exist_ok=True); path=UPLOAD_FOLDER/f"{uuid4().hex}.xlsx"
    file.save(path)
    try:
        result=preview(path) if action=="preview" else import_excel(path)
        return ok(result,"数据校验通过。" if action=="preview" else "数据导入成功。")
    except ImportValidationError as e: return fail(str(e))
    except Exception: return fail("导入失败，数据未写入。请检查内容格式和编号是否有效。")
    finally:
        path.unlink(missing_ok=True)

@app.errorhandler(404)
def not_found(_): return fail("请求的页面或接口不存在。",404)
@app.errorhandler(413)
def too_large(_): return fail("文件过大，最大允许 10MB。",413)
@app.errorhandler(500)
def server_error(_): return fail("服务器处理请求时出现错误。",500)

if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=False)
