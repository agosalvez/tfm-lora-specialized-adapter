"""
Cliente de prueba para la API de extracción de texto e imágenes
Probado y funcional
"""

import requests
import json
import base64
from PIL import Image
import io
import os

API_URL = "http://localhost:5000"

def test_health():
    """Verifica que la API esté funcionando"""
    print("🔍 Verificando estado de la API...")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API funcionando correctamente")
            print(f"   PyMuPDF versión: {data.get('pymupdf_version', 'N/A')}")
            return True
        else:
            print(f"❌ API respondió con código: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        print("   ¿Está ejecutándose el servidor Flask?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def process_pdf(pdf_path):
    """Procesa un archivo PDF y extrae texto e imágenes"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        return False
    
    print(f"📄 Procesando: {pdf_path}")
    
    try:
        # Abrir archivo y enviarlo a la API
        with open(pdf_path, 'rb') as file:
            files = {'file': file}
            
            response = requests.post(
                f"{API_URL}/process-document",
                files=files,
                timeout=60  # 60 segundos timeout
            )
        
        # Verificar respuesta
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("✅ Documento procesado exitosamente")
                print_results(data)
                save_results(data)
                return True
            else:
                print(f"❌ Error en el procesamiento: {data.get('error', 'Error desconocido')}")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Error desconocido')}")
            except:
                print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - el servidor tardó demasiado en responder")
        return False
    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
        return False

def print_results(data):
    """Muestra un resumen de los resultados"""
    
    file_info = data.get('file_info', {})
    text_info = data.get('extracted_text', {})
    images_info = data.get('extracted_images', {})
    
    print("\n" + "="*50)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*50)
    
    # Información del archivo
    print(f"📄 Archivo: {file_info.get('filename', 'N/A')}")
    print(f"📏 Tamaño: {file_info.get('size_bytes', 0):,} bytes")
    print(f"📃 Páginas: {file_info.get('pages', 0)}")
    
    # Información del texto
    print(f"\n📝 TEXTO EXTRAÍDO:")
    print(f"   - Caracteres: {text_info.get('length_chars', 0):,}")
    print(f"   - Tiene texto: {'Sí' if text_info.get('has_text') else 'No'}")
    
    # Información de imágenes
    print(f"\n🖼️ IMÁGENES EXTRAÍDAS:")
    print(f"   - Cantidad: {images_info.get('count', 0)}")
    
    if images_info.get('count', 0) > 0:
        for img in images_info.get('images', []):
            dims = img.get('dimensiones', {})
            size_kb = img.get('tamaño_bytes', 0) / 1024
            print(f"   - Imagen {img.get('id')}: {dims.get('ancho')}x{dims.get('alto')} px ({size_kb:.1f} KB)")
    
    # Muestra del texto
    text_content = text_info.get('content', '')
    markdown_content = text_info.get('markdown', '')
    
    if text_content:
        print(f"\n📄 MUESTRA DEL TEXTO ORIGINAL (primeros 200 caracteres):")
        print("-" * 30)
        print(text_content[:200] + ("..." if len(text_content) > 200 else ""))
    
    if markdown_content:
        print(f"\n📝 MUESTRA DEL MARKDOWN (primeros 300 caracteres):")
        print("-" * 30)
        print(markdown_content[:300] + ("..." if len(markdown_content) > 300 else ""))

def save_results(data):
    """Guarda los resultados en archivos"""
    
    print(f"\n💾 GUARDANDO RESULTADOS...")
    
    # Guardar texto extraído (formato original)
    text_content = data.get('extracted_text', {}).get('content', '')
    if text_content:
        with open('texto_extraido.txt', 'w', encoding='utf-8') as f:
            f.write(text_content)
        print("   ✅ Texto plano guardado: texto_extraido.txt")
    
    # Guardar texto en formato Markdown con marcadores de imágenes
    markdown_content = data.get('extracted_text', {}).get('markdown', '')
    if markdown_content:
        with open('texto_extraido.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print("   ✅ Texto Markdown guardado: texto_extraido.md")
    
    # Guardar imágenes
    images = data.get('extracted_images', {}).get('images', [])
    if images:
        for img in images:
            try:
                # Decodificar base64
                img_data = base64.b64decode(img['base64'])
                
                # Crear nombre de archivo
                filename = f"imagen_p{img['pagina']}_id{img['id']}.png"
                
                # Guardar imagen
                with open(filename, 'wb') as f:
                    f.write(img_data)
                
                # Mostrar info de posición si está disponible
                pos_info = ""
                if img.get('posicion_en_pagina'):
                    pos = img['posicion_en_pagina']
                    pos_info = f" (pos: x={pos['x']:.0f}, y={pos['y']:.0f})"
                
                print(f"   ✅ Imagen guardada: {filename}{pos_info}")
                
            except Exception as e:
                print(f"   ❌ Error guardando imagen {img.get('id')}: {e}")
    
    # Guardar JSON completo
    with open('resultado_completo.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("   ✅ JSON completo guardado: resultado_completo.json")

def main():
    """Función principal"""
    
    print("🧪 CLIENTE DE PRUEBA - EXTRACTOR DE TEXTO E IMÁGENES")
    print("="*60)
    
    # 1. Verificar API
    if not test_health():
        print("\n💡 Para iniciar la API ejecuta: python app.py")
        return
    
    # 2. Buscar archivo PDF
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("\n❌ No se encontraron archivos PDF en el directorio actual")
        print("💡 Coloca un archivo PDF en esta carpeta y vuelve a ejecutar")
        return
    
    # 3. Usar el primer PDF encontrado
    pdf_path = pdf_files[0]
    print(f"\n📁 Archivo PDF encontrado: {pdf_path}")
    
    # 4. Procesar archivo
    success = process_pdf(pdf_path)
    
    if success:
        print(f"\n🎉 ¡Procesamiento completado exitosamente!")
        print("📁 Archivos generados:")
        print("   - texto_extraido.txt (formato original)")
        print("   - texto_extraido.md (Markdown con marcadores de imágenes)")
        print("   - imagen_p*_id*.png (si hay imágenes)")
        print("   - resultado_completo.json")
    else:
        print(f"\n❌ El procesamiento falló")

if __name__ == "__main__":
    main()