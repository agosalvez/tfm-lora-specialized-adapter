#!/usr/bin/env python3
"""
Script orquestador para procesar documentos PDF con docling y generar descripciones de imágenes.
Genera texto.md (original) y texto_final.md (con descripciones insertadas)
"""

import os
import sys
import subprocess
import requests
import re
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging primero
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_document.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env en el mismo directorio
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"✅ Archivo .env cargado desde: {env_path}")
    
    # Mostrar qué variables se encontraron
    api_url_from_env = os.getenv('API_URL')
    auth_token_from_env = os.getenv('AUTH_TOKEN')
    
    if api_url_from_env:
        logger.info(f"   - API_URL encontrada: {api_url_from_env}")
    if auth_token_from_env:
        logger.info(f"   - AUTH_TOKEN encontrada: {'***' + auth_token_from_env[-4:] if len(auth_token_from_env) > 4 else '***'}")
else:
    logger.warning(f"⚠️ Archivo .env no encontrado en: {env_path}")
    logger.info("ℹ️  Se usarán valores por defecto para configuración")

class DocumentProcessor:
    """Clase para procesar documentos PDF y generar descripciones de imágenes"""
    
    def __init__(self, api_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Inicializa el procesador de documentos
        
        Args:
            api_url (str): URL del endpoint de la API
            auth_token (str): Token de autenticación
        """
        # Usar variables de entorno si no se proporcionan valores
        self.api_url = api_url or os.getenv('API_URL', 'http://localhost:5000/analyze')
        self.auth_token = auth_token or os.getenv('AUTH_TOKEN', 'TOKEN_FROM_ENV_FILE')
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        # Generar timestamp para la carpeta artifacts
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.artifacts_dir = f"artifacts_{self.timestamp}"
        
        # Logging de configuración
        logger.info("🔧 Configuración del procesador:")
        logger.info(f"   - API URL: {self.api_url}")
        logger.info(f"   - Token: {'***' + self.auth_token[-4:] if len(self.auth_token) > 4 else '***'}")
        logger.info(f"📁 Directorio de salida: {self.artifacts_dir}")
        logger.info(f"⏰ Timestamp generado: {self.timestamp}")
    
    def ejecutar_docling(self, pdf_file: str) -> bool:
        """
        Ejecuta el script docling.py para procesar el PDF
        
        Args:
            pdf_file (str): Ruta al archivo PDF
            
        Returns:
            bool: True si la ejecución fue exitosa
        """
        try:
            logger.info(f"🔄 Ejecutando docling.py con archivo: {pdf_file}")
            logger.info(f"📁 Directorio de salida: {self.artifacts_dir}")
            
            # Ejecutar el script docling.py con directorio personalizado
            result = subprocess.run(
                [sys.executable, "docling.py", pdf_file, self.artifacts_dir],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("✅ docling.py ejecutado exitosamente")
            logger.debug(f"Salida: {result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error al ejecutar docling.py: {e}")
            logger.error(f"Salida de error: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("❌ No se encontró el archivo docling.py")
            return False
    
    def obtener_imagenes(self) -> List[str]:
        """
        Obtiene la lista de imágenes en artifacts_TIMESTAMP/imagenes_extraidas ordenadas
        
        Returns:
            List[str]: Lista de rutas de imágenes ordenadas
        """
        try:
            imagenes_dir = os.path.join(self.artifacts_dir, "imagenes_extraidas")
            
            if not os.path.exists(imagenes_dir):
                logger.error(f"❌ No se encontró el directorio {imagenes_dir}")
                return []
            
            # Buscar archivos de imagen PNG ordenados
            imagen_files = []
            for file in os.listdir(imagenes_dir):
                if file.startswith("image") and file.endswith(".png"):
                    imagen_files.append(file)
            
            # Ordenar por número
            imagen_files.sort(key=lambda x: int(x.replace("image", "").replace(".png", "")))
            
            # Convertir a rutas completas
            imagen_paths = [os.path.join(imagenes_dir, img) for img in imagen_files]
            
            logger.info(f"📁 Encontradas {len(imagen_paths)} imágenes: {imagen_files}")
            return imagen_paths
            
        except Exception as e:
            logger.error(f"❌ Error al obtener imágenes: {e}")
            return []
    
    def procesar_imagen(self, imagen_path: str, prompt: str = "Las imágenes se basan en una situación de una actuación de magia e ilusionismo. Quiero que describas lo que ves, haciendo hincapié en flechas, hacia dónde se dirigen, qué hacen o qué intención quiere aportar la imagen.") -> Optional[str]:
        """
        Procesa una imagen enviándola al endpoint de la API
        
        Args:
            imagen_path (str): Ruta a la imagen
            prompt (str): Texto del prompt
            
        Returns:
            Optional[str]: Descripción generada o None si hay error
        """
        try:
            logger.info(f"🔄 Procesando imagen: {imagen_path}")
            
            # Verificar que la imagen existe
            if not os.path.exists(imagen_path):
                logger.error(f"❌ La imagen no existe: {imagen_path}")
                return None
            
            # Determinar el tipo MIME basado en la extensión
            imagen_ext = os.path.splitext(imagen_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(imagen_ext, 'image/png')
            
            logger.info(f"📋 Tipo MIME detectado: {mime_type}")
            logger.info(f"🔗 URL de la API: {self.api_url}")
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            
            # Leer el archivo en memoria para evitar problemas de scope
            with open(imagen_path, 'rb') as image_file:
                image_data = image_file.read()
            
            logger.info(f"📊 Tamaño de imagen: {len(image_data)} bytes")
            
            # Preparar los datos del formulario
            files = {
                'image': (os.path.basename(imagen_path), image_data, mime_type)
            }
            data = {
                'text': prompt
            }
            
            # Headers específicos para la request (sin Content-Type para multipart)
            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }
            
            logger.info("📤 Enviando petición al servidor...")
            
            # Realizar la llamada POST
            response = requests.post(
                self.api_url,
                files=files,
                data=data,
                headers=headers,
                timeout=60  # Aumentado a 60 segundos
            )
            
            logger.info(f"📥 Respuesta recibida - Código: {response.status_code}")
            logger.info(f"📏 Tamaño de respuesta: {len(response.text)} caracteres")
            
            # Verificar el código de respuesta
            response.raise_for_status()
            
            # Extraer la descripción de la respuesta
            descripcion = response.text.strip()
            
            if not descripcion:
                logger.warning(f"⚠️ La respuesta está vacía para {imagen_path}")
                return None
            
            logger.info(f"✅ Descripción generada para {imagen_path}")
            logger.debug(f"📝 Descripción: {descripcion[:200]}...")
            
            return descripcion
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout al procesar {imagen_path} - La API tardó más de 60 segundos")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Error de conexión al procesar {imagen_path} - Verifica que la API esté ejecutándose")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"🚫 Error HTTP {response.status_code} para {imagen_path}: {e}")
            if response.status_code == 401:
                logger.error("🔑 Error de autorización - Verifica el token en el archivo .env")
            elif response.status_code == 404:
                logger.error("🔍 Endpoint no encontrado - Verifica la URL de la API")
            elif response.status_code == 500:
                logger.error("💥 Error del servidor - Problema en la API")
            try:
                logger.error(f"📄 Respuesta del servidor: {response.text}")
            except:
                pass
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en la llamada HTTP para {imagen_path}: {e}")
            return None
        except FileNotFoundError:
            logger.error(f"📄 Archivo de imagen no encontrado: {imagen_path}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado al procesar {imagen_path}: {e}")
            logger.error(f"🔍 Tipo de error: {type(e).__name__}")
            return None
    
    def extraer_descripcion_de_json(self, respuesta: str) -> str:
        """
        Extrae el campo 'response' de un JSON o devuelve el texto tal como está
        
        Args:
            respuesta (str): Respuesta de la API (puede ser JSON o texto plano)
            
        Returns:
            str: Descripción extraída del JSON o texto original
        """
        try:
            import json
            
            # Intentar parsear como JSON
            datos = json.loads(respuesta)
            
            # Si es un diccionario, buscar el campo 'response'
            if isinstance(datos, dict):
                if 'response' in datos:
                    descripcion = datos['response']
                    logger.info(f"✅ Campo 'response' extraído del JSON: {descripcion[:100]}...")
                    return descripcion
                else:
                    # Si no hay campo 'response', usar el primer campo string que encontremos
                    for key, value in datos.items():
                        if isinstance(value, str) and value.strip():
                            logger.info(f"✅ Campo '{key}' extraído del JSON: {value[:100]}...")
                            return value
                    
                    # Si no encontramos campos string, devolver el JSON como string
                    logger.warning(f"⚠️ No se encontró campo 'response' en JSON, devolviendo JSON completo")
                    return str(datos)
            else:
                # Si el JSON es una lista u otro tipo, devolver como está
                logger.warning(f"⚠️ JSON no es un diccionario, devolviendo como está")
                return str(datos)
                
        except json.JSONDecodeError:
            # No es JSON válido, devolver el texto tal como está
            logger.debug(f"📄 No es JSON válido, devolviendo texto plano: {respuesta[:100]}...")
            return respuesta
        except Exception as e:
            logger.error(f"❌ Error al procesar JSON: {e}")
            return respuesta
    
    def guardar_descripcion(self, imagen_path: str, descripcion: str) -> bool:
        """
        Guarda la descripción en un archivo .md, procesando JSON si es necesario
        
        Args:
            imagen_path (str): Ruta de la imagen procesada
            descripcion (str): Descripción generada (puede ser JSON o texto plano)
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Crear directorio de descripciones si no existe
            descriptions_dir = os.path.join(self.artifacts_dir, "image_descriptions")
            Path(descriptions_dir).mkdir(parents=True, exist_ok=True)
            
            # Obtener nombre del archivo de imagen sin extensión
            imagen_name = Path(imagen_path).stem  # image1, image2, etc.
            output_file = os.path.join(descriptions_dir, f"{imagen_name}.md")
            
            # Extraer la descripción del JSON si es necesario
            descripcion_final = self.extraer_descripcion_de_json(descripcion)
            
            # Guardar descripción con codificación UTF-8 explícita
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                f.write(f"# Descripción de {imagen_name}\n\n")
                f.write(f"**Imagen:** {imagen_path}\n\n")
                f.write(f"**Descripción:**\n\n{descripcion_final}\n")
            
            logger.info(f"💾 Descripción guardada en: {output_file}")
            logger.debug(f"📝 Contenido guardado: {descripcion_final[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al guardar descripción para {imagen_path}: {e}")
            return False
    
    def leer_descripcion(self, imagen_name: str) -> Optional[str]:
        """
        Lee la descripción de una imagen desde el archivo .md correspondiente
        
        Args:
            imagen_name (str): Nombre de la imagen (ej: image1)
            
        Returns:
            Optional[str]: Descripción de la imagen o None si no se encuentra
        """
        try:
            descripcion_file = os.path.join(self.artifacts_dir, "image_descriptions", f"{imagen_name}.md")
            
            if not os.path.exists(descripcion_file):
                logger.warning(f"⚠️ No se encontró archivo de descripción: {descripcion_file}")
                return None
                
            # Leer archivo con codificación UTF-8 explícita
            with open(descripcion_file, 'r', encoding='utf-8', errors='replace') as f:
                contenido = f.read()
                
            # Extraer solo la descripción (después de "**Descripción:**")
            if "**Descripción:**" in contenido:
                descripcion = contenido.split("**Descripción:**")[1].strip()
                
                # Limpiar posibles caracteres de control o espacios extra
                descripcion = ' '.join(descripcion.split())
                
                # NUEVA MEJORA: Aplicar extracción de JSON también al leer archivos existentes
                descripcion = self.extraer_descripcion_de_json(descripcion)
                
                # Verificar que la descripción no esté vacía
                if descripcion:
                    logger.debug(f"📄 Descripción leída para {imagen_name}: {descripcion[:100]}...")
                    return descripcion
                else:
                    logger.warning(f"⚠️ Descripción vacía para {imagen_name}")
                    return None
            else:
                logger.warning(f"⚠️ Formato no reconocido en {descripcion_file}")
                # Intentar devolver solo el contenido principal
                lineas = contenido.split('\n')
                contenido_limpio = []
                for linea in lineas:
                    if linea.strip() and not linea.startswith('#') and not linea.startswith('**'):
                        contenido_limpio.append(linea.strip())
                
                if contenido_limpio:
                    # NUEVA MEJORA: Aplicar extracción de JSON también aquí
                    contenido_final = ' '.join(contenido_limpio)
                    return self.extraer_descripcion_de_json(contenido_final)
                else:
                    # NUEVA MEJORA: Aplicar extracción de JSON también aquí
                    return self.extraer_descripcion_de_json(contenido.strip())
                
        except UnicodeDecodeError as e:
            logger.error(f"❌ Error de codificación al leer descripción de {imagen_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error al leer descripción de {imagen_name}: {e}")
            return None
    
    def insertar_descripciones_en_texto(self) -> bool:
        """
        Crea texto_final.md reemplazando completamente los enlaces de imágenes
        por el valor del campo 'response' de sus descripciones
        
        Returns:
            bool: True si se creó texto_final.md correctamente
        """
        try:
            texto_file = os.path.join(self.artifacts_dir, "texto.md")
            texto_final_file = os.path.join(self.artifacts_dir, "texto_final.md")
            
            if not os.path.exists(texto_file):
                logger.error(f"❌ No se encontró el archivo {texto_file}")
                return False
            
            logger.info("🔄 Creando texto_final.md reemplazando enlaces por descripciones...")
            
            # Leer el archivo original con codificación UTF-8 explícita
            with open(texto_file, 'r', encoding='utf-8', errors='replace') as f:
                contenido = f.read()
            
            # Patrones para encontrar enlaces a imágenes
            patrones_imagen = [
                r'!\[.*?\]\(.*?image(\d+)\.png.*?\)',  # ![alt](path/image1.png)
                r'\[.*?\]\(.*?image(\d+)\.png.*?\)',   # [alt](path/image1.png)
                r'<img.*?src=".*?image(\d+)\.png.*?".*?>',  # <img src="path/image1.png">
                r'image(\d+)\.png',  # image1.png simple
            ]
            
            contenido_modificado = contenido
            descripciones_insertadas = 0
            
            # Procesar cada patrón de imagen
            for patron in patrones_imagen:
                matches = list(re.finditer(patron, contenido_modificado))
                
                # Procesar matches de atrás hacia adelante para evitar problemas de índices
                for match in reversed(matches):
                    numero_imagen = match.group(1)
                    imagen_name = f"image{numero_imagen}"
                    
                    # Leer la descripción correspondiente
                    descripcion = self.leer_descripcion(imagen_name)
                    
                    if descripcion:
                        # Reemplazar completamente el enlace por la descripción
                        enlace_original = match.group(0)
                        
                        # Reemplazar el enlace por solo la descripción
                        contenido_modificado = (
                            contenido_modificado[:match.start()] +
                            descripcion +
                            contenido_modificado[match.end():]
                        )
                        
                        descripciones_insertadas += 1
                        logger.info(f"✅ Enlace reemplazado por descripción para {imagen_name}")
                        logger.debug(f"🔄 {enlace_original} → {descripcion[:50]}...")
                    else:
                        logger.warning(f"⚠️ No se pudo obtener descripción para {imagen_name}")
            
            # Guardar el archivo final con codificación UTF-8 explícita
            with open(texto_final_file, 'w', encoding='utf-8', newline='') as f:
                f.write(contenido_modificado)
            
            logger.info(f"✅ Archivo texto_final.md creado con {descripciones_insertadas} enlaces reemplazados")
            logger.info(f"📄 Archivo original preservado: {texto_file}")
            logger.info(f"📄 Archivo final creado: {texto_final_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al crear texto_final.md: {e}")
            return False

    def procesar_documento(self, pdf_file: str) -> bool:
        """
        Procesa un documento PDF completo: extrae texto/imágenes y genera descripciones
        
        Args:
            pdf_file (str): Ruta al archivo PDF
            
        Returns:
            bool: True si todo el proceso fue exitoso
        """
        logger.info("=" * 60)
        logger.info("🚀 Iniciando procesamiento completo del documento")
        logger.info(f"📄 Archivo PDF: {pdf_file}")
        logger.info(f"📁 Directorio de salida: {self.artifacts_dir}")
        logger.info("=" * 60)
        
        # Paso 1: Ejecutar docling.py
        if not self.ejecutar_docling(pdf_file):
            logger.error("❌ Falló la ejecución de docling.py")
            return False
        
        # Paso 1.5: Corregir enlaces de imágenes en texto.md
        if self.corregir_enlaces_imagenes():
            logger.info("✅ Enlaces de imágenes corregidos en texto.md")
        else:
            logger.warning("⚠️ No se pudieron corregir algunos enlaces de imágenes")
        
        # Paso 2: Obtener lista de imágenes
        imagen_paths = self.obtener_imagenes()
        if not imagen_paths:
            logger.error("❌ No se encontraron imágenes para procesar")
            return False
        
        # Paso 3: Procesar cada imagen
        logger.info(f"🔄 Procesando {len(imagen_paths)} imágenes...")
        
        exitosos = 0
        for imagen_path in imagen_paths:
            descripcion = self.procesar_imagen(imagen_path)
            if descripcion:
                if self.guardar_descripcion(imagen_path, descripcion):
                    exitosos += 1
                else:
                    logger.warning(f"⚠️ No se pudo guardar descripción para {imagen_path}")
            else:
                logger.warning(f"⚠️ No se pudo procesar {imagen_path}")
        
        logger.info(f"✅ Procesamiento completado: {exitosos}/{len(imagen_paths)} imágenes procesadas")
        
        # Paso 4: Crear texto_final.md con descripciones insertadas
        if exitosos > 0:
            if self.insertar_descripciones_en_texto():
                logger.info("✅ Archivo texto_final.md creado con descripciones insertadas")
            else:
                logger.warning("⚠️ No se pudo crear texto_final.md con las descripciones")
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("🎉 PROCESAMIENTO COMPLETADO")
        logger.info(f"📁 Directorio generado: {self.artifacts_dir}")
        logger.info(f"⏰ Timestamp: {self.timestamp}")
        logger.info("=" * 60)
        
        return exitosos > 0

    def verificar_configuracion(self) -> bool:
        """
        Verifica que la configuración esté correctamente establecida
        
        Returns:
            bool: True si la configuración es válida
        """
        logger.info("🔍 Verificando configuración...")
        
        # Verificar API URL
        if not self.api_url or self.api_url == 'http://localhost:5000/analyze':
            logger.warning("⚠️ Usando URL por defecto. Considera configurar API_URL en .env")
        else:
            logger.info(f"✅ API URL configurada: {self.api_url}")
        
        # Verificar token
        if not self.auth_token or self.auth_token == 'TOKEN_FROM_ENV_FILE':
            logger.warning("⚠️ Token no configurado. Configura AUTH_TOKEN en .env")
            return False
        else:
            logger.info(f"✅ Token configurado: {'***' + self.auth_token[-4:] if len(self.auth_token) > 4 else '***'}")
        
        # Verificar archivo .env
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            logger.info(f"✅ Archivo .env encontrado: {env_path}")
        else:
            logger.warning(f"⚠️ Archivo .env no encontrado: {env_path}")
        
        # Probar conexión con la API si la configuración es válida
        if self.auth_token and self.auth_token != 'TOKEN_FROM_ENV_FILE':
            logger.info("🔌 Probando conexión con la API...")
            if self.probar_conexion_api():
                logger.info("✅ Conexión con la API exitosa")
            else:
                logger.error("❌ Fallo en la conexión con la API")
                return False
        else:
            logger.warning("⚠️ Omitiendo prueba de API por token inválido")
        
        return True

    def probar_conexion_api(self) -> bool:
        """
        Prueba la conexión básica con la API sin enviar imagen
        
        Returns:
            bool: True si la API responde correctamente
        """
        try:
            logger.info("🔌 Probando conexión con la API...")
            
            # Crear una imagen de prueba pequeña (1x1 pixel PNG)
            import base64
            # PNG de 1x1 pixel transparente
            png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
            
            files = {
                'image': ('test.png', png_data, 'image/png')
            }
            data = {
                'text': 'Test de conexión'
            }
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }
            
            response = requests.post(
                self.api_url,
                files=files,
                data=data,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"📥 Respuesta de prueba - Código: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ API responde correctamente")
                return True
            else:
                logger.warning(f"⚠️ API respondió con código: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Error de conexión - La API no está disponible")
            return False
        except requests.exceptions.Timeout:
            logger.error("⏰ Timeout en la prueba de conexión")
            return False
        except Exception as e:
            logger.error(f"❌ Error en prueba de conexión: {e}")
            return False

    def solo_insertar_descripciones(self) -> bool:
        """
        Función para crear solo texto_final.md con las descripciones insertadas
        (útil si ya se procesaron las imágenes anteriormente)
        
        Returns:
            bool: True si se creó texto_final.md correctamente
        """
        logger.info("🔄 Creando texto_final.md con descripciones insertadas...")
        
        # Primero corregir enlaces de imágenes en texto.md
        if self.corregir_enlaces_imagenes():
            logger.info("✅ Enlaces de imágenes corregidos en texto.md")
        else:
            logger.warning("⚠️ No se pudieron corregir algunos enlaces de imágenes")
        
        # Luego insertar descripciones
        if self.insertar_descripciones_en_texto():
            logger.info("✅ Archivo texto_final.md creado correctamente")
            return True
        else:
            logger.error("❌ Error al crear texto_final.md")
            return False

    def corregir_enlaces_imagenes(self) -> bool:
        """
        Corrige los enlaces de imágenes en texto.md para que apunten a las rutas reales
        
        Returns:
            bool: True si se corrigieron los enlaces correctamente
        """
        try:
            texto_file = os.path.join(self.artifacts_dir, "texto.md")
            
            if not os.path.exists(texto_file):
                logger.error(f"❌ No se encontró el archivo {texto_file}")
                return False
            
            logger.info("🔄 Corrigiendo enlaces de imágenes en texto.md...")
            
            # Leer el archivo original con codificación UTF-8 explícita
            with open(texto_file, 'r', encoding='utf-8', errors='replace') as f:
                contenido = f.read()
            
            # Obtener lista de imágenes reales en imagenes_extraidas
            imagenes_dir = os.path.join(self.artifacts_dir, "imagenes_extraidas")
            imagenes_reales = []
            
            if os.path.exists(imagenes_dir):
                for file in os.listdir(imagenes_dir):
                    if file.startswith("image") and file.endswith(".png"):
                        imagenes_reales.append(file)
                imagenes_reales.sort(key=lambda x: int(x.replace("image", "").replace(".png", "")))
            
            logger.info(f"🖼️ Imágenes encontradas: {imagenes_reales}")
            
            # Patrones para encontrar enlaces de imágenes generados por docling
            import re
            
            # Buscar patrones como ![figura](ruta_generica) y reemplazar con rutas reales
            patrones_a_reemplazar = [
                # Patrón típico de docling: ![algo](ruta_temporal_o_generica)
                r'!\[([^\]]*)\]\([^)]*\.(png|jpg|jpeg|gif|bmp|webp)\)',
                # Patrón de imagen referenciada
                r'\[([^\]]*)\]\([^)]*\.(png|jpg|jpeg|gif|bmp|webp)\)',
                # Imagen HTML
                r'<img[^>]*src="([^"]*\.(png|jpg|jpeg|gif|bmp|webp))"[^>]*>'
            ]
            
            contenido_modificado = contenido
            imagen_counter = 0
            enlaces_corregidos = 0
            
            for patron in patrones_a_reemplazar:
                matches = re.finditer(patron, contenido_modificado, re.IGNORECASE)
                for match in matches:
                    if imagen_counter < len(imagenes_reales):
                        imagen_real = imagenes_reales[imagen_counter]
                        ruta_imagen_real = f"imagenes_extraidas/{imagen_real}"
                        
                        # Reconstruir el enlace con la ruta correcta
                        if patron.startswith('!\\['):  # Markdown image
                            alt_text = match.group(1) if match.group(1) else f"Imagen {imagen_counter + 1}"
                            nuevo_enlace = f"![{alt_text}]({ruta_imagen_real})"
                        elif patron.startswith('\\['):  # Markdown link
                            link_text = match.group(1) if match.group(1) else f"Imagen {imagen_counter + 1}"
                            nuevo_enlace = f"[{link_text}]({ruta_imagen_real})"
                        else:  # HTML img
                            nuevo_enlace = f'<img src="{ruta_imagen_real}" alt="Imagen {imagen_counter + 1}">'
                        
                        # Reemplazar el enlace original con el nuevo
                        contenido_modificado = contenido_modificado.replace(match.group(0), nuevo_enlace, 1)
                        
                        enlaces_corregidos += 1
                        imagen_counter += 1
            
            # Si no se encontraron patrones específicos, buscar cualquier mención de imagen
            if enlaces_corregidos == 0:
                logger.info("🔍 No se encontraron patrones estándar, buscando menciones genéricas...")
                
                # Buscar líneas que mencionen imágenes y agregar enlaces
                lineas = contenido_modificado.split('\n')
                nuevas_lineas = []
                
                for linea in lineas:
                    nuevas_lineas.append(linea)
                    
                    # Si la línea menciona "figura", "imagen", "gráfico", etc.
                    if any(palabra in linea.lower() for palabra in ['figura', 'imagen', 'gráfico', 'diagrama', 'ilustración']):
                        # Buscar si ya tiene un enlace
                        if not re.search(r'!\[.*?\]\(.*?\)', linea) and not re.search(r'<img.*?>', linea):
                            if imagen_counter < len(imagenes_reales):
                                imagen_real = imagenes_reales[imagen_counter]
                                ruta_imagen_real = f"imagenes_extraidas/{imagen_real}"
                                nuevo_enlace = f"\n![Imagen {imagen_counter + 1}]({ruta_imagen_real})\n"
                                nuevas_lineas.append(nuevo_enlace)
                                enlaces_corregidos += 1
                                imagen_counter += 1
                                logger.info(f"➕ Enlace agregado después de: {linea.strip()}")
                
                contenido_modificado = '\n'.join(nuevas_lineas)
            
            # Guardar el archivo modificado con codificación UTF-8 explícita
            with open(texto_file, 'w', encoding='utf-8', newline='') as f:
                f.write(contenido_modificado)
            
            logger.info(f"✅ Enlaces de imágenes corregidos: {enlaces_corregidos}")
            logger.info(f"📄 Archivo texto.md actualizado: {texto_file}")
            
            return enlaces_corregidos > 0
            
        except Exception as e:
            logger.error(f"❌ Error al corregir enlaces de imágenes: {e}")
            return False

    def insertar_descripciones_desde_carpeta(self, artifacts_dir: str) -> bool:
        """
        Función para crear texto_final.md usando una carpeta artifacts específica
        
        Args:
            artifacts_dir (str): Directorio artifacts a usar
            
        Returns:
            bool: True si se creó texto_final.md correctamente
        """
        # Verificar que la carpeta existe
        if not os.path.exists(artifacts_dir):
            logger.error(f"❌ La carpeta artifacts no existe: {artifacts_dir}")
            return False
        
        # Verificar que tiene la estructura correcta
        texto_file = os.path.join(artifacts_dir, "texto.md")
        if not os.path.exists(texto_file):
            logger.error(f"❌ No se encontró texto.md en: {artifacts_dir}")
            return False
            
        descriptions_dir = os.path.join(artifacts_dir, "image_descriptions")
        if not os.path.exists(descriptions_dir):
            logger.error(f"❌ No se encontró carpeta image_descriptions en: {artifacts_dir}")
            return False
        
        # Usar temporalmente esta carpeta artifacts
        artifacts_dir_original = self.artifacts_dir
        self.artifacts_dir = artifacts_dir
        
        logger.info(f"🔄 Usando carpeta artifacts: {artifacts_dir}")
        logger.info("🔄 Creando texto_final.md con descripciones insertadas...")
        
        try:
            # Primero corregir enlaces de imágenes en texto.md
            if self.corregir_enlaces_imagenes():
                logger.info("✅ Enlaces de imágenes corregidos en texto.md")
            else:
                logger.warning("⚠️ No se pudieron corregir algunos enlaces de imágenes")
            
            # Luego insertar descripciones
            if self.insertar_descripciones_en_texto():
                logger.info("✅ Archivo texto_final.md creado correctamente")
                return True
            else:
                logger.error("❌ Error al crear texto_final.md")
                return False
        finally:
            # Restaurar artifacts_dir original
            self.artifacts_dir = artifacts_dir_original

