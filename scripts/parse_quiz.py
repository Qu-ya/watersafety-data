# scripts/parse_quiz.py
import json, pathlib, pdfplumber

HERE     = pathlib.Path(__file__).resolve().parent.parent
IN_PDF   = HERE / "quiz" / "114年度救生員資格檢定學科測驗題庫.pdf"
OUT_JSON = HERE / "quiz" / "quiz_114_parsed.json"

# 1. 合併所有頁文字，去掉換行
full = ""
with pdfplumber.open(IN_PDF) as pdf:
    for p in pdf.pages:
        full += (p.extract_text() or "").replace("\n", "")

# 2. 以「。」切分，每句當一題
parts = [s.strip() for s in full.split("。") if s.strip()]

# 3. 製作清單
data = []
for idx, txt in enumerate(parts, 1):
    data.append({"num": idx, "question": txt + "。"})

# 4. 輸出 JSON
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Parsed {len(data)} 題到 {OUT_JSON.name}")
