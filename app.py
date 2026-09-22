from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file, session, redirect, url_for
from uuid import uuid4
from config import MAX_CONTENT_LENGTH, TEMPLATE_PATH, UPLOAD_FOLDER, SECRET_KEY
from database import init_database
from services import dashboard_service as ds
from services.import_service import preview, import_excel, ImportValidationError
from services.plc_collector import collector, load_settings
from services.security_service import authenticate,login_user,change_password,require_roles,audit,list_users,save_user
from services import admin_service as ads

app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"]=MAX_CONTENT_LENGTH
app.config["SECRET_KEY"]=SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax")
init_database()
collector.start()

def ok(data=None,message="查询成功"): return jsonify(success=True,message=message,data=data or {})
def fail(message,status=400): return jsonify(success=False,message=message,data={}),status

@app.before_request
def protect_routes():
    if request.endpoint in ("login","static") or request.path.startswith("/static/"): return
    if not session.get("user_id"):
        if request.path.startswith("/api/"): return fail("请先登录",401)
        return redirect(url_for("login",next=request.path))
    if session.get("must_change_password") and request.endpoint not in ("password_page","password_change","logout"):
        return redirect(url_for("password_page"))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="GET": return render_template("login.html",title="用户登录")
    user=authenticate(request.form.get("username",""),request.form.get("password",""))
    if not user: return render_template("login.html",title="用户登录",error="用户名或密码错误。"),401
    login_user(user); audit("登录","用户",user["username"])
    return redirect(request.args.get("next") or url_for("dashboard"))

@app.get("/logout")
def logout():
    audit("退出登录","用户",session.get("username")); session.clear(); return redirect(url_for("login"))

@app.get("/password")
def password_page(): return render_template("password.html",title="修改密码",active="")
@app.post("/api/password")
def password_change():
    try:
        change_password(session["user_id"],request.form.get("current_password",""),request.form.get("new_password",""))
        session["must_change_password"]=False; audit("修改密码","用户",session["username"]); return ok(message="密码修改成功。")
    except ValueError as e:return fail(str(e))

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
@require_roles("admin","operator")
def import_page(): return render_template("import_data.html",active="import",title="数据导入")
@app.get("/master-data")
@require_roles("admin","operator")
def master_page(): return render_template("master_data.html",active="master",title="主数据维护")
@app.get("/reports")
def reports_page(): return render_template("reports.html",active="reports",title="报表导出")
@app.get("/admin")
@require_roles("admin")
def admin_page(): return render_template("admin.html",active="admin",title="用户与操作日志")
@app.get("/security")
@require_roles("admin")
def security_page(): return render_template("security.html",active="security",title="备份与安全审计")

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
@require_roles("admin","operator")
def api_import():
    file=request.files.get("file"); action=request.form.get("action","preview")
    if not file or not file.filename: return fail("请选择要上传的 Excel 文件。")
    if Path(file.filename).suffix.lower()!=".xlsx": return fail("仅支持 .xlsx 格式文件。")
    # 中文文件名经过安全化后可能只剩“xlsx”，因此使用随机名称并保留扩展名。
    UPLOAD_FOLDER.mkdir(parents=True,exist_ok=True); path=UPLOAD_FOLDER/f"{uuid4().hex}.xlsx"
    file.save(path)
    try:
        result=preview(path) if action=="preview" else import_excel(path)
        if action!="preview": audit("导入数据","Excel",file.filename,str(result))
        return ok(result,"数据校验通过。" if action=="preview" else "数据导入成功。")
    except ImportValidationError as e: audit("导入数据","Excel",file.filename,str(e),"失败"); return fail(str(e))
    except Exception: audit("导入数据","Excel",file.filename,"系统异常","失败"); return fail("导入失败，数据未写入。请检查内容格式和编号是否有效。")
    finally:
        path.unlink(missing_ok=True)

@app.get("/api/master-data")
@require_roles("admin","operator")
def api_master(): return ok(ads.master_data())
@app.post("/api/master-data/<table>")
@require_roles("admin","operator")
def api_master_save(table):
    try:
        key=ads.save_master(table,request.get_json() or {}); audit("保存主数据",table,key); return ok(message="保存成功。")
    except Exception as e:return fail(str(e))

@app.get("/api/users")
@require_roles("admin")
def api_users(): return ok(list_users())
@app.post("/api/users")
@require_roles("admin")
def api_users_save():
    try: save_user(request.get_json() or {}); audit("新增用户","用户",request.json.get("username")); return ok(message="用户创建成功。")
    except Exception as e:return fail(str(e))
@app.get("/api/audit-logs")
@require_roles("admin")
def api_logs(): return ok(ads.logs())

@app.get("/export/<report>")
def export_report(report):
    try:
        path=ads.export_report(report); audit("导出报表",report,path.name); return send_file(path,as_attachment=True,download_name=path.name)
    except ValueError as e:return fail(str(e))

@app.post("/api/backup")
@require_roles("admin")
def api_backup():
    path=ads.create_backup(); audit("创建备份","数据库",path.name); return send_file(path,as_attachment=True,download_name=path.name)
@app.get("/api/security-checks")
@require_roles("admin")
def api_security_checks(): return ok(ads.security_checks())

@app.errorhandler(404)
def not_found(_): return fail("请求的页面或接口不存在。",404)
@app.errorhandler(413)
def too_large(_): return fail("文件过大，最大允许 10MB。",413)
@app.errorhandler(500)
def server_error(_): return fail("服务器处理请求时出现错误。",500)

if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=False)
