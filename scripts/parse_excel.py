# scripts/parse_excel.py
import pandas as pd
import json
from pathlib import Path

# 1. Excel 路徑
HERE    = Path(__file__).resolve().parent.parent
IN_XLSX = HERE / "quiz" / "114年度救生員資格檢定學科測驗題庫.xlsx"
OUT_JSON= HERE / "quiz" / "quiz_114_parsed.json"

# 2. 讀 Excel（第一筆是標題）
df = pd.read_excel(IN_XLSX)

# 3. 檢查筆數
total = len(df)
print(f"▶️ Excel 總共 {total} 筆")

# 4. 轉成清爽的 JSON
records = df.to_dict(orient="records")
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 已輸出 {total} 筆到 {OUT_JSON.name}")
