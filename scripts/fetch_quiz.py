"""
自動下載「救生員資格檢定學科題庫 PDF」→ 轉 JSON
每年 PDF 位於體育署 iSport，網址規則固定，只需帶入民國年份
"""
import requests, pdfplumber, pandas as pd, re, io, datetime, pathlib, json

# --------------------------------------------------
YEAR = datetime.date.today().year - 1911           # 2025→114
OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)

PDF_URL = ( "https://isports.sa.gov.tw/apps/FDownload.aspx"
            "?SYS=LGM&MENU_CD=M10&ITEM_CD=T07&MENU_PRG_CD=3&ITEM_PRG_CD=3"
            f"&FILE_YEAR={YEAR}" )

pdf_bytes = requests.get(PDF_URL, timeout=30).content
pdf_file  = OUTDIR / f"quiz_{YEAR}.pdf"
pdf_file.write_bytes(pdf_bytes)

# --------------------------------------------------
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text()
        # 樣式： 1.水母漂可以使... (A)
        for m in re.finditer(r"(\d+)\.([^\n]+?)\(([ABCDOX])\)", txt):
            no, question, marker = m.groups()
            typ  = "TF" if marker in "OX" else "MC"
            ans  = marker
            rows.append({
                "id": f"Q{int(no):04}",
                "chapter": f"CH{int(no)//100+1:02}",
                "type": typ,
                "q": question.strip(),
                "choices": "" if typ=="TF" else "A|B|C|D",
                "ans": ans,
                "explain": ""         # 可之後補解析
            })

df = pd.DataFrame(rows)
json_file = OUTDIR / f"quiz_lifeguard_{YEAR}.json"
df.to_json(json_file, orient="records", indent=2, force_ascii=False)
print(f"Saved {json_file} with {len(df)} questions")
