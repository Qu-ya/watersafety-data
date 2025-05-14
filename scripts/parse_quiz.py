# 讀完 full_text 之後，改用這一段切題
import re

pattern = re.compile(r'(.+。)(?=\s|$)')
items = pattern.findall(full_text)

questions = []
for i, text in enumerate(items, 1):
    questions.append({
        "num": i,
        "question": text.strip()
    })

print(f"✅ Parsed {len(questions)} 題")  # 應該是 701
