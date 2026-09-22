from datetime import date, timedelta
from services.calculations import quality_rate, defective_rate, inventory_status, order_warning

def test_quality_rate(): assert quality_rate(95,100)==95
def test_defective_rate(): assert defective_rate(5,100)==5
def test_zero_actual():
    assert quality_rate(0,0)==0
    assert defective_rate(0,0)==0
def test_low_inventory(): assert inventory_status(9,10,100)=="库存不足"
def test_high_inventory(): assert inventory_status(101,10,100)=="库存过高"
def test_overdue_order():
    warning,days=order_warning(date.today()-timedelta(days=1),"生产中")
    assert warning=="逾期" and days==-1

