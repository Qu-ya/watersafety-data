#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_excel.py

功能：
1. 自動掃描專案根目錄下 quiz 資料夾內的 .xlsx 檔案。
2. 讀取所有工作表，使用第4列作為欄位標題 (header=3)。
3. 檢查並過濾掉「題項／題目／答案」標題列與空白列。
4. 整理為 JSON list，每筆題目包含 num、chapter、id、question、answer。
5. 輸出至 quiz/quiz_114_parsed.json，覆寫舊檔。
"""
import pandas as pd
import json
import sys
from pathlib import Path

# ═══════════ 1. 定義路徑 ═══════════
# 此腳本放在專案/scripts 內，故先往上兩層到專案根目錄
HERE = Path(__file__).resolve().parent.parent  # 根目錄
QUIZ_DIR = HERE / "quiz"                       # 根目錄下的 quiz 資料夾
xlsx_list = list(QUIZ_DIR.glob("*.xlsx"))      # 掃描 quiz 資料夾下的 .xlsx
if not xlsx_list:
    print(f"❌ 找不到 Excel 檔於 {QUIZ_DIR}", file=sys.stderr)
    sys.exit(1)
IN_XLSX = xlsx_list[0]
OUT_JSON = QUIZ_DIR / "quiz_114_parsed.json"
print(f"🔎 使用 Excel 檔案：{IN_XLSX.name}", file=sys.stdout)

# ═══════════ 2. 過濾函式 (過濾標題列與空白列) ═══════════
def is_valid_row(row) -> bool:
    id_val = str(row["題項"]).strip()
    q_val = str(row["題目"]).strip()
    a_val = str(row["答案"]).strip()
    # id 必須純數字，question 不可為標題文字或空，answer 不可為標題文字或空
    return id_val.isdigit() and q_val not in ("", "題目") and a_val not in ("", "答案")

# ═══════════ 3. 讀取所有工作表並合併 ═══════════
print("📖 開始讀取所有工作表...", file=sys.stdout)
excel = pd.ExcelFile(IN_XLSX)
frames = []
for sheet in excel.sheet_names:
    df = pd.read_excel(
        IN_XLSX,
        sheet_name=sheet,
        header=3,
        usecols="A:C",
        dtype=str
    )
    df.columns = ["答案", "題項", "題目"]
    df["chapter"] = sheet
    frames.append(df)
print(f"✅ 共讀取 {len(frames)} 個工作表", file=sys.stdout)

df_all = pd.concat(frames, ignore_index=True)
print(f"🔍 原始列數：{len(df_all)}", file=sys.stdout)

# ═══════════ 4. 過濾並生成 records ═══════════
print("🔎 開始過濾無效列...", file=sys.stdout)
valid_rows = df_all[df_all.apply(is_valid_row, axis=1)]
print(f"✅ 有效題目列數：{len(valid_rows)}", file=sys.stdout)

records = []
for idx, row in valid_rows.iterrows():
    records.append({
        "num":      idx + 1,
        "chapter":  row["chapter"],
        "id":       row["題項"].strip(),
        "question": row["題目"].strip(),
        "answer":   row["答案"].strip(),
    })

# ═══════════ 5. 輸出 JSON 檔案 ═══════════
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print(f"🏁 最終輸出題數：{len(records)} 到 {OUT_JSON.name}", file=sys.stdout)

# ========= 6. 注意 =========
# - Path(__file__).parent.parent 確保 QUIZ_DIR 指向專案根目錄下的 quiz
# - 如有放置 .xlsx 在其他子資料夾，請修改 QUIZ_DIR 路徑
