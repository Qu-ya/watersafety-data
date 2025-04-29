"""
下載救生員題庫 PDF → 轉成 JSON
每年只改最上方 PDF_URL
"""
import requests, pathlib, io, datetime, pdfplumber, pandas as pd, re

# 1. 直接指定 114 年度 PDF（明年換這行）
python<br>PDF_URL = (<br> "https://isports.sa.gov.tw/apps/FDownload.aspx"<br> "?SYS=LGM&MENU_CD=M10&ITEM_CD=T07&MENU_PRG_CD=3&ITEM_PRG_CD=3"<br> "&FILE_PATH=LGM%2F09%2F04%2F1120214%2F009f3c95-7d06-43d9-a6d8-513a779be3e4.pdf"<br> 
"&FILE_NAME=114%E5%B9%B4%E5%BA%A6%E6%95%91%E7%94%9F%E5%93%A1%E8%B3%87%E6%A0%BC%E6%AA%A2%E5%AE%9A%E5%AD%B8%E7%A7%91%E6%B8%AC%E9%A9%97%E9%A1%8C%E5%BA%AB.pdf"<br>)<br>

# 2. 下載 PDF（帶 Header＋驗證）
HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer":
        "https://isports.sa.gov.tw/apps/Essay.aspx?SYS=LGM&ITEM_CD=T07"
}
resp = requests.get(PDF_URL, headers=HEADERS, timeout=30)
if resp.status_code != 200 or "application/pdf" not in resp.headers.get("content-type", ""):
    raise RuntimeError(f"下載失敗：HTTP {resp.status_code} - {resp.headers.get('content-type')}")
if not resp.content.startswith(b"%PDF"):
    raise RuntimeError("收到的不是 PDF！前 100 位元組：\n" +
                       resp.content[:100].decode("latin-1", "ignore"))

pdf_bytes = resp.content                 # ← 之後解析就用這個
print("PDF OK →", PDF_URL)

# 3. 準備輸出目錄與檔名
OUTDIR   = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)
year_tag = datetime.date.today().year - 1911          # 2025→114
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
