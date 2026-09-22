from datetime import datetime
from functools import wraps
from flask import jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from database import connect, transaction

ROLE_NAMES={"admin":"管理员","operator":"操作员","viewer":"只读用户"}

def authenticate(username,password):
    conn=connect()
    try: row=conn.execute("SELECT * FROM users WHERE username=? AND enabled=1",(username,)).fetchone()
    finally: conn.close()
    return dict(row) if row and check_password_hash(row["password_hash"],password) else None

def login_user(user):
    session.clear(); session["user_id"]=user["id"]; session["username"]=user["username"]
    session["display_name"]=user["display_name"]; session["role"]=user["role"]
    session["must_change_password"]=bool(user["must_change_password"])
    with transaction() as c: c.execute("UPDATE users SET last_login_at=? WHERE id=?",(now(),user["id"]))

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def audit(action,target_type,target_id="",detail="",result="成功"):
    with transaction() as c:
        c.execute("INSERT INTO operation_logs(user_id,username,action,target_type,target_id,detail,result,ip_address,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
          (session.get("user_id"),session.get("username","匿名"),action,target_type,str(target_id),str(detail)[:500],result,request.remote_addr or "",now()))

def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            if not session.get("user_id"):
                if request.path.startswith("/api/"): return jsonify(success=False,message="请先登录",data={}),401
                return redirect(url_for("login",next=request.path))
            if roles and session.get("role") not in roles:
                if request.path.startswith("/api/"): return jsonify(success=False,message="没有操作权限",data={}),403
                return redirect(url_for("dashboard"))
            return fn(*args,**kwargs)
        return wrapped
    return decorator

def change_password(user_id,current,new_password):
    if len(new_password)<10 or not any(x.isdigit() for x in new_password) or not any(x.isalpha() for x in new_password):
        raise ValueError("新密码至少10位，并同时包含字母和数字。")
    with transaction() as c:
        row=c.execute("SELECT password_hash FROM users WHERE id=?",(user_id,)).fetchone()
        if not row or not check_password_hash(row[0],current): raise ValueError("当前密码不正确。")
        c.execute("UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?",(generate_password_hash(new_password),user_id))

def list_users():
    c=connect()
    try: return [dict(x) for x in c.execute("SELECT id,username,display_name,role,enabled,must_change_password,created_at,last_login_at FROM users ORDER BY id")]
    finally: c.close()

def save_user(data):
    username=str(data.get("username","")).strip(); display=str(data.get("display_name","")).strip()
    role=data.get("role"); password=data.get("password","")
    if not username or not display or role not in ROLE_NAMES: raise ValueError("用户资料不完整。")
    if len(password)<10: raise ValueError("初始密码至少10位。")
    with transaction() as c:
        c.execute("INSERT INTO users(username,password_hash,display_name,role,enabled,must_change_password,created_at) VALUES(?,?,?,?,1,1,?)",
                  (username,generate_password_hash(password),display,role,now()))
