import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_quiz_super(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    
    full_text = ""
    for page in doc:
        rect = page.rect
        # 2-कॉलम वाली PDF को सही से पढ़ने के लिए पेज को 2 हिस्सों में बाँटना
        left = page.get_text("text", clip=fitz.Rect(0, 0, rect.width/2, rect.height))
        right = page.get_text("text", clip=fitz.Rect(rect.width/2, 0, rect.width, rect.height))
        full_text += (left or "") + "\n" + (right or "") + "\n"
    doc.close()
    
    # सारे फालतू स्पेस हटाकर उसे एक साफ़ लाइन में बदलना
    clean_text = re.sub(r'\s+', ' ', full_text)
    
    # 1. 2. 3. (सवाल नंबर) के आधार पर टेक्स्ट को काटना
    parts = re.split(r'\s(\d{1,3})\.\s+', " " + clean_text)
    
    for i in range(1, len(parts)-1, 2):
        q_id = parts[i]
        content = parts[i+1]
        
        # (a), (b), (c), (d) की जगह ढूँढना (चाहे वे कैपिटल में हों या स्माल में)
        a_idx = content.lower().find('(a)')
        b_idx = content.lower().find('(b)')
        c_idx = content.lower().find('(c)')
        d_idx = content.lower().find('(d)')
        
        # अगर सवाल में कम से कम (a) और (b) मौजूद हैं, तभी उसे सेव करें
        if a_idx != -1 and b_idx != -1:
            question_text = content[:a_idx].strip()
            
            opts_positions = []
            for char, idx in [('a', a_idx), ('b', b_idx), ('c', c_idx), ('d', d_idx)]:
                if idx != -1:
                    opts_positions.append((char, idx))
            opts_positions.sort(key=lambda x: x[1])
            
            options_dict = {"a": "", "b": "", "c": "", "d": ""}
            
            for j in range(len(opts_positions)):
                char, start_idx = opts_positions[j]
                end_idx = opts_positions[j+1][1] if j+1 < len(opts_positions) else len(content)
                
                # ऑप्शन का टेक्स्ट निकालना और शुरू का (a) हटाना
                opt_text = content[start_idx:end_idx].strip()
                opt_text = re.sub(r'^\([a-dA-D]\)\s*', '', opt_text)
                options_dict[char] = opt_text
            
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
        return jsonify(extract_quiz_super(path))
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
