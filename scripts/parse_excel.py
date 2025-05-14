import pandas as pd
import json
from pathlib import Path
import sys

# 1. 定義路徑與檔名
HERE = Path(__file__).resolve().parent.parent
QUIZ_DIR = HERE / "quiz"
xlsx_list = list(QUIZ_DIR.glob("*.xlsx"))
if not xlsx_list:
    raise FileNotFoundError(f"找不到 .xlsx 檔於 {QUIZ_DIR}")
IN_XLSX = xlsx_list[0]
OUT_JSON = QUIZ_DIR / "quiz_114_parsed.json"
print(f"🔎 使用 Excel：{IN_XLSX.name}", file=sys.stdout)

# 2. 讀取所有工作表並合併
xls = pd.ExcelFile(IN_XLSX)
frames = []
for sheet in xls.sheet_names:
    df_sheet = pd.read_excel(xls, sheet_name=sheet)
    # 清理欄名
    df_sheet.columns = [str(c).strip().replace("\n", "") for c in df_sheet.columns]
    # 設定章節欄
    df_sheet["chapter"] = sheet
    frames.append(df_sheet)

df = pd.concat(frames, ignore_index=True)

# 3. 自動找欄位：答案、題號與題目
cols = df.columns.tolist()
print(f"🔍 所有欄位名稱: {cols}")
try:
    answer_col = next(c for c in cols if "答" in c)
    question_col = next(c for c in cols if "題項" in c or ("題" in c and "題目" not in c))
    id_col = next(c for c in cols if c not in ["chapter", answer_col, question_col])
except StopIteration:
    raise RuntimeError(f"無法自動找到題目/答案欄，請查看欄位: {cols}")
print(f"⚠️ 使用欄位 -> id: '{id_col}', question: '{question_col}', answer: '{answer_col}'")

# 4. 過濾非空題目並取前 701 筆
df = df[df[question_col].notna()].iloc[:701].reset_index(drop=True)

# 5. 輸出 JSON
records = []
for row in df.itertuples(index=False):
    rec = {
        "chapter": str(getattr(row, 'chapter')).strip(),
        "id": str(getattr(row, id_col)).strip(),
        "question": str(getattr(row, question_col)).strip(),
        "answer": str(getattr(row, answer_col)).strip(),
    }
    records.append(rec)

with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 最終筆數：{len(records)}，輸出到 {OUT_JSON.name}")
