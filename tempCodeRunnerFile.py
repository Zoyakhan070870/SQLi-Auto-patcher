from flask import Flask, request, render_template, send_file, abort
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

@app.route('/', methods=['GET', 'POST'])
def index():
    patched_file_path = None
    original_code = None
    patched_code = None
    uploaded_filename = None

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file and allowed_file(uploaded_file.filename):
            uploaded_filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_filename)
            uploaded_file.save(file_path)

            patched_file_path = os.path.join(OUTPUT_FOLDER, f'patched_{uploaded_filename}')
            with open(file_path, 'r') as f:
                original_code = f.read()

            patched_code = auto_patch(original_code)

            with open(patched_file_path, 'w') as f:
                f.write(patched_code)
        else:
            abort(400, description="Invalid file. Only Python (.py) files are allowed.")

    # Pass 'os' to the template
    return render_template('index.html',
                           original_code=original_code,
                           patched_code=patched_code,
                           patched_file_path=patched_file_path,
                           uploaded_filename=uploaded_filename,
                           os=os)  # Add this line

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
