#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動下載體育署救生員題庫 PDF → 確認下載成功
"""

import io
import datetime
import pathlib
import re

import requests
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup

# 1. 題庫列表頁 URL（必須先定義）
LIST_URL = (
    "https://isports.sa.gov.tw/apps/Essay.aspx"
    "?SYS=LGM"
    "&MENU_CD=M10"
    "&ITEM_CD=T07"
    "&MENU_PRG_CD=3"
    "&ITEM_PRG_CD=3"
)

# 2. 準備輸出資料夾
OUTDIR = pathlib.Path(__file__).parent.parent / "quiz"
OUTDIR.mkdir(exist_ok=True)

# 3. 建立 Session & Headers
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": LIST_URL,
}

# 4. GET 題庫列表頁
print("GET list page …", LIST_URL)
resp1 = session.get(LIST_URL, headers=HEADERS, timeout=30)
resp1.raise_for_status()
html = resp1.text

# 5. 用 BeautifulSoup 找 <form id="aspnetForm">
soup = BeautifulSoup(html, "lxml")
form = soup.find("form", id="aspnetForm")
if not form:
    print("▶ HTML 前 300 字：\n", html[:300])
    raise RuntimeError("找不到 ASP.NET Form")

# 6. 收集所有 hidden input 欄位，作為 POST payload
payload = {
    inp.get("name"): inp.get("value", "")
    for inp in form.select("input[type=hidden]")
    if inp.get("name")
}

# 7. 設定下載觸發參數
payload["__EVENTTARGET"]   = "ctl00$IsportContent$FileDownLoad"
payload["__EVENTARGUMENT"] = ""

# 8. POST 觸發下載 PDF
DOWNLOAD_URL = f"https://isports.sa.gov.tw{form['action']}"
print("POST download PDF …", DOWNLOAD_URL)
resp2 = session.post(DOWNLOAD_URL, headers=HEADERS, data=payload, timeout=60)
resp2.raise_for_status()

# 9. 檢查回傳一定是 PDF
ct = resp2.headers.get("Content-Type", "")
if not ct.startswith("application/pdf"):
    print("▶ 下載回傳 Content-Type =", ct)
    print("▶ 回傳前 300 字：\n", resp2.text[:300])
    raise RuntimeError("下載失敗，非 PDF")

pdf_bytes = resp2.content
print("PDF OK ✔", len(pdf_bytes), "bytes")

# 10. 暫存成 quiz.pdf
pdf_path = OUTDIR / "quiz.pdf"
pdf_path.write_bytes(pdf_bytes)
print("Saved PDF →", pdf_path.name)
