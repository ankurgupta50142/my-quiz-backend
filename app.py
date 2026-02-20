import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_quiz(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    for page in doc:
        rect = page.rect
        # 2-कॉलम लेआउट को संभालने के लिए (जैसे APS Target Paper)
        left = page.get_text("text", clip=fitz.Rect(0, 0, rect.width/2, rect.height))
        right = page.get_text("text", clip=fitz.Rect(rect.width/2, 0, rect.width, rect.height))
        text = re.sub(r'\s+', ' ', (left or "") + "\n" + (right or ""))
        blocks = re.split(r'(\d+)\.\s+', text)
        for i in range(1, len(blocks), 2):
            q_id, content = blocks[i], blocks[i+1]
            if '(a)' in content and '(b)' in content:
                parts = re.split(r'\(([a-d])\)', content)
                if len(parts) >= 9:
                    final_quiz.append({
                        "id": q_id,
                        "question": parts[0].strip(),
                        "options": {"a": parts[2].strip(), "b": parts[4].strip(), "c": parts[6].strip(), "d": parts[8].strip()}
                    })
    doc.close()
    return final_quiz

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    path = "temp.pdf"
    file.save(path)
    try:
        return jsonify(extract_quiz(path))
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
  
