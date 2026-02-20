import os
import re
import fitz
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_quiz_aps(pdf_path):
    final_quiz = []
    doc = fitz.open(pdf_path)
    
    full_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect
        
        # 2-कॉलम को सही से पढ़ने का लॉजिक
        left = page.get_text("text", clip=fitz.Rect(0, 0, rect.width/2, rect.height))
        right = page.get_text("text", clip=fitz.Rect(rect.width/2, 0, rect.width, rect.height))
        
        full_text += (left or "") + "\n" + (right or "") + "\n"
        
    doc.close()
    
    # फालतू न्यूलाइन हटाकर टेक्स्ट को व्यवस्थित करना
    clean_text = re.sub(r'\n+', '\n', full_text)
    
    # '1. ', '2. ' (सवाल नंबर) के आधार पर अलग करना
    blocks = re.split(r'\n(\d{1,2})\.\s+', "\n" + clean_text)
    
    for i in range(1, len(blocks)-1, 2):
        q_id = blocks[i]
        content = blocks[i+1]
        
        # (a), (b), (c), (d) विकल्पों को खोजना
        a_idx = re.search(r'\(\s*[aA]\s*\)', content)
        b_idx = re.search(r'\(\s*[bB]\s*\)', content)
        c_idx = re.search(r'\(\s*[cC]\s*\)', content)
        d_idx = re.search(r'\(\s*[dD]\s*\)', content)
        
        # अगर सवाल में (a) और (b) हैं, तभी उसे सवाल मानना (इससे पहले पेज के निर्देश अपने आप हट जाएंगे)
        if a_idx and b_idx:
            # सवाल का टेक्स्ट (a) शुरू होने से पहले तक का है
            q_text = content[:a_idx.start()].strip()
            # सवाल के अंदर की लाइनों को एक साथ जोड़ना
            q_text = q_text.replace('\n', ' ')
            
            # ऑप्शंस को उनकी जगह के हिसाब से निकालना
            opts = []
            if a_idx: opts.append(('a', a_idx.start(), a_idx.end()))
            if b_idx: opts.append(('b', b_idx.start(), b_idx.end()))
            if c_idx: opts.append(('c', c_idx.start(), c_idx.end()))
            if d_idx: opts.append(('d', d_idx.start(), d_idx.end()))
            
            # ऑप्शंस को सही क्रम में सेट करना
            opts.sort(key=lambda x: x[1])
            
            options_dict = {"a": "", "b": "", "c": "", "d": ""}
            for j in range(len(opts)):
                key = opts[j][0]
                start_pos = opts[j][2]
                end_pos = opts[j+1][1] if j+1 < len(opts) else len(content)
                
                # ऑप्शन के टेक्स्ट से फालतू लाइन हटाना
                options_dict[key] = content[start_pos:end_pos].replace('\n', ' ').strip()
            
            final_quiz.append({
                "id": q_id,
                "question": q_text,
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
        return jsonify(extract_quiz_aps(path))
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run()
