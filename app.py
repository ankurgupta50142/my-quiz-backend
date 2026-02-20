import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Krutidev को पढ़ने के लिए स्पेशल पैटर्न
def extract_quiz_krutidev(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    # Krutidev में (a) अक्सर 'v' 'k' जैसे कोड में दिखता है
    # इसलिए हम नंबरिंग (1., 2.) पर फोकस करेंगे
    blocks = re.split(r'(\d+)\.\s+', full_text)
    
    for i in range(1, len(blocks), 2):
        q_id = blocks[i]
        content = blocks[i+1]
        
        # Krutidev में ब्रैकेट और ऑप्शंस को पकड़ने का लचीला तरीका
        # हम मान के चलेंगे कि सवाल के बाद 4 विकल्प 'v', 'c', 'n' जैसे कोड में हो सकते हैं
        if 'a' in content.lower() or 'v' in content: 
            parts = re.split(r'\(', content) # ब्रैकेट से तोड़ना
            if len(parts) >= 5:
                final_quiz.append({
                    "id": q_id,
                    "question": parts[0].strip(),
                    "options": {
                        "a": parts[1].strip(),
                        "b": parts[2].strip(),
                        "c": parts[3].strip(),
                        "d": parts[4].strip()
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
        # Krutidev फॉर्मेट के लिए एक्सट्रैक्शन
        results = extract_quiz_krutidev(path)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
