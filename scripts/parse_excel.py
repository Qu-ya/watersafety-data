#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_excel.py

功能：
1. 自動掃描 quiz 資料夾內的 .xlsx 檔案。
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
HERE = Path(__file__).resolve().parent         # 本檔所在資料夾
QUIZ_DIR = HERE / "quiz"                      # quiz 子資料夾
xlsx_list = list(QUIZ_DIR.glob("*.xlsx"))     # 掃描所有 .xlsx
if not xlsx_list:
    print(f"❌ 找不到 Excel 檔於 {QUIZ_DIR}", file=sys.stderr)
    sys.exit(1)
IN_XLSX = xlsx_list[0]                          # 取第一個檔案
OUT_JSON = QUIZ_DIR / "quiz_114_parsed.json"
print(f"🔎 使用 Excel 檔案：{IN_XLSX.name}", file=sys.stdout)

# ═══════════ 2. 定義過濾函式 ═══════════
def is_valid_row(row) -> bool:
    """
    判斷 DataFrame 讀出的一列是否為有效題目：
    - id（題項）必須是純數字
    - question（題目）不能是標題文字或空白
    - answer（答案）不能是標題文字或空白
    回傳 True 才會保留此列。
    """
    id_val = str(row["題項"]).strip()
    q_val = str(row["題目"]).strip()
    a_val = str(row["答案"]).strip()
    if not id_val.isdigit():    # 篩除非純數字
        return False
    if q_val in ("", "題目"):  # 篩除標題與空白
        return False
    if a_val in ("", "答案"):
        return False
    return True

# ═══════════ 3. 讀取所有工作表並合併 ═══════════
print("📖 開始讀取所有工作表...", file=sys.stdout)
excel = pd.ExcelFile(IN_XLSX)
frames = []
for sheet in excel.sheet_names:
    # 從第4列(header=3)讀取 A~C 欄 (答案/題項/題目)
    df = pd.read_excel(
        IN_XLSX,
        sheet_name=sheet,
        header=3,
        usecols="A:C",
        dtype=str
    )
    df.columns = ["答案", "題項", "題目"]  # 統一欄位名稱
    df["chapter"] = sheet                    # 新增章節欄位
    frames.append(df)
print(f"✅ 共讀取 {len(frames)} 個工作表", file=sys.stdout)

# 合併所有 DataFrame
df_all = pd.concat(frames, ignore_index=True)
print(f"🔍 原始列數：{len(df_all)}", file=sys.stdout)

# ═══════════ 4. 過濾並生成 records ═══════════
print("🔎 開始過濾無效列...", file=sys.stdout)
valid_rows = df_all[df_all.apply(is_valid_row, axis=1)]
print(f"✅ 有效題目列數：{len(valid_rows)}", file=sys.stdout)

records = []
for idx, row in valid_rows.iterrows():
    records.append({
        "num":      idx + 1,                # num 連續編號
        "chapter":  row["chapter"],
        "id":       row["題項"].strip(),
        "question": row["題目"].strip(),
        "answer":   row["答案"].strip(),
    })

# ═══════════ 5. 輸出 JSON 檔案 ═══════════
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print(f"🏁 最終輸出題數：{len(records)} 到 {OUT_JSON.name}", file=sys.stdout)

# ========= 6. 腳本說明 =========
# 1. is_valid_row(): 過濾標題列與空白列，確保只有真實題目進 JSON。
# 2. header=3: 代表跳過前三列把第4列當欄位名稱，符合你的 Excel 排版。
# 3. usecols="A:C": 只讀【答案 (A)】【題項 (B)】【題目 (C)】3 欄。
# 4. dtype=str: 全部讀成字串，避免數字自動轉 int 導致 isdigit() 失效。
# 5. concat + apply(): 整合多個工作表並對每列應用 is_valid_row 篩選。
# 6. json.dump(indent=2): 美化 JSON，開發時方便閱讀。
