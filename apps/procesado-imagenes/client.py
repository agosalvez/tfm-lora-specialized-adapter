import json
import base64
import requests
import argparse
import os
import sys
from PIL import Image
import io

class QwenVLClient:
    """Cliente para interactuar con el servidor Qwen2-VL"""
    
    def __init__(self, server_url="http://localhost:5000"):
        """Inicializar cliente con URL del servidor"""
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        # Timeout más largo para T4 (es más lenta)
        self.session.timeout = 120
        
    def check_server_status(self):
        """Verificar estado del servidor"""
        try:
            response = self.session.get(f"{self.server_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servidor: {data['status']}")
                print(f"📱 Dispositivo: {data.get('device', 'unknown')}")
                print(f"🤖 Modelo cargado: {'Sí' if data.get('model_loaded') else 'No'}")
                return True
            else:
                print(f"❌ Error del servidor: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ No se puede conectar al servidor: {e}")
            return False
    
    def analyze_image_file(self, image_path, text_prompt, max_retries=3):
        """Analizar imagen desde archivo"""
        if not os.path.exists(image_path):
            print(f"❌ Error: Archivo no encontrado: {image_path}")
            return None
        
        try:
            # Verificar que es una imagen válida
            with Image.open(image_path) as img:
                print(f"📷 Imagen: {image_path} ({img.size[0]}x{img.size[1]}, {img.mode})")
        except Exception as e:
            print(f"❌ Error: Archivo no es una imagen válida: {e}")
            return None
        
        # Enviar solicitud
        for attempt in range(max_retries):
            try:
                print(f"🔄 Enviando solicitud... (intento {attempt + 1}/{max_retries})")
                
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    data = {'text': text_prompt}
                    
                    response = self.session.post(
                        f"{self.server_url}/analyze",
                        files=files,
                        data=data,
                        timeout=120  # Timeout más largo para T4
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print("✅ Análisis completado!")
                        return result['response']
                    else:
                        print(f"❌ Error del servidor: {result.get('error')}")
                        return None
                else:
                    print(f"❌ Error HTTP {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout en intento {attempt + 1}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error de conexión en intento {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                print("🔄 Reintentando...")
        
        print("❌ Falló después de todos los intentos")
        return None
    
    def analyze_image_base64(self, image_path, text_prompt):
        """Analizar imagen usando base64"""
        try:
            # Convertir imagen a base64
            with Image.open(image_path) as img:
                # Convertir a RGB si es necesario
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionar si es muy grande
                if img.size[0] > 1024 or img.size[1] > 1024:
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    print(f"📏 Imagen redimensionada a: {img.size}")
                
                # Convertir a bytes
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                image_bytes = buffer.getvalue()
                
                # Codificar en base64
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                
            print(f"📊 Tamaño de imagen en base64: {len(image_b64)} caracteres")
            
            # Enviar solicitud
            payload = {
                'image': f"data:image/jpeg;base64,{image_b64}",
                'text': text_prompt
            }
            
            response = self.session.post(
                f"{self.server_url}/analyze_base64",
                json=payload,
                timeout=120  # Timeout más largo para T4
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Análisis completado!")
                    return result['response']
                else:
                    print(f"❌ Error del servidor: {result.get('error')}")
                    return None
            else:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error procesando imagen: {e}")
            return None
    
    def interactive_mode(self):
        """Modo interactivo para hacer múltiples consultas"""
        print("🎯 Modo interactivo iniciado")
        print("📝 Comandos disponibles:")
        print("  - 'exit' o 'quit': Salir")
        print("  - 'status': Verificar estado del servidor")
        print("  - 'help': Mostrar ayuda")
        print("-" * 50)
        
        while True:
            try:
                # Solicitar ruta de imagen
                image_path = input("\n📷 Ruta de la imagen (o comando): ").strip()
                
                if image_path.lower() in ['exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break
                elif image_path.lower() == 'status':
                    self.check_server_status()
                    continue
                elif image_path.lower() == 'help':
                    print("📝 Ayuda:")
                    print("  - Introduce la ruta completa a una imagen")
                    print("  - Luego escribe tu pregunta sobre la imagen")
                    print("  - El servidor analizará la imagen y responderá")
                    continue
                
                if not image_path:
                    continue
                
                # Verificar que existe el archivo
                if not os.path.exists(image_path):
                    print(f"❌ Archivo no encontrado: {image_path}")
                    continue
                
                # Solicitar pregunta
                text_prompt = input("❓ Tu pregunta sobre la imagen: ").strip()
                if not text_prompt:
                    print("❌ Por favor escribe una pregunta")
                    continue
                
                # Analizar imagen
                print("\n" + "="*50)
                result = self.analyze_image_file(image_path, text_prompt)
                
                if result:
                    print(f"\n🤖 Respuesta del modelo:")
                    print("-" * 30)
                    print(result)
                    print("-" * 30)
                else:
                    print("❌ No se pudo obtener respuesta")
                print("="*50)
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except EOFError:
                print("\n👋 ¡Hasta luego!")
                break
    
    def batch_analyze(self, image_folder, questions_file):
        """Analizar múltiples imágenes en lote"""
        if not os.path.exists(image_folder):
            print(f"❌ Carpeta no encontrada: {image_folder}")
            return
        
        if not os.path.exists(questions_file):
            print(f"❌ Archivo de preguntas no encontrado: {questions_file}")
            return
        
        # Cargar preguntas
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ Error leyendo archivo de preguntas: {e}")
            return
        
        # Buscar imágenes
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
        image_files = []
        
        for file in os.listdir(image_folder):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(image_folder, file))
        
        if not image_files:
            print(f"❌ No se encontraron imágenes en: {image_folder}")
            return
        
        print(f"📁 Encontradas {len(image_files)} imágenes")
        print(f"❓ Usando {len(questions)} preguntas")
        
        # Procesar cada imagen con cada pregunta
        results = []
        total = len(image_files) * len(questions)
        current = 0
        
        for image_file in image_files:
            for question in questions:
                current += 1
                print(f"\n🔄 Procesando {current}/{total}: {os.path.basename(image_file)}")
                print(f"❓ Pregunta: {question}")
                
                result = self.analyze_image_file(image_file, question)
                
                results.append({
                    'image': image_file,
                    'question': question,
                    'response': result,
                    'success': result is not None
                })
                
                if result:
                    print(f"✅ Completado")
                else:
                    print(f"❌ Falló")
        
        # Guardar resultados
        output_file = 'batch_results.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 Resultados guardados en: {output_file}")
        except Exception as e:
            print(f"❌ Error guardando resultados: {e}")

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description="Cliente para Qwen2-VL Server")
    parser.add_argument('--server', default='http://localhost:5000', 
                       help='URL del servidor (default: http://localhost:5000)')
    parser.add_argument('--image', help='Ruta de la imagen a analizar')
    parser.add_argument('--text', help='Pregunta sobre la imagen')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Modo interactivo')
    parser.add_argument('--batch', help='Carpeta con imágenes para análisis en lote')
    parser.add_argument('--questions', help='Archivo con preguntas para análisis en lote')
    parser.add_argument('--base64', action='store_true', 
                       help='Usar método base64 en lugar de upload')
    parser.add_argument('--status', action='store_true', 
                       help='Solo verificar estado del servidor')
    
    args = parser.parse_args()
    
    # Crear cliente
    client = QwenVLClient(args.server)
    
    print(f"🌐 Conectando a: {args.server}")
    
    # Solo verificar estado
    if args.status:
        client.check_server_status()
        return
    
    # Verificar servidor
    if not client.check_server_status():
        print("❌ No se puede conectar al servidor. Verifica que esté ejecutándose.")
        sys.exit(1)
    
    # Modo interactivo
    if args.interactive:
        client.interactive_mode()
        return
    
    # Análisis en lote
    if args.batch:
        questions_file = args.questions or 'questions.txt'
        client.batch_analyze(args.batch, questions_file)
        return
    
    # Análisis individual
    if args.image and args.text:
        print(f"\n📷 Analizando imagen: {args.image}")
        print(f"❓ Pregunta: {args.text}")
        print("-" * 50)
        
        if args.base64:
            result = client.analyze_image_base64(args.image, args.text)
        else:
            result = client.analyze_image_file(args.image, args.text)
        
        if result:
            print(f"\n🤖 Respuesta:")
            print(result)
        else:
            print("❌ No se pudo obtener respuesta")
        return
    
    # Si no hay argumentos específicos, mostrar ayuda
    print("📖 Uso del cliente:")
    print("  python client.py --interactive                    # Modo interactivo")
    print("  python client.py --image foto.jpg --text '¿Qué ves?'  # Análisis individual")
    print("  python client.py --batch ./imagenes --questions preguntas.txt  # Lote")
    print("  python client.py --status                         # Estado del servidor")
    print("\nEjemplos:")
    print("  python client.py -i")
    print("  python client.py --image ejemplo.jpg --text 'Describe esta imagen'")
    print("  python client.py --batch ./fotos --questions mis_preguntas.txt")

if __name__ == '__main__':
    main()
