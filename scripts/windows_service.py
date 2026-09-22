"""Windows 服务：管理员 PowerShell 中运行本脚本的 install/start/stop/remove。"""
import os,sys
from pathlib import Path
import win32event,win32service,win32serviceutil,servicemanager
from waitress.server import create_server

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
os.chdir(PROJECT)

class DashboardService(win32serviceutil.ServiceFramework):
    _svc_name_="ProductionOperationsDashboard"
    _svc_display_name_="生产运营与库存管理看板"
    _svc_description_="生产设备采集、报警、OEE和库存管理服务"
    def __init__(self,args):
        super().__init__(args);self.stop_event=win32event.CreateEvent(None,0,0,None);self.server=None
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.server:self.server.close()
        win32event.SetEvent(self.stop_event)
    def SvcDoRun(self):
        from app import app
        servicemanager.LogInfoMsg("生产运营看板服务启动")
        self.server=create_server(app,host=os.environ.get("DASHBOARD_HOST","0.0.0.0"),port=int(os.environ.get("DASHBOARD_PORT","5000")),threads=8)
        self.server.run()

if __name__=="__main__":win32serviceutil.HandleCommandLine(DashboardService)
