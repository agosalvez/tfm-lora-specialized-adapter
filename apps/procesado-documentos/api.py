"""
API Flask para extraer texto e imágenes de documentos PDF
Usando PyMuPDF - Código completo y funcional
"""

from flask import Flask, request, jsonify
import os
import tempfile
import base64
from datetime import datetime
import traceback

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF no está instalado")
    print("Ejecuta: pip install PyMuPDF")
    exit(1)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo

def extract_text_and_images(pdf_path):
    """
    Extrae texto e imágenes de un PDF usando PyMuPDF
    Retorna: (texto_completo, texto_markdown, lista_imagenes, numero_paginas)
    """
    doc = None
    try:
        # Abrir el documento PDF
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        
        # Variables para almacenar resultados
        texto_completo = ""
        texto_markdown = ""
        lista_imagenes = []
        
        # Procesar cada página
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # OBTENER POSICIONES DE IMÁGENES PRIMERO
            image_list = page.get_images(full=True)
            posiciones_imagenes = []
            
            for img_index, img in enumerate(image_list):
                try:
                    # Obtener bbox de la imagen en la página
                    img_rects = page.get_image_rects(img[0])
                    if img_rects:
                        # Usar la primera posición si hay varias
                        rect = img_rects[0]
                        posiciones_imagenes.append({
                            'img_index': img_index,
                            'y_position': rect.y0,  # Posición Y superior
                            'rect': rect
                        })
                except:
                    continue
            
            # Ordenar imágenes por posición Y (de arriba hacia abajo)
            posiciones_imagenes.sort(key=lambda x: x['y_position'])
            
            # EXTRAER TEXTO de la página
            texto_pagina = page.get_text()
            
            if texto_pagina.strip():  # Solo agregar si hay texto
                # Texto simple (mantener formato original)
                texto_completo += f"=== PÁGINA {page_num + 1} ===\n\n"
                texto_completo += texto_pagina
                texto_completo += "\n\n" + "="*50 + "\n\n"
                
                # Texto en Markdown con marcadores de imágenes
                texto_markdown += f"# Página {page_num + 1}\n\n"
                
                # Dividir texto en líneas para insertar marcadores de imágenes
                lineas_texto = texto_pagina.split('\n')
                texto_con_imagenes = []
                
                # Insertar marcadores de imagen aproximadamente donde corresponden
                for i, linea in enumerate(lineas_texto):
                    texto_con_imagenes.append(linea)
                    
                    # Si hay imágenes en esta página, insertar marcadores
                    for pos_img in posiciones_imagenes:
                        img_idx = pos_img['img_index']
                        # Insertar marcador aproximadamente en el medio del texto
                        if i == len(lineas_texto) // (len(posiciones_imagenes) + 1) * (posiciones_imagenes.index(pos_img) + 1):
                            img_id = len(lista_imagenes) + img_idx + 1
                            texto_con_imagenes.append(f"\n![Imagen {img_id}](imagen_p{page_num + 1}_id{img_id}.png)\n")
                            texto_con_imagenes.append(f"*[IMAGEN {img_id} UBICADA AQUÍ EN EL DOCUMENTO ORIGINAL]*\n")
                
                texto_markdown += '\n'.join(texto_con_imagenes)
                texto_markdown += "\n\n---\n\n"
            
            # EXTRAER IMÁGENES de la página
            for img_index, img in enumerate(image_list):
                try:
                    # Obtener referencia de la imagen
                    xref = img[0]
                    
                    # Extraer imagen como Pixmap
                    pix = fitz.Pixmap(doc, xref)
                    
                    # Verificar que sea una imagen válida (RGB o GRAY)
                    if pix.n - pix.alpha < 4:
                        # Convertir a bytes PNG
                        img_data = pix.tobytes("png")
                        
                        # Codificar en base64
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        
                        # Obtener posición si está disponible
                        posicion_info = None
                        for pos_img in posiciones_imagenes:
                            if pos_img['img_index'] == img_index:
                                posicion_info = {
                                    'x': pos_img['rect'].x0,
                                    'y': pos_img['rect'].y0,
                                    'ancho': pos_img['rect'].width,
                                    'alto': pos_img['rect'].height
                                }
                                break
                        
                        # Agregar a la lista
                        lista_imagenes.append({
                            'id': len(lista_imagenes) + 1,
                            'pagina': page_num + 1,
                            'indice_en_pagina': img_index + 1,
                            'base64': img_base64,
                            'tamaño_bytes': len(img_data),
                            'dimensiones': {
                                'ancho': pix.width,
                                'alto': pix.height
                            },
                            'posicion_en_pagina': posicion_info
                        })
                    
                    # Liberar memoria del pixmap
                    pix = None
                    
                except Exception as img_error:
                    print(f"Error procesando imagen {img_index} en página {page_num + 1}: {img_error}")
                    continue
        
        return texto_completo, texto_markdown, lista_imagenes, total_pages
        
    except Exception as e:
        raise Exception(f"Error procesando PDF: {str(e)}")
    
    finally:
        # Asegurar que el documento se cierre siempre
        if doc:
            doc.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que la API está funcionando"""
    return jsonify({
        'status': 'healthy',
        'service': 'PDF Text and Image Extractor',
        'pymupdf_version': fitz.VersionBind,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/process-document', methods=['POST'])
def process_document():
    """
    Endpoint principal para procesar documentos PDF
    Extrae texto e imágenes y los devuelve en formato JSON
    """
    
    # Verificar que se envió un archivo
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No se proporcionó ningún archivo',
            'error_code': 'NO_FILE'
        }), 400
    
    file = request.files['file']
    
    # Verificar que el archivo tiene nombre
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'El archivo no tiene nombre',
            'error_code': 'EMPTY_FILENAME'
        }), 400
    
    # Verificar que es un PDF
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Solo se aceptan archivos PDF',
            'error_code': 'INVALID_FORMAT'
        }), 400
    
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Guardar archivo temporal
        file.save(temp_file_path)
        
        # Verificar que el archivo se guardó correctamente
        if not os.path.exists(temp_file_path):
            raise Exception("No se pudo guardar el archivo temporal")
        
        # Extraer texto e imágenes
        texto_extraido, texto_markdown, imagenes_extraidas, num_paginas = extract_text_and_images(temp_file_path)
        
        # Preparar respuesta exitosa
        response_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'file_info': {
                'filename': file.filename,
                'size_bytes': os.path.getsize(temp_file_path),
                'pages': num_paginas
            },
            'extracted_text': {
                'content': texto_extraido,
                'markdown': texto_markdown,
                'length_chars': len(texto_extraido),
                'has_text': len(texto_extraido.strip()) > 0
            },
            'extracted_images': {
                'count': len(imagenes_extraidas),
                'images': imagenes_extraidas
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        # Manejo de errores
        error_response = {
            'success': False,
            'error': str(e),
            'error_code': 'PROCESSING_ERROR',
            'timestamp': datetime.now().isoformat()
        }
        
        # Si está en modo debug, incluir traceback
        if app.debug:
            error_response['traceback'] = traceback.format_exc()
        
        return jsonify(error_response), 500
        
    finally:
        # Limpiar archivos temporales SIEMPRE
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as cleanup_error:
            print(f"Error limpiando archivos temporales: {cleanup_error}")

@app.errorhandler(413)
def file_too_large(e):
    """Manejo de archivos muy grandes"""
    return jsonify({
        'success': False,
        'error': 'El archivo es demasiado grande (máximo 50MB)',
        'error_code': 'FILE_TOO_LARGE'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Manejo de rutas no encontradas"""
    return jsonify({
        'success': False,
        'error': 'Endpoint no encontrado',
        'error_code': 'NOT_FOUND',
        'available_endpoints': ['/health', '/process-document']
    }), 404

if __name__ == '__main__':
    print("🚀 Iniciando API de extracción de texto e imágenes")
    print("📦 Verificando PyMuPDF...")
    
    try:
        print(f"✅ PyMuPDF versión: {fitz.VersionBind}")
    except Exception as e:
        print(f"❌ Error con PyMuPDF: {e}")
        exit(1)
    
    print("🌐 Endpoints disponibles:")
    print("   - GET  /health          (verificar estado)")
    print("   - POST /process-document (procesar PDF)")
    print("🔧 Tamaño máximo: 50MB")
    print("📍 Servidor: http://localhost:5000")
    print("-" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )