import json
import os
import base64
from io import BytesIO
from flask import Flask, request, jsonify, render_template_string
from PIL import Image
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variables globales para el modelo
model = None
processor = None
device = None

def load_model():
    """Cargar el modelo Qwen2-VL"""
    global model, processor, device
    
    try:
        logger.info("🔄 Cargando modelo Qwen2-VL...")
        
        model_name = "Qwen/Qwen2-VL-7B-Instruct"
        
        # Detectar dispositivo
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔧 Usando dispositivo: {device}")
        
        # Cargar modelo optimizado para Tesla T4
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,  # T4 funciona mejor con float16
            device_map="auto",
            load_in_8bit=True,  # OBLIGATORIO para T4 (16GB VRAM)
            trust_remote_code=True
        )
        
        # Cargar procesador
        processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        logger.info("✅ Modelo cargado correctamente!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        return False

def process_image_from_base64(image_data):
    """Procesar imagen desde base64"""
    try:
        # Remover prefijo data:image si existe
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decodificar base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return image
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return None

def generate_response(image, text_prompt, max_length=512):
    """Generar respuesta del modelo"""
    global model, processor
    
    if model is None or processor is None:
        return "Error: Modelo no cargado"
    
    try:
        # Preparar mensajes
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": text_prompt}
                ]
            }
        ]
        
        # Aplicar template de chat
        text = processor.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Procesar entrada
        inputs = processor(
            text=[text], 
            images=[image], 
            return_tensors="pt"
        )
        
        # Mover al dispositivo
        if device == "cuda":
            inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        # Generar respuesta
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=0.7,
                do_sample=True,
                pad_token_id=processor.tokenizer.eos_token_id
            )
        
        # Decodificar respuesta
        response = processor.batch_decode(
            outputs, 
            skip_special_tokens=True
        )[0]
        
        # Extraer solo la respuesta del asistente
        if "assistant\n" in response:
            response = response.split("assistant\n")[-1].strip()
        
        return response
        
    except Exception as e:
        logger.error(f"Error generando respuesta: {e}")
        return f"Error: {str(e)}"

# Plantilla HTML para la interfaz web
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qwen2-VL Server</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .input-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="file"], textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        textarea { height: 100px; resize: vertical; }
        button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .response { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 4px solid #007bff; }
        .error { border-left-color: #dc3545; background: #f8d7da; }
        .loading { text-align: center; color: #666; }
        .image-preview { max-width: 300px; max-height: 300px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <h1>🤖 Qwen2-VL Vision Language Model</h1>
    
    <div id="status" class="status"></div>
    
    <div class="container">
        <h3>📷 Subir Imagen y Hacer Pregunta</h3>
        
        <div class="input-group">
            <label for="imageInput">Seleccionar Imagen:</label>
            <input type="file" id="imageInput" accept="image/*">
            <img id="imagePreview" class="image-preview" style="display: none;">
        </div>
        
        <div class="input-group">
            <label for="textInput">Pregunta sobre la imagen:</label>
            <textarea id="textInput" placeholder="Describe lo que ves en esta imagen..."></textarea>
        </div>
        
        <button id="analyzeBtn" onclick="analyzeImage()">🔍 Analizar Imagen</button>
        
        <div id="response" class="response" style="display: none;">
            <h4>Respuesta:</h4>
            <div id="responseText"></div>
        </div>
    </div>

    <script>
        // Previsualización de imagen
        document.getElementById('imageInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('imagePreview');
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });

        // Verificar estado del servidor
        function checkStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    if (data.status === 'ready') {
                        statusDiv.className = 'status success';
                        statusDiv.textContent = '✅ Servidor listo - Modelo cargado correctamente';
                    } else {
                        statusDiv.className = 'status error';
                        statusDiv.textContent = '❌ Error: ' + data.message;
                    }
                })
                .catch(error => {
                    const statusDiv = document.getElementById('status');
                    statusDiv.className = 'status error';
                    statusDiv.textContent = '❌ No se puede conectar al servidor';
                });
        }

        // Analizar imagen
        function analyzeImage() {
            const imageInput = document.getElementById('imageInput');
            const textInput = document.getElementById('textInput');
            const analyzeBtn = document.getElementById('analyzeBtn');
            const responseDiv = document.getElementById('response');
            const responseText = document.getElementById('responseText');

            if (!imageInput.files[0]) {
                alert('Por favor selecciona una imagen');
                return;
            }

            if (!textInput.value.trim()) {
                alert('Por favor escribe una pregunta');
                return;
            }

            // Mostrar loading
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = '⏳ Analizando...';
            responseDiv.style.display = 'block';
            responseDiv.className = 'response';
            responseText.innerHTML = '<div class="loading">🔄 Procesando imagen...</div>';

            // Preparar datos
            const formData = new FormData();
            formData.append('image', imageInput.files[0]);
            formData.append('text', textInput.value);

            // Enviar solicitud
            fetch('/analyze', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    responseText.textContent = data.response;
                } else {
                    responseDiv.className = 'response error';
                    responseText.textContent = 'Error: ' + data.error;
                }
            })
            .catch(error => {
                responseDiv.className = 'response error';
                responseText.textContent = 'Error de conexión: ' + error;
            })
            .finally(() => {
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = '🔍 Analizar Imagen';
            });
        }

        // Verificar estado al cargar la página
        checkStatus();
        
        // Verificar estado cada 30 segundos
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Página principal con interfaz web"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    """Endpoint para verificar estado del servidor"""
    global model, processor
    
    if model is not None and processor is not None:
        return jsonify({
            'status': 'ready',
            'message': 'Modelo cargado correctamente',
            'device': str(device),
            'model_loaded': True
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Modelo no cargado',
            'model_loaded': False
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """Endpoint para analizar imagen con texto"""
    global model, processor
    
    try:
        # Verificar que el modelo está cargado
        if model is None or processor is None:
            return jsonify({
                'success': False,
                'error': 'Modelo no cargado'
            }), 500
        
        # Obtener imagen
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó imagen'
            }), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Archivo de imagen vacío'
            }), 400
        
        # Obtener texto
        text_prompt = request.form.get('text', '')
        if not text_prompt.strip():
            return jsonify({
                'success': False,
                'error': 'No se proporcionó texto'
            }), 400
        
        # Procesar imagen
        image = Image.open(image_file.stream)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Generar respuesta
        response = generate_response(image, text_prompt)
        
        return jsonify({
            'success': True,
            'response': response,
            'prompt': text_prompt
        })
        
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/analyze_base64', methods=['POST'])
def analyze_base64():
    """Endpoint para analizar imagen en base64"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros: image y text requeridos'
            }), 400
        
        # Procesar imagen desde base64
        image = process_image_from_base64(data['image'])
        if image is None:
            return jsonify({
                'success': False,
                'error': 'Error procesando imagen base64'
            }), 400
        
        # Generar respuesta
        response = generate_response(image, data['text'])
        
        return jsonify({
            'success': True,
            'response': response,
            'prompt': data['text']
        })
        
    except Exception as e:
        logger.error(f"Error en análisis base64: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'device': str(device) if device else 'unknown'
    })

def main():
    """Función principal"""
    logger.info("🚀 Iniciando servidor Qwen2-VL...")
    
    # Cargar modelo al inicio
    if not load_model():
        logger.error("❌ No se pudo cargar el modelo. El servidor se iniciará sin modelo.")
    
    # Configurar servidor
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🌐 Servidor disponible en: http://{host}:{port}")
    logger.info("📖 Endpoints disponibles:")
    logger.info("  GET  / - Interfaz web")
    logger.info("  GET  /status - Estado del servidor")
    logger.info("  POST /analyze - Analizar imagen (form-data)")
    logger.info("  POST /analyze_base64 - Analizar imagen (base64)")
    logger.info("  GET  /health - Estado de salud")
    
    # Iniciar servidor
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()

