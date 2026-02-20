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
        # पेज का पूरा टेक्स्ट निकालें (टेबल फॉर्मेट को ध्यान में रखते हुए)
        full_text += page.get_text("text") + "\n"
    
    # फालतू स्पेस को साफ़ करें लेकिन लाइन ब्रेक का ध्यान रखें
    clean_text = re.sub(r' +', ' ', full_text)
    
    # सवाल नंबर के आधार पर बाँटें (जैसे 1. या 10.)
    [span_5](start_span)#
    blocks = re.split(r'(\n\d+\.\s+)', clean_text)
    
    for i in range(1, len(blocks), 2):
        q_header = blocks[i].strip()
        content = blocks[i+1]
        
        # आपके पेपर में (a), (b), (c), (d) विकल्प हैं[span_5](end_span)
        if '(a)' in content and '(b)' in content:
            parts = re.split(r'\(([a-d])\)', content)
            
            if len(parts) >= 9:
                # सवाल का पूरा हिस्सा (टेबल/मैचिंग के साथ)
                question_text = q_header + " " + parts[0].strip()
                
                final_quiz.append({
                    "id": q_header.replace('.', ''),
                    "question": question_text,
                    "options": {
                        "a": parts[2].strip(),
                        "b": parts[4].strip(),
                        "c": parts[6].strip(),
                        "d": parts[8].strip()
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
