import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def clean_text(text):
    # फालतू स्पेस और नई लाइनों को हटाना
    return re.sub(r'\s+', ' ', text).strip()

def extract_quiz_final(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    
    full_text = ""
    for page in doc:
        # पूरे पेज का टेक्स्ट निकालें
        full_text += page.get_text("text") + "\n"
    
    # सवाल नंबर के हिसाब से टेक्स्ट को तोड़ना (जैसे 1. या 100.)
    # इसमें हमने \n? जोड़ा है ताकि अगर सवाल नई लाइन से शुरू हो तो भी पकड़ ले
    blocks = re.split(r'(?:\n|^)(\d+)\.\s+', full_text)
    
    for i in range(1, len(blocks), 2):
        q_id = blocks[i]
        content = blocks[i+1]
        
        # ऑप्शंस (a), (b), (c), (d) को ढूँढना - इसमें लचीलापन बढ़ाया है
        if '(a)' in content.lower() and '(b)' in content.lower():
            # ऑप्शंस को अलग करने के लिए Regex का उपयोग
            parts = re.split(r'\(([a-dA-D])\)', content)
            
            if len(parts) >= 9:
                final_quiz.append({
                    "id": q_id,
                    "question": clean_text(parts[0]),
                    "options": {
                        "a": clean_text(parts[2]),
                        "b": clean_text(parts[4]),
                        "c": clean_text(parts[6]),
                        "d": clean_text(parts[8])
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
        results = extract_quiz_final(path)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
