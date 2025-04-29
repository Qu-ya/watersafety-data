"""
下載救生員題庫 PDF → 解析成 JSON  
每年只要改上面的 PDF_URL (見註解) 就能用
"""

import requests, pathlib, io, datetime, pdfplumber, pandas as pd, re

# ───── ① 這 3 個常數直接抄自 DevTools Payload ─────
DL_URL = "https://isports.sa.gov.tw/apps/FDownload.aspx"

FILE_PATH = (
    "LGM/09/04/1120214/009f3c95-7d06-43d9-a6d8-513a779be3e4.pdf"
)  # ← 網址裡的 FILE_PATH
FILE_NAME = "114年度救生員資格檢定學科測驗題庫.pdf"

# ───── ② 下載 ─────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://isports.sa.gov.tw/apps/FDownload.aspx",
}

FORM = {
    # 這 3 個其實放在 URL 也行；保險起見留在 form 同時送
    "SYS_CD": "LGM",
    "MENU_CD": "M10",
    "ITEM_CD": "T07",
    # 真正決定下載哪個檔案的 3 個欄位
    "ctl00$IsportContents$FILE_PATH": FILE_PATH,
    "ctl00$IsportContents$FILE_NAME": FILE_NAME,
    "ctl00$IsportContents$DOWNLOAD_FILE_NO": "F00000285",  # 原頁面帶的流水號
}

resp = requests.post(DL_URL, headers=HEADERS, data=FORM, timeout=30)

# 確認真的拿到 PDF
ct = resp.headers.get("content-type", "")
if resp.status_code != 200 or not ct.startswith("application/pdf"):
    raise RuntimeError(f"下載失敗：HTTP {resp.status_code} - {ct}")

pdf_bytes = resp.content
print("PDF OK ✔", len(pdf_bytes), "bytes")

# ───── ③ 存檔（方便手動檢查）─────
OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)
year_tag = datetime.date.today().year - 1911  # 2025→114
(OUTDIR / f"quiz_{year_tag}.pdf").write_bytes(pdf_bytes)

# ───── ④ 解析 PDF → rows ─────
rows = []
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    for page in pdf.pages:
        txt = page.extract_text() or ""
        # 每行格式：1.水母罩可分成… (A)　　　或　1.(A)
        for n, q, ans in re.findall(r"(\d+)\.(.*?\n+?)\(([ABCDOX])\)", txt):
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

# ───── ⑤ 輸出 JSON ─────
json_path = OUTDIR / f"quiz_lifeguard_{year_tag}.json"
pd.DataFrame(rows).to_json(json_path, orient="records", indent=2, force_ascii=False)
print("Saved", json_path.name, "with", len(rows), "questions")
