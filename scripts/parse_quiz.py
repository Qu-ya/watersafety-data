import io, pathlib, pdfplumber, pandas as pd, re

# 1. 輸入檔案路徑
IN_PDF = pathlib.Path(__file__).parent.parent / "quiz" / "quiz_114.pdf"

# 2. 開啟 PDF → 擷取文字
with pdfplumber.open(IN_PDF) as pdf:
    rows = []
    for page in pdf.pages:
        txt = page.extract_text() or ""
        for n, q, ans in re.findall(r"(\d+)\.([^\n]+?)\(([ABCDOX])\)", txt):
            # ...（跟你原本解析 row 的邏輯一樣）
            rows.append({...})

# 3. 輸出 JSON
OUT_JSON = IN_PDF.with_suffix(".json")
pd.DataFrame(rows).to_json(OUT_JSON, orient="records", indent=2, force_ascii=False)
print("Saved JSON →", OUT_JSON.name)
