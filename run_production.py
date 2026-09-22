"""使用 Waitress 启动生产模式，供局域网或 Windows 服务使用。"""
import os
from waitress import serve
from app import app

if __name__=="__main__":
    serve(app,host=os.environ.get("DASHBOARD_HOST","0.0.0.0"),
          port=int(os.environ.get("DASHBOARD_PORT","5000")),threads=8)
