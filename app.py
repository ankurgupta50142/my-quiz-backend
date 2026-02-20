import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# CORS एरर रोकने के लिए
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_quiz_436(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    
    full_text = ""
    for page in doc:
        # आपकी PDF सिंगल कॉलम है, इसलिए सीधा टेक्स्ट निकाल रहे हैं
        full_text += page.get_text("text") + "\n"
    
    # फालतू स्पेस हटाना
    full_text = re.sub(r'\s+', ' ', full_text)
    
    # [span_6](start_span)[span_7](start_span)सवाल नंबर ढूँढने का तरीका (जैसे: 1. या 10.)[span_6](end_span)[span_7](end_span)
    blocks = re.split(r'(\d+)\.\s+', full_text)
    
    for i in range(1, len(blocks), 2):
        q_id = blocks[i]
        content = blocks[i+1]
        
        # [span_8](start_span)[span_9](start_span)आपके पेपर में विकल्प (a), (b), (c), (d) के रूप में हैं[span_8](end_span)[span_9](end_span)
        if '(a)' in content and '(b)' in content:
            # विकल्प अलग करना
            parts = re.split(r'\(([a-d])\)', content)
            
            if len(parts) >= 9:
                final_quiz.append({
                    "id": q_id,
                    "question": parts[0].strip(),
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
        results = extract_quiz_436(path)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
