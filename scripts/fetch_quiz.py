"""
抓取體育署救生員題庫：
1. 先 GET 題庫頁擷取表單隱藏欄位
2. 帶完整 payload POST 取得 PDF
3. 存成 quiz_<year>.pdf，再解析成 JSON
"""

import requests, pathlib, io, datetime, pdfplumber, pandas as pd, re
from bs4 import BeautifulSoup            # <—— 新增

# ------- 基本常數（只有 FILE_* 兩行每年要手動換） -------
LIST_URL  = "https://isports.sa.gov.tw/apps/FDownload.aspx"
FILE_PATH = "LGM/09/04/1120214/009f3c95-7d06-43d9-a6d8-513a779be3e4.pdf"
FILE_NAME = "114年度救生員資格檢定學科測驗題庫.pdf"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)
HEAD = {"User-Agent": UA, "Referer": LIST_URL}

# ------- ① 先 GET 頁面抓 __VIEWSTATE… 等隱藏欄位 -------
html = requests.get(LIST_URL, headers=HEAD, timeout=30).text
soup = BeautifulSoup(html, "lxml")
payload = {
    "SYS_CD": "LGM",
    "MENU_CD": "M10",
    "ITEM_CD": "T07",
    "ctl00$IsportContents$FILE_PATH":  FILE_PATH,
    "ctl00$IsportContents$FILE_NAME":  FILE_NAME,
    "ctl00$IsportContents$DOWNLOAD_FILE_NO": "F00000285",
}
# 把所有 <input type="hidden"> 一併帶進來
for tag in soup.select("input[type=hidden][name]"):
    payload.setdefault(tag["name"], tag.get("value", ""))

# ------- ② POST 下載 PDF -------
resp = requests.post(LIST_URL, headers=HEAD, data=payload, timeout=30)
ct   = resp.headers.get("content-type", "")
if resp.status_code != 200 or not ct.startswith("application/pdf"):
    raise RuntimeError(f"下載失敗：HTTP {resp.status_code} - {ct}")

pdf_bytes = resp.content
print("PDF OK ✔", len(pdf_bytes), "bytes")

# ------- ③ 存檔 -------
OUTDIR   = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)
year_tag = datetime.date.today().year - 1911          # 2025→114
(OUTDIR / f"quiz_{year_tag}.pdf").write_bytes(pdf_bytes)

# ------- ④ 解析 PDF -------
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for pg in pdf.pages:
        txt = pg.extract_text() or ""
        for n, q, ans in re.findall(r"(\d+)\.(.*?)\(([ABCDOX])\)", txt, flags=re.S):
            typ = "TF" if ans in "OX" else "MC"
            rows.append(
                {
                    "id": f"{int(n):04}",
                    "chapter": f"CH{int(n)//100+1:02}",
                    "type": typ,
                    "q": q.strip(),
                    "choices": "" if typ == "TF" else "A|B|C|D",
                    "ans": ans,
                    "explain": "",
                }
            )

# ------- ⑤ 輸出 JSON -------
json_path = OUTDIR / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(json_path, orient="records", indent=2, force_ascii=False)
print("Saved", json_path.name, "with", len(rows), "questions")
