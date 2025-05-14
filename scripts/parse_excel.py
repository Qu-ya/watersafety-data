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
    df_sheet = pd.read_excel(xls, sheet_name=sheet)
    # 清理欄名
    df_sheet.columns = [str(c).strip().replace("\n","") for c in df_sheet.columns]
    df_sheet["chapter"] = sheet
    frames.append(df_sheet)

df = pd.concat(frames, ignore_index=True)

# ─── 3. 列出所有欄位，抓題目欄並過濾 ────────────────────
print("🔍 所有欄位名稱:", list(df.columns), file=sys.stdout)

try:
    question_col = next(c for c in df.columns if "題" in c)
    print(f"✅ 偵測到題目欄: '{question_col}'", file=sys.stdout)
except StopIteration:
    # 如果真的找不到，就用最後一個欄
    question_col = df.columns[-1]
    print(f"⚠️ 找不到含「題」的欄位，改用: '{question_col}'", file=sys.stdout)

# 過濾掉空的題目列，並只取前 701 筆
df = df[df[question_col].notna()].iloc[:701].reset_index(drop=True)
print(f"🔢 過濾＆取前701筆，剩 {len(df)} 筆", file=sys.stdout)

# ─── 4. 輸出 JSON ───────────────────────────────────────
records = []
for idx, row in df.iterrows():
    records.append({
        "num":      idx + 1,
        "chapter":  row["chapter"],
        "question": row[question_col].strip(),
        # "answer": row.get("答案","")   # 如果要帶答案請取消註解
    })

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 輸出 {len(records)} 筆到 {OUT_JSON.name}", file=sys.stdout)
