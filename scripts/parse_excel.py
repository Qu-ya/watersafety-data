import pandas as pd, json
from pathlib import Path

HERE     = Path(__file__).resolve().parent.parent
IN_XLSX  = HERE / "quiz" / "114年度救生員資格檢定學科測驗題庫.xlsx"
OUT_JSON = HERE / "quiz" / "quiz_114_parsed.json"

# 1. 讀所有分頁、合併，同時加上 chapter 欄
xls = pd.ExcelFile(IN_XLSX)
frames = []
for sheet in xls.sheet_names:
    df_sheet = pd.read_excel(xls, sheet_name=sheet)
    df_sheet.columns = [str(c).strip().replace("\n","") for c in df_sheet.columns]
    # 把工作表名稱當成章節
    df_sheet["chapter"] = sheet
    frames.append(df_sheet)
df = pd.concat(frames, ignore_index=True)

# 2. 找出題目欄、過濾空值、只取前 701 筆
question_col = next(c for c in df.columns if "題" in c)
df = df[df[question_col].notna()].iloc[:701].reset_index(drop=True)

# 3. 輸出 JSON，每筆都有 chapter + 題目
records = []
for idx, row in df.iterrows():
    records.append({
        "num": idx + 1,
        "chapter": row["chapter"],
        "question": row[question_col],
        # 如果你還要保留答案欄，也可以加進來 row["答案"]
    })

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 最終筆數：{len(records)}，輸出到 {OUT_JSON.name}")
