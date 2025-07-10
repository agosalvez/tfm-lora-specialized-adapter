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

def procesar_pdf(pdf_file, output_dir="artifacts/imagenes_extraidas"):
    """
    Procesa un PDF usando docling y extrae texto e imágenes
    Siempre convierte de PDF a MD con imágenes PNG
    
    Args:
        pdf_file (str): Ruta al archivo PDF (obligatorio)
        output_dir (str): Directorio de salida para imágenes
    
    Returns:
        bool: True si el procesamiento fue exitoso, False en caso contrario
    """
    
    # Verificar que el archivo PDF existe
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        return False
    
    # Crear directorio de salida si no existe (incluyendo directorios padres)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Comando docling con valores fijos: from pdf, to md, imágenes PNG
    cmd = [
        "docling",
        pdf_file,
        "--from", "pdf",
        "--to", "md",
        "--image-export-mode", "referenced",
        "--output", output_dir
    ]
    
    print(f"🔄 Ejecutando: {' '.join(cmd)}")
    
    try:
        # Ejecutar el comando
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print("✅ Procesamiento completado exitosamente")
        print(f"📁 Contenido guardado en: {output_dir}")
        
        # Renombrar imágenes y mover archivo de texto
        renombrar_archivos_generados(output_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar docling: {e}")
        print(f"Salida de error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Error: No se encontró el comando 'docling'")
        print("Asegúrate de que docling esté instalado y disponible en el PATH")
        return False

def renombrar_archivos_generados(output_dir):
    """
    Renombra las imágenes generadas a image1.png, image2.png, etc.
    y mueve el archivo de texto a demo.md fuera de la carpeta
    
    Args:
        output_dir (str): Directorio donde están los archivos generados
    """
    try:
        # Buscar archivos de imagen PNG en el directorio (incluyendo subdirectorios)
        imagen_files = []
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.png'):
                    imagen_files.append(os.path.join(root, file))
        
        # Ordenar por nombre de archivo
        imagen_files.sort()
        
        print(f"🖼️  Renombrando {len(imagen_files)} imágenes...")
        
        # Renombrar imágenes correlativamente
        for i, old_path in enumerate(imagen_files, 1):
            new_name = f"image{i}.png"
            new_path = os.path.join(output_dir, new_name)
            
            # Mover archivo al directorio principal si está en subdirectorio
            if os.path.dirname(old_path) != output_dir:
                shutil.move(old_path, new_path)
                print(f"   📄 {os.path.basename(old_path)} → {new_name} (movido)")
            elif old_path != new_path:
                os.rename(old_path, new_path)
                print(f"   📄 {os.path.basename(old_path)} → {new_name}")
        
        # Buscar y mover el archivo de texto (incluyendo subdirectorios)
        md_files = []
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
        
        if md_files:
            md_file = md_files[0]  # Tomar el primer archivo MD encontrado
            new_md_path = "artifacts/texto.md"
            
            # Crear directorio artifacts si no existe
            Path("artifacts").mkdir(exist_ok=True)
            
            # Mover el archivo de texto a la carpeta artifacts
            shutil.move(md_file, new_md_path)
            print(f"📄 Archivo de texto movido: {os.path.basename(md_file)} → artifacts/texto.md")
        
        # Limpiar subdirectorios vacíos si existen
        for root, dirs, files in os.walk(output_dir, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):  # Si está vacío
                        os.rmdir(dir_path)
                        print(f"🗑️  Eliminado subdirectorio vacío: {dir_path}")
                except OSError:
                    pass  # Ignorar errores al eliminar directorios
        
        print(f"✅ Renombrado completado: {len(imagen_files)} imágenes")
        
    except Exception as e:
        print(f"⚠️  Advertencia: Error al renombrar archivos: {e}")

def main():
    """Función principal"""
    
    # Verificar que se proporcione el archivo PDF como parámetro obligatorio
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar el archivo PDF como parámetro")
        print("Uso: python docling.py <archivo_pdf>")
        print("Ejemplo: python docling.py documento.pdf")
        print("")
        print("El script siempre convierte:")
        print("  - FROM: PDF")
        print("  - TO: MD (Markdown)")
        print("  - Imágenes: PNG (image1.png, image2.png, ...)")
        print("  - Texto: artifacts/texto.md")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    print(f"📄 Archivo PDF: {pdf_file}")
    print(f"📂 Directorio de salida: artifacts/")
    print(f"🔄 Conversión: PDF → MD con imágenes PNG")
    print("-" * 50)
    
    # Procesar el PDF
    success = procesar_pdf(pdf_file, "artifacts/imagenes_extraidas")
    
    if success:
        print("\n🎉 ¡Procesamiento completado!")
        print(f"📁 Imágenes guardadas en: artifacts/imagenes_extraidas/")
        print(f"📄 Archivo de texto: artifacts/texto.md")
        print(f"🖼️  Imágenes: artifacts/imagenes_extraidas/image*.png")
    else:
        print("\n💥 Error en el procesamiento")
        sys.exit(1)

if __name__ == "__main__":
    main() 