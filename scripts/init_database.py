import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import init_database

if __name__ == "__main__":
    init_database()
    print("数据库初始化完成。")
