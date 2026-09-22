from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "production.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
TEMPLATE_PATH = BASE_DIR / "data" / "生产运营数据模板.xlsx"
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

