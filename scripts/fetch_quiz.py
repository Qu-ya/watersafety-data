"""
自動抓體育署題庫頁 → 解析真正 PDF → 轉 JSON
"""
import requests, re, pathlib, io, datetime, pdfplumber, pandas as pd

OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)

# 1. 抓列表頁（固定網址）
LIST_URL = "https://isports.sa.gov.tw/apps/Essay.aspx?SYS=LGM&MENU_PRG_CD=3&ITEM_PRG_CD=3&ITEM_CD=T07"
html = requests.get(LIST_URL, timeout=30).text

# 2. 用正則抽出第一個 PDF 相對路徑
pdf_pattern = re.compile(r"downLoadFileWithName\(\s*'([^']+?\.pdf)'", re.I)
m = pdf_pattern.search(html)

if not m:
    raise RuntimeError("找不到 PDF 連結，請檢查 HTML，前 500 字：\n" + html[:500])

relative_path = m.group(1)               # 例：LGM/09/04/1120214/xxxx.pdf
PDF_URL = f"https://isports.sa.gov.tw/{relative_path}"
print("PDF URL =", PDF_URL)

# 3. 下載 PDF
pdf_bytes = requests.get(PDF_URL, timeout=30).content
year_tag   = datetime.date.today().year - 1911          # 2025→114
(pdf_path := OUTDIR / f"quiz_{year_tag}.pdf").write_bytes(pdf_bytes)

# 4. 解析 PDF
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text()
        for n,q,ans in re.findall(r"(\d+)\.([^\n]+?)\(([ABCDOX])\)", txt):
            typ = "TF" if ans in "OX" else "MC"
            rows.append({
                "id": f"Q{int(n):04}",
                "chapter": f"CH{int(n)//100+1:02}",
                "type": typ,
                "q": q.strip(),
                "choices": "" if typ=="TF" else "A|B|C|D",
                "ans": ans,
                "explain": ""
            })

json_path = OUTDIR / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(json_path, orient="records",
                           indent=2, force_ascii=False)
print("Saved", json_path, "with", len(rows), "questions")
