# scripts/parse_excel.py

import pandas as pd
import json
from pathlib import Path
import sys

# ─── 1. 定義路徑 ─────────────────────────────────────────
HERE    = Path(__file__).resolve().parent.parent
QUIZ_DIR= HERE / "quiz"

# 自動尋找 quiz/ 底下的 .xlsx 檔
xlsx_list = list(QUIZ_DIR.glob("*.xlsx"))
if not xlsx_list:
    raise FileNotFoundError(f"找不到 .xlsx 檔於 {QUIZ_DIR}")
IN_XLSX = xlsx_list[0]
OUT_JSON= QUIZ_DIR / "quiz_114_parsed.json"

print(f"🔎 使用 Excel：{IN_XLSX.name}", file=sys.stdout)

# ─── 2. 讀所有分頁、合併並帶上章節欄 ────────────────────
xls    = pd.ExcelFile(IN_XLSX)
frames = []

for sheet in xls.sheet_names:
    # 跳過前 3 行（標題、章節名稱），表頭就是「答案, 題項, 題目」
    df_sheet = pd.read_excel(
        xls,
        sheet_name=sheet,
        header=3,                # 第4列作為欄名
        usecols="A:C",           # 只讀 A、B、C 這三欄
        names=["answer","num","question"]  # 給三欄好記的名字
    )
    df_sheet["chapter"] = sheet
    frames.append(df_sheet)

df = pd.concat(frames, ignore_index=True)

# ─── 3. 列出所有欄位，抓題目欄並過濾 ────────────────────
question_col = "question"

# 3. 過濾空值 & 只取前 701 筆
df = df[df["question"].notna()].iloc[:701].reset_index(drop=True)
print(f"🔢 過濾＆取前701筆，剩 {len(df)} 筆", file=sys.stdout)

# 4. 輸出 JSON：每筆都有欄位 answer/num/chapter/question
records = []
for idx, row in df.iterrows():
    records.append({
        "num":      idx + 1,
        "chapter":  row["chapter"],
        "question": str(row["question"]).strip(),
        "answer":   str(row["answer"]).strip()
    })

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 輸出 {len(records)} 筆到 {OUT_JSON.name}", file=sys.stdout)
