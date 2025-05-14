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

# ═══════════ 2. 讀取所有分頁（第4列作為欄位標題） ═══════════
xlsx = pd.ExcelFile(IN_XLSX)
frames = []
for sheet in xlsx.sheet_names:
    df = pd.read_excel(
        IN_XLSX,
        sheet_name=sheet,
        header=3,        # 從第4列當欄位名稱 (0-based: 3)
        usecols="A:C", # 抓 A=答案, B=題項, C=題目 三欄
        dtype=str        # 全部讀成 str，避免數字轉 int
    )
    # 確保欄名正確
    df.columns = ["答案", "題項", "題目"]
    # 加上章節資訊
    df["chapter"] = sheet
    frames.append(df)

# 合併所有分頁
df = pd.concat(frames, ignore_index=True)
print(f"🔍 所有欄位名稱: {list(df.columns)}", file=sys.stdout)

# ═══════════ 3. 檢查欄位並取前701筆 ═══════════
required = ["題項", "題目", "答案"]
for col in required:
    if col not in df.columns:
        raise RuntimeError(f"找不到「{col}」欄位，請確認 Excel 的第4列是否正確")
print(f"⚠️ 使用欄位 -> id: '題項', question: '題目', answer: '答案'", file=sys.stdout)

# 過濾空題目並取前701筆
df = df[df["題目"].notna()].iloc[:701].reset_index(drop=True)

# ═══════════ 4. 組成 records 並輸出 JSON ═══════════
records = []
for idx, row in df.iterrows():
    records.append({
        "num":      idx + 1,
        "chapter":  row["chapter"],
        "id":       row["題項"].strip(),
        "question": row["題目"].strip(),
        "answer":   row["答案"].strip(),
    })

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print(f"✅ 最終筆數：{len(records)}，輸出到 {OUT_JSON.name}", file=sys.stdout)
