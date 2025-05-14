# scripts/parse_excel.py
import pandas as pd
import json
from pathlib import Path
import sys

# ═══════════ 1. 定義路徑 ═══════════
HERE     = Path(__file__).resolve().parent.parent
QUIZ_DIR = HERE / "quiz"
xlsx_list = list(QUIZ_DIR.glob("*.xlsx"))
if not xlsx_list:
    raise FileNotFoundError(f"找不到 .xlsx 檔於 {QUIZ_DIR}")
IN_XLSX  = xlsx_list[0]
OUT_JSON = QUIZ_DIR / "quiz_114_parsed.json"

print(f"🔎 使用 Excel：{IN_XLSX.name}", file=sys.stdout)

# ═══════════ 2. 讀取所有分頁（用第二列作為欄位標題）╔═
frames = []
for sheet in pd.ExcelFile(IN_XLSX).sheet_names:
    # header=1 表示跳過第一列，第二列才當成欄位名稱
    df = pd.read_excel(IN_XLSX, sheet_name=sheet, header=1)
    # 清理欄位字串
    df.columns = [str(c).strip().replace("\n", "") for c in df.columns]
    df["chapter"] = sheet
    frames.append(df)
df = pd.concat(frames, ignore_index=True)

print(f"🔍 所有欄位名稱: {list(df.columns)}", file=sys.stdout)

# ═══════════ 3. 明確指定三個欄位 ═══════════
id_col       = "題項"
question_col = "題目"
answer_col   = "答案"

for col in (id_col, question_col, answer_col):
    if col not in df.columns:
        raise RuntimeError(f"找不到「{col}」欄位，請確認 Excel 的標題列")

print(f"⚠️ 使用欄位 -> id: '{id_col}', question: '{question_col}', answer: '{answer_col}'", file=sys.stdout)

# 只要前 701 筆，且題目欄不為空
df = df[df[question_col].notna()].iloc[:701].reset_index(drop=True)

# ═══════════ 4. 組成 records 並輸出 JSON ═══════════
records = []
for idx, row in df.iterrows():
    records.append({
        "num":       idx + 1,
        "chapter":   row["chapter"],
        "id":        str(row[id_col]).strip(),
        "question":  str(row[question_col]).strip(),
        "answer":    str(row[answer_col]).strip(),
    })

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 最終筆數：{len(records)}，輸出到 {OUT_JSON.name}", file=sys.stdout)
