from flask import Flask, request, jsonify, send_file, abort
import os
from patcher import auto_patch
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'py'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to upload a Python file, patch it, and return the patched file path.
    """
    uploaded_file = request.files.get('file')
    if uploaded_file and allowed_file(uploaded_file.filename):
        uploaded_filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_filename)
        uploaded_file.save(file_path)

        # Check if the file is empty or not
        if os.path.getsize(file_path) == 0:
            return jsonify({"error": "Uploaded file is empty."}), 400

        patched_file_path = os.path.join(OUTPUT_FOLDER, f'patched_{uploaded_filename}')
        
        try:
            with open(file_path, 'r') as f:
                original_code = f.read()
            
            # Apply the patching function
            patched_code = auto_patch(original_code)

            with open(patched_file_path, 'w') as f:
                f.write(patched_code)

            return jsonify({
                "message": "File uploaded and patched successfully.",
                "patched_file_path": patched_file_path
            })
        
        except Exception as e:
            return jsonify({"error": f"Error processing the file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file. Only Python (.py) files are allowed."}), 400

@app.route('/api/patch', methods=['POST'])
def patch_code():
    """
    Endpoint to accept Python code, patch it, and return the patched code as JSON.
    """
    data = request.get_json()

    if 'code' not in data:
        return jsonify({"error": "No code provided in the request body."}), 400
    
    original_code = data['code']
    
    try:
        patched_code = auto_patch(original_code)
        return jsonify({"patched_code": patched_code})
    
    except Exception as e:
        return jsonify({"error": f"Error patching the code: {str(e)}"}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Endpoint to download a patched file.
    """
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found."}), 404

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
