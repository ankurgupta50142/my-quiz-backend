import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_quiz_fixed(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    # KrutiDev में ब्रैकेट और नंबर अलग तरह से दिखते हैं
    # हम नंबर (1. से 100.) के आधार पर ब्लॉक तोड़ेंगे
    blocks = re.split(r'(\d+)\.\s+', full_text)
    
    for i in range(1, len(blocks), 2):
        q_id = blocks[i]
        content = blocks[i+1]
        
        # KrutiDev में (a) के लिए 'v' और (b) के लिए 'k' जैसे अक्षर इस्तेमाल होते हैं
        # हम '(' ब्रैकेट के आधार पर ऑप्शंस बाँटेंगे
        parts = re.split(r'\(', content)
        if len(parts) >= 5:
            final_quiz.append({
                "id": q_id,
                "question": parts[0].strip(),
                "options": {
                    "a": parts[1].replace('a)', '').strip(),
                    "b": parts[2].replace('b)', '').strip(),
                    "c": parts[3].replace('c)', '').strip(),
                    "d": parts[4].replace('d)', '').strip()
                }
            })
    doc.close()
    return final_quiz

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file"}), 400
    path = "temp.pdf"
    file.save(path)
    try:
        results = extract_quiz_fixed(path)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
