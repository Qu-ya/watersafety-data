# scripts/parse_quiz.py
import json, pathlib, pdfplumber

HERE     = pathlib.Path(__file__).resolve().parent.parent
IN_PDF   = HERE / "quiz" / "quiz_114.pdf"        # ← 確認跟你 repo 裡的檔名一樣
OUT_JSON = HERE / "quiz" / "quiz_114_parsed.json"

full = ""
with pdfplumber.open(IN_PDF) as pdf:
    for p in pdf.pages:
        full += (p.extract_text() or "").replace("\n", "")

parts = [s.strip() for s in full.split("。") if s.strip()]

data = [{"num": i+1, "question": txt + "。"} for i, txt in enumerate(parts)]

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Parsed {len(data)} 題到 {OUT_JSON.name}")
