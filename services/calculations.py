from datetime import date, datetime

def percentage(part, total):
    return round(part / total * 100, 2) if total else 0

def quality_rate(qualified, actual): return percentage(qualified, actual)
def defective_rate(defective, actual): return percentage(defective, actual)
def completion_rate(completed, planned): return min(percentage(completed, planned), 100)

def inventory_status(current, safety, maximum):
    if current < safety: return "库存不足"
    if current > maximum: return "库存过高"
    return "正常"

def order_warning(delivery_date, status, today=None):
    today = today or date.today()
    target = datetime.strptime(str(delivery_date), "%Y-%m-%d").date()
    days = (target - today).days
    if status != "已完成" and days < 0: return "逾期", days
    if status != "已完成" and days <= 3: return "临近", days
    return "正常", days

