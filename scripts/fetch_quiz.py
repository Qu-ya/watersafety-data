"""
下載救生員題庫 PDF → 轉成 JSON
每年只要改最上面的 PDF_URL 即可
"""

import requests, pathlib, io, datetime, pdfplumber, pandas as pd, re

# 1. 直接指定 114 年度 PDF（明年換 115 只改這一行）
PDF_URL = "https://isports.sa.gov.tw/LGM/09/04/1120214/009f3c95-7d06-43d9-a6d8-513a779be3e4.pdf"

OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)

# 2. 下載 PDF 並存檔
pdf_bytes = requests.get(PDF_URL, timeout=30).content
year_tag  = datetime.date.today().year - 1911          # 2025→114
(OUTDIR / f"quiz_{year_tag}.pdf").write_bytes(pdf_bytes)

print("PDF URL =", PDF_URL)

# 3. 解析 PDF → rows
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text() or ""
        for n, q, ans in re.findall(r"(\d+)\.([^\n]+?)\(([ABCDOX])\)", txt):
            typ = "TF" if ans in "OX" else "MC"
            rows.append({
                "id": f"Q{int(n):04}",
                "chapter": f"CH{int(n)//100+1:02}",
                "type": typ,
                "q": q.strip(),
                "choices": "" if typ == "TF" else "A|B|C|D",
                "ans": ans,
                "explain": ""
            })

# 4. 輸出 JSON
json_path = OUTDIR / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(json_path, orient="records",
                           indent=2, force_ascii=False)
print("Saved", json_path, "with", len(rows), "questions")