def main():
    """Función principal"""
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar el archivo PDF como parámetro")
        print("Uso: python process_document.py <archivo_pdf>")
        print("   o: python process_document.py --insert-descriptions")
        print("   o: python process_document.py --insert-descriptions-from <carpeta_artifacts>")
        print("   o: python process_document.py --check-config")
        print("   o: python process_document.py --test-image <ruta_imagen>")
        print("Ejemplo: python process_document.py documento.pdf")
        print("         python process_document.py --insert-descriptions")
        print("         python process_document.py --insert-descriptions-from artifacts_20240315_143022")
        print("         python process_document.py --check-config")
        print("         python process_document.py --test-image ./artifacts_*/imagenes_extraidas/image1.png")
        print("")
        print("Archivos generados:")
        print("  - artifacts_TIMESTAMP/texto.md (texto original)")
        print("  - artifacts_TIMESTAMP/texto_final.md (texto con descripciones insertadas)")
        sys.exit(1)
    
    # Crear procesador
    processor = DocumentProcessor()
    
    # Verificar qué modo se está ejecutando
    if sys.argv[1] == "--check-config":
        # Modo verificación de configuración
        success = processor.verificar_configuracion()
        
        if success:
            print("\n🎉 ¡Configuración válida!")
            print("✅ El sistema está listo para procesar documentos")
        else:
            print("\n⚠️ Configuración incompleta")
            print("💡 Revisa el archivo .env y configura AUTH_TOKEN")
            sys.exit(1)
    elif sys.argv[1] == "--test-image":
        # Modo prueba de imagen específica
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar la ruta de la imagen")
            print("Uso: python process_document.py --test-image <ruta_imagen>")
            sys.exit(1)
        
        imagen_path = sys.argv[2]
        if not os.path.exists(imagen_path):
            print(f"❌ Error: La imagen no existe: {imagen_path}")
            sys.exit(1)
        
        print(f"🔄 Probando procesamiento de imagen: {imagen_path}")
        descripcion = processor.procesar_imagen(imagen_path)
        
        if descripcion:
            print("\n🎉 ¡Imagen procesada exitosamente!")
            print(f"📝 Descripción generada:")
            print("-" * 50)
            print(descripcion)
            print("-" * 50)
        else:
            print("\n💥 Error al procesar la imagen")
            print("💡 Revisa los logs para más detalles")
            sys.exit(1)
    elif sys.argv[1] == "--insert-descriptions":
        # Modo solo insertar descripciones
        success = processor.solo_insertar_descripciones()
        
        if success:
            print("\n🎉 ¡Archivo texto_final.md creado exitosamente!")
            print(f"📁 Directorio utilizado: {processor.artifacts_dir}")
            print("📁 Archivos disponibles:")
            print(f"   - {processor.artifacts_dir}/texto.md (texto original extraído)")
            print(f"   - {processor.artifacts_dir}/texto_final.md (texto con descripciones insertadas)")
        else:
            print("\n💥 Error al crear texto_final.md")
            sys.exit(1)
    elif sys.argv[1] == "--insert-descriptions-from":
        # Modo insertar descripciones desde carpeta específica
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar la carpeta artifacts")
            print("Uso: python process_document.py --insert-descriptions-from <carpeta_artifacts>")
            print("Ejemplo: python process_document.py --insert-descriptions-from artifacts_20240315_143022")
            sys.exit(1)
        
        artifacts_dir = sys.argv[2]
        success = processor.insertar_descripciones_desde_carpeta(artifacts_dir)
        
        if success:
            print("\n🎉 ¡Archivo texto_final.md creado exitosamente!")
            print(f"📁 Directorio utilizado: {artifacts_dir}")
            print("📁 Archivos disponibles:")
            print(f"   - {artifacts_dir}/texto.md (texto original con enlaces corregidos)")
            print(f"   - {artifacts_dir}/texto_final.md (texto con descripciones insertadas)")
            print(f"   - {artifacts_dir}/imagenes_extraidas/ (imágenes)")
            print(f"   - {artifacts_dir}/image_descriptions/ (descripciones)")
        else:
            print("\n💥 Error al crear texto_final.md")
            sys.exit(1)
    else:
        # Modo normal: procesamiento completo
        pdf_file = sys.argv[1]
        
        # Verificar que el archivo PDF existe
        if not os.path.exists(pdf_file):
            print(f"❌ Error: El archivo {pdf_file} no existe")
            sys.exit(1)
        
        # Ejecutar procesamiento completo
        success = processor.procesar_documento(pdf_file)
        
        if success:
            print("\n🎉 ¡Procesamiento completado exitosamente!")
            print(f"📁 Directorio generado: {processor.artifacts_dir}")
            print("📁 Archivos generados:")
            print(f"   - {processor.artifacts_dir}/texto.md (texto original extraído)")
            print(f"   - {processor.artifacts_dir}/texto_final.md (texto con descripciones insertadas)")
            print(f"   - {processor.artifacts_dir}/imagenes_extraidas/ (imágenes)")
            print(f"   - {processor.artifacts_dir}/image_descriptions/ (descripciones)")
        else:
            print("\n💥 Error en el procesamiento")
            sys.exit(1)

if __name__ == "__main__":
    main() 