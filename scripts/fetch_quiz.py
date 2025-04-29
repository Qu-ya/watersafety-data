"""
從體育署救生員題庫頁面，自動抓取當年度 PDF 並轉成 JSON
"""

import datetime, io, pathlib, re, json
import requests, pdfplumber, pandas as pd
from bs4 import BeautifulSoup          # ← 新加
# --------------------------------------------------
OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)

BASE = "https://isports.sa.gov.tw"
LIST_URL = (
    f"{BASE}/apps/Essay.aspx"
    "?SYS=LGM&MENU_CD=M10&ITEM_CD=T07&MENU_PRG_CD=3&ITEM_PRG_CD=3"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": LIST_URL,               # ← 讓第二次請求帶正確來源
}

# 1. 先抓題庫頁面；同一個 session 會保存 cookie
sess = requests.Session()              # ← 新加
print("GET list page …")
html = sess.get(LIST_URL, headers=HEADERS, timeout=30).text

# 2. 用 BeautifulSoup 找出 PDF 相對路徑
soup = BeautifulSoup(html, "lxml")
link = soup.select_one("div.listbox a[href*='.pdf']")   # 第一個 .pdf 連結
if not link:
    raise RuntimeError("在題庫頁面找不到 .pdf 連結")

rel_path = re.search(r"(LGM/.+?\.pdf)", link["href"]).group(1)
PDF_URL = f"{BASE}/{rel_path}"
print("PDF URL  ➜", PDF_URL)

# 3. 用同一個 session 下載 PDF
print("download pdf …")
resp = sess.get(PDF_URL, headers=HEADERS, timeout=30)
ct   = resp.headers.get("content-type", "")
if not ct.startswith("application/pdf"):
    raise RuntimeError(f"下載失敗：HTTP {resp.status_code} - {ct}")

pdf_bytes = resp.content
print("PDF OK ✓", len(pdf_bytes), "bytes")

# 4. 存檔
year_tag = datetime.date.today().year - 1911
(OUTDIR / f"quiz_{year_tag}.pdf").write_bytes(pdf_bytes)

# 5. 解析 PDF → DataFrame
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text() or ""
        for n, q, ans in re.findall(r"(\d+)\.(.+?)(\([ABCDOX]\))", txt):
            typ  = "TF" if ans in "OX" else "MC"
            rows.append({
                "id"      : f"Q{int(n):04}",
                "chapter" : f"CH{int(n)//100+1:02}",
                "type"    : typ,
                "q"       : q.strip(),
                "choices" : "" if typ=="TF" else "A|B|C|D",
                "ans"     : ans,
                "explain" : ""
            })

# 6. 輸出 JSON
json_path = OUTDIR / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(json_path, orient="records", indent=2, force_ascii=False)
print("Saved", json_path, "with", len(rows), "questions")
