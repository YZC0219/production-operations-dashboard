import pandas as pd
import pytest
from services.import_service import read_and_validate, ImportValidationError, SHEETS

def write_book(path,sheets):
    with pd.ExcelWriter(path,engine="openpyxl") as w:
        for name,cols in sheets.items(): pd.DataFrame(columns=cols).to_excel(w,sheet_name=name,index=False)

def test_missing_sheet(tmp_path):
    path=tmp_path/"bad.xlsx"; subset=dict(list(SHEETS.items())[:-1]); write_book(path,subset)
    with pytest.raises(ImportValidationError,match="缺少必要工作表"): read_and_validate(path)

def test_missing_column(tmp_path):
    path=tmp_path/"bad.xlsx"; broken={k:list(v) for k,v in SHEETS.items()}; broken["设备信息"].remove("设备名称"); write_book(path,broken)
    with pytest.raises(ImportValidationError,match="缺少字段"): read_and_validate(path)

