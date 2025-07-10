#!/usr/bin/env python3
"""
Script orquestador para procesar documentos PDF con docling y generar descripciones de imágenes
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from typing import List, Optional
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_document.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Clase para procesar documentos PDF y generar descripciones de imágenes"""
    
    def __init__(self, api_url: str = None, auth_token: str = None):
        """
        Inicializa el procesador de documentos
        
        Args:
            api_url (str): URL del endpoint de la API
            auth_token (str): Token de autenticación
        """
        # Usar variables de entorno si no se proporcionan valores
        self.api_url = api_url or os.getenv('API_URL', 'http://localhost:5000/analyze')
        self.auth_token = auth_token or os.getenv('AUTH_TOKEN', '123')
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
    
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
            
            # Ejecutar el script docling.py
            result = subprocess.run(
                [sys.executable, "docling.py", pdf_file],
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
        Obtiene la lista de imágenes en artifacts/imagenes_extraidas ordenadas
        
        Returns:
            List[str]: Lista de rutas de imágenes ordenadas
        """
        try:
            if not os.path.exists("artifacts/imagenes_extraidas"):
                logger.error("❌ No se encontró el directorio artifacts/imagenes_extraidas")
                return []
            
            # Buscar archivos de imagen PNG ordenados
            imagen_files = []
            for file in os.listdir("artifacts/imagenes_extraidas"):
                if file.startswith("image") and file.endswith(".png"):
                    imagen_files.append(file)
            
            # Ordenar por número
            imagen_files.sort(key=lambda x: int(x.replace("image", "").replace(".png", "")))
            
            # Convertir a rutas completas
            imagen_paths = [os.path.join("artifacts/imagenes_extraidas", img) for img in imagen_files]
            
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
            
            # Preparar los datos del formulario
            with open(imagen_path, 'rb') as image_file:
                files = {
                    'image': (os.path.basename(imagen_path), image_file, 'image/png')
                }
                data = {
                    'text': prompt
                }
                
                # Realizar la llamada POST
                response = requests.post(
                    self.api_url,
                    files=files,
                    data=data,
                    headers=self.headers,
                    timeout=30
                )
                
                response.raise_for_status()
                
                # Extraer la descripción de la respuesta
                descripcion = response.text
                logger.info(f"✅ Descripción generada para {imagen_path}")
                
                return descripcion
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en la llamada HTTP para {imagen_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error al procesar {imagen_path}: {e}")
            return None
    
    def guardar_descripcion(self, imagen_path: str, descripcion: str) -> bool:
        """
        Guarda la descripción en un archivo .md
        
        Args:
            imagen_path (str): Ruta de la imagen procesada
            descripcion (str): Descripción generada
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Crear directorio de descripciones si no existe
            Path("artifacts/image_descriptions").mkdir(parents=True, exist_ok=True)
            
            # Obtener nombre del archivo de imagen sin extensión
            imagen_name = Path(imagen_path).stem  # image1, image2, etc.
            output_file = f"artifacts/image_descriptions/{imagen_name}.md"
            
            # Guardar descripción
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Descripción de {imagen_name}\n\n")
                f.write(f"**Imagen:** {imagen_path}\n\n")
                f.write(f"**Descripción:**\n\n{descripcion}\n")
            
            logger.info(f"💾 Descripción guardada en: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al guardar descripción para {imagen_path}: {e}")
            return False
    
    def procesar_documento(self, pdf_file: str) -> bool:
        """
        Procesa un documento PDF completo: extrae texto/imágenes y genera descripciones
        
        Args:
            pdf_file (str): Ruta al archivo PDF
            
        Returns:
            bool: True si todo el proceso fue exitoso
        """
        logger.info("🚀 Iniciando procesamiento completo del documento")
        logger.info(f"📄 Archivo PDF: {pdf_file}")
        
        # Paso 1: Ejecutar docling.py
        if not self.ejecutar_docling(pdf_file):
            logger.error("❌ Falló la ejecución de docling.py")
            return False
        
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
        
        return exitosos > 0

def main():
    """Función principal"""
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar el archivo PDF como parámetro")
        print("Uso: python process_document.py <archivo_pdf>")
        print("Ejemplo: python process_document.py documento.pdf")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    # Verificar que el archivo PDF existe
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        sys.exit(1)
    
    # Crear procesador y ejecutar
    processor = DocumentProcessor()
    success = processor.procesar_documento(pdf_file)
    
    if success:
        print("\n🎉 ¡Procesamiento completado exitosamente!")
        print("📁 Archivos generados:")
        print("   - artifacts/texto.md (texto extraído)")
        print("   - artifacts/imagenes_extraidas/ (imágenes)")
        print("   - artifacts/image_descriptions/ (descripciones)")
    else:
        print("\n💥 Error en el procesamiento")
        sys.exit(1)

if __name__ == "__main__":
    main() 