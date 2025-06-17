import requests
import json
import base64

# Cambia esto por la ruta a tu archivo PDF
pdf_path = 'tamariz.pdf'
url = 'http://localhost:5000/process_pdf'

with open(pdf_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)

if response.status_code == 200:
    data = response.json()
    
    print("\n--- MARKDOWN ---\n")
    print(data['markdown'])

    print(f"\n--- {len(data['images'])} IMAGEN(ES) EXTRAÍDA(S) ---\n")
    for i, img_b64 in enumerate(data['images']):
        with open(f'image_{i+1}.png', 'wb') as out_img:
            out_img.write(base64.b64decode(img_b64))
        print(f"Imagen guardada: image_{i+1}.png")
else:
    print("❌ Error:", response.status_code, response.text)
