from flask import Flask, request, jsonify
import base64
import tempfile
import os
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter

app = Flask(__name__)
converter = DocumentConverter()  # carga los modelos internos

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        file.save(input_path)

        # Convertir PDF a documento Docling
        result = converter.convert(input_path)
        markdown_text = result.document.export_to_markdown()

        # Extraer imágenes del PDF
        images_b64 = []
        pdf = fitz.open(input_path)
        for img in pdf.get_page_images(0, full=True):  # itera todas las páginas e imágenes
            xref = img[0]
            base_img = pdf.extract_image(xref)
            img_bytes = base_img["image"]
            images_b64.append(base64.b64encode(img_bytes).decode('utf-8'))

    return jsonify({"markdown": markdown_text, "images": images_b64})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
