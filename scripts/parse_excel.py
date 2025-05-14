import pandas as pd, json
from pathlib import Path

HERE     = Path(__file__).resolve().parent.parent
IN_XLSX  = HERE / "quiz" / "114年度救生員資格檢定學科測驗題庫.xlsx"
OUT_JSON = HERE / "quiz" / "quiz_114_parsed.json"

# 1. 讀所有分頁、合併，並加上 sheet_name 當 chapter
xls = pd.ExcelFile(IN_XLSX)
frames = []
for sheet in xls.sheet_names:
    df_sheet = pd.read_excel(xls, sheet_name=sheet)
    # 清理欄名
    df_sheet.columns = [str(c).strip().replace("\n","") for c in df_sheet.columns]
    df_sheet["chapter"] = sheet
    frames.append(df_sheet)
df = pd.concat(frames, ignore_index=True)

import sys

# 2. 列出所有欄位讓你看（會出現在 Actions log）
print("🔍 所有欄位名稱:", list(df.columns), file=sys.stdout)

# 嘗試找第一個含「題」字的欄位
try:
    question_col = next(c for c in df.columns if "題" in c)
except StopIteration:
    # 如果找不到，就 fallback 用最後一個欄
    question_col = df.columns[-1]
    print(f"⚠️ 找不到含「題」字欄位，改用最後一個欄: '{question_col}'", file=sys.stdout)

# 3. 過濾空值、只要前 701 筆
df = df[df[question_col].notna()].iloc[:701].reset_index(drop=True)

# 3. 輸出 JSON：每筆都有 num/chapter/question
records = []
for idx, row in df.iterrows():
    records.append({
        "num": idx + 1,
        "chapter": row["chapter"],
        "question": row[question_col]
    })

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 最終筆數：{len(records)}，輸出到 {OUT_JSON.name}")
