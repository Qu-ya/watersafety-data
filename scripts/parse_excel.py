# scripts/parse_excel.py
import pandas as pd, json
from pathlib import Path

HERE     = Path(__file__).resolve().parent.parent
IN_XLSX  = HERE / "quiz" / "114年度救生員資格檢定學科測驗題庫.xlsx"
OUT_JSON = HERE / "quiz" / "quiz_114_parsed.json"

# 1. 讀所有工作表並合併
xls = pd.ExcelFile(IN_XLSX)
frames = []
for sheet in xls.sheet_names:
    df_sheet = pd.read_excel(xls, sheet_name=sheet)
    frames.append(df_sheet)
df = pd.concat(frames, ignore_index=True)

# 2. **去除「題目」欄位是空的列**（過濾掉標題或空白行）
df = df[df["題目"].notna()]

# 3. **強制只取前 701 筆** (Excel 如果有多，直接切掉)
df = df.iloc[:701].reset_index(drop=True)

# 4. 輸出 JSON
records = df.to_dict(orient="records")
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ Excel 經過過濾＆切片後，總共 {len(records)} 筆，輸出到 {OUT_JSON.name}")
