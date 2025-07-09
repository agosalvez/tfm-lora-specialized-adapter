#!/usr/bin/env python3
"""
Script para procesar PDFs con docling y extraer texto e imágenes
Siempre convierte de PDF a MD con imágenes PNG
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def procesar_pdf(pdf_file, output_dir="target"):
    """
    Procesa un PDF usando docling y extrae texto e imágenes
    Siempre convierte de PDF a MD con imágenes PNG
    
    Args:
        pdf_file (str): Ruta al archivo PDF (obligatorio)
        output_dir (str): Directorio de salida
    """
    
    # Verificar que el archivo PDF existe
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        return False
    
    # Crear directorio de salida si no existe
    Path(output_dir).mkdir(exist_ok=True)
    
    # Comando docling con valores fijos: from pdf, to md, imágenes PNG
    cmd = [
        "docling",
        pdf_file,
        "--from", "pdf",
        "--to", "md",
        "--image-export-mode", "referenced",
        "--output", f"./{output_dir}"
    ]
    
    print(f"🔄 Ejecutando: {' '.join(cmd)}")
    
    try:
        # Ejecutar el comando
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print("✅ Procesamiento completado exitosamente")
        print(f"📁 Contenido guardado en: {output_dir}")
        
        # Mostrar archivos generados
        if os.path.exists(output_dir):
            archivos = os.listdir(output_dir)
            print(f"📄 Archivos generados: {len(archivos)}")
            for archivo in archivos:
                print(f"   - {archivo}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar docling: {e}")
        print(f"Salida de error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Error: No se encontró el comando 'docling'")
        print("Asegúrate de que docling esté instalado y disponible en el PATH")
        return False

def main():
    """Función principal"""
    
    # Verificar que se proporcione el archivo PDF como parámetro obligatorio
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar el archivo PDF como parámetro")
        print("Uso: python docling.py <archivo_pdf> [directorio_salida]")
        print("Ejemplo: python docling.py documento.pdf")
        print("")
        print("El script siempre convierte:")
        print("  - FROM: PDF")
        print("  - TO: MD (Markdown)")
        print("  - Imágenes: PNG (img1.png, img2.png, ...)")
        print("  - Texto: result.md")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    # Crear directorio de salida con datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = Path(pdf_file).stem  # Obtener nombre sin extensión
    output_dir = f"target_{nombre_base}_{timestamp}"
    
    # Opcional: directorio de salida personalizado
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    print(f"📄 Archivo PDF: {pdf_file}")
    print(f"📂 Directorio de salida: {output_dir}")
    print(f"⏰ Timestamp: {timestamp}")
    print(f"🔄 Conversión: PDF → MD con imágenes PNG")
    print("-" * 50)
    
    # Procesar el PDF
    success = procesar_pdf(pdf_file, output_dir)
    
    if success:
        print("\n🎉 ¡Procesamiento completado!")
        print(f"📁 Resultados guardados en: {output_dir}")
        print(f"📄 Archivo de texto: {output_dir}/result.md")
        print(f"🖼️  Imágenes: {output_dir}/img*.png")
    else:
        print("\n💥 Error en el procesamiento")
        sys.exit(1)

if __name__ == "__main__":
    main() 