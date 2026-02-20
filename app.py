import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_quiz_ultimate(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    full_text = "\n"
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()
    
    # सवाल नंबर के आधार पर बांटना (जैसे: लाइन के शुरू में '1. ')
    blocks = re.split(r'\n(\d+)\.\s+', full_text)
    
    for i in range(1, len(blocks)-1, 2):
        q_id = blocks[i]
        content = blocks[i+1]
        
        # फालतू स्पेस हटाना
        content = re.sub(r'\s+', ' ', content).strip()
        
        # ऑप्शंस (a), (b), (c), (d) को ढूँढना
        a_m = re.search(r'\(\s*[aA]\s*\)', content)
        b_m = re.search(r'\(\s*[bB]\s*\)', content)
        c_m = re.search(r'\(\s*[cC]\s*\)', content)
        d_m = re.search(r'\(\s*[dD]\s*\)', content)
        
        if a_m and b_m and c_m and d_m:
            opts = [
                ('a', a_m.start(), a_m.end()),
                ('b', b_m.start(), b_m.end()),
                ('c', c_m.start(), c_m.end()),
                ('d', d_m.start(), d_m.end())
            ]
            opts.sort(key=lambda x: x[1]) # जो पहले आए, उसे पहले रखना
            
            # सवाल वह है जो पहले ऑप्शन से पहले लिखा है
            question_text = content[:opts[0][1]].strip()
            
            options_dict = {}
            for j in range(4):
                key = opts[j][0]
                start_val = opts[j][2]
                end_val = opts[j+1][1] if j < 3 else len(content)
                options_dict[key] = content[start_val:end_val].strip()
            
            final_quiz.append({
                "id": q_id,
                "question": question_text,
                "options": options_dict
            })
    return final_quiz

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file"}), 400
    path = "temp.pdf"
    file.save(path)
    try:
        return jsonify(extract_quiz_ultimate(path))
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
