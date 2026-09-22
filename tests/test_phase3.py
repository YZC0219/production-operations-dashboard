import json
from services import device_config_service as dcs
from services.alarm_service import evaluate,list_alarms
from database import transaction

def test_device_config_validation_and_save(tmp_path,monkeypatch):
    path=tmp_path/"plc.json"; path.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(dcs,"SETTINGS_PATH",path)
    result=dcs.save_config({"poll_interval_seconds":3,"devices":[{"machine_code":"M001","ip":"192.168.1.10","driver":"simulation"}]})
    assert result["poll_interval_seconds"]==3
    saved=json.loads(path.read_text(encoding='utf-8'))
    assert saved["devices"][0]["db_number"]==1

def test_alarm_lifecycle():
    with transaction() as c:c.execute("DELETE FROM alarms WHERE machine_code='TEST-PLC'")
    evaluate("TEST-PLC","故障","离线",9)
    active=[x for x in list_alarms() if x["machine_code"]=="TEST-PLC"]
    assert len(active)==2 and all(x["status"]=="活动" for x in active)
    evaluate("TEST-PLC","运行","在线",0)
    recovered=[x for x in list_alarms() if x["machine_code"]=="TEST-PLC"]
    assert all(x["status"]=="已恢复" for x in recovered)
    with transaction() as c:c.execute("DELETE FROM alarms WHERE machine_code='TEST-PLC'")
