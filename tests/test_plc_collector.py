import struct
from services.plc_collector import decode_s7_data

def test_decode_s7_data():
    raw=bytearray(14)
    raw[0]=1
    struct.pack_into(">i",raw,2,123)
    struct.pack_into(">i",raw,6,120)
    struct.pack_into(">i",raw,10,3)
    data=decode_s7_data(raw,{"status_byte":0,"actual_quantity_dint":2,
        "qualified_quantity_dint":6,"defective_quantity_dint":10})
    assert data=={"status":"运行","actual_quantity":123,"qualified_quantity":120,
                  "defective_quantity":3,"fault_code":0}

def test_decode_fault_status():
    raw=bytearray(14); raw[0]=3
    data=decode_s7_data(raw,{"status_byte":0,"actual_quantity_dint":2,
        "qualified_quantity_dint":6,"defective_quantity_dint":10})
    assert data["status"]=="故障" and data["fault_code"]==1
