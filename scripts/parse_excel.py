# scripts/parse_excel.py
import pandas as pd, json
from pathlib import Path

HERE     = Path(__file__).resolve().parent.parent
IN_XLSX  = HERE / "quiz" / "114年度救生員資格檢定學科測驗題庫.xlsx"
OUT_JSON = HERE / "quiz" / "quiz_114_parsed.json"

# 1) 讀所有工作表並合併
xls = pd.ExcelFile(IN_XLSX)
frames = [pd.read_excel(xls, sheet_name=sn) for sn in xls.sheet_names]
df = pd.concat(frames, ignore_index=True)

# 2) 清理欄名：去掉前後空白和換行
df.columns = [str(col).strip().replace("\n", "") for col in df.columns]

# 3) 自動找出「題」欄（第一個含『題』字的欄名）
question_col = next((c for c in df.columns if "題" in c), df.columns[-1])
print(f"🔎 使用題目欄位：'{question_col}'")

# 4) 過濾掉空值，並只取前 701 筆
df = df[df[question_col].notna()].iloc[:701].reset_index(drop=True)

# 5) 輸出 JSON
records = df.to_dict(orient="records")
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 最終筆數：{len(records)}，輸出到 {OUT_JSON.name}")
