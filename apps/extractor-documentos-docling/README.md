# Extractor de Documentos con Docling

Este proyecto permite procesar documentos PDF, extraer texto e imágenes, y generar descripciones automáticas de las imágenes mediante una API.

## Características

- **Extracción de PDF**: Convierte PDFs a Markdown con imágenes PNG
- **Renombrado automático**: Las imágenes se renombran correlativamente (image1.png, image2.png, etc.)
- **Procesamiento de imágenes**: Genera descripciones automáticas de cada imagen
- **Logging completo**: Registro detallado de todas las operaciones

## Estructura del Proyecto

```
├── docling.py              # Script principal de extracción PDF
├── process_document.py     # Orquestador completo del proceso
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Este archivo
└── artifacts/              # Carpeta principal de resultados (generado)
    ├── texto.md           # Texto extraído del PDF
    ├── imagenes_extraidas/ # Imágenes extraídas
    │   ├── image1.png
    │   ├── image2.png
    │   └── ...
    └── image_descriptions/ # Descripciones generadas
        ├── image1.md
        ├── image2.md
        └── ...
```

## Instalación

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Instalar docling** (si no está instalado):
   ```bash
   pip install docling
   ```

3. **Verificar instalación**:
   ```bash
   python -c "import docling; print('Docling instalado correctamente')"
   ```

## Uso

### Opción 1: Proceso Completo (Recomendado)

Ejecuta todo el flujo: extracción PDF + procesamiento de imágenes:

```bash
python process_document.py documento.pdf
```

### Opción 2: Solo Extracción PDF

Si solo quieres extraer texto e imágenes del PDF:

```bash
python docling.py documento.pdf
```

## Configuración de la API

El script `process_document.py` está configurado para conectarse a:
- **URL**: `http://localhost:5000`
- **Token**: `123123123`
- **Headers**: `Authorization: Bearer 123123123`

### Formato de la petición POST

```python
{
    "text": "Las imágenes se basan en una situación de una actuación de magia e ilusionismo. Quiero que describas lo que ves, haciendo hincapié en flechas, hacia dónde se dirigen, qué hacen o qué intención quiere aportar la imagen.",
    "image": <archivo_binario>
}
```

## Archivos Generados

### artifacts/texto.md
Archivo Markdown con el texto extraído del PDF.

### artifacts/imagenes_extraidas/
Directorio con las imágenes extraídas:
- `image1.png`
- `image2.png`
- `image3.png`
- ...

### artifacts/image_descriptions/
Directorio con las descripciones generadas:
- `image1.md` - Descripción de image1.png
- `image2.md` - Descripción de image2.png
- `image3.md` - Descripción de image3.png
- ...

## Logging

El script genera logs detallados en:
- **Consola**: Salida en tiempo real
- **Archivo**: `process_document.log`

## Manejo de Errores

El sistema incluye manejo robusto de errores:
- Verificación de existencia de archivos
- Validación de respuestas de API
- Logging detallado de errores
- Continuación del proceso aunque fallen algunas imágenes

## Ejemplo de Uso Completo

```bash
# 1. Procesar un documento PDF
python process_document.py mi_documento.pdf

# 2. Verificar resultados
ls -la artifacts/
ls -la artifacts/imagenes_extraidas/
ls -la artifacts/image_descriptions/
cat artifacts/texto.md

## Notas Técnicas

- **Formato de imágenes**: PNG
- **Codificación**: UTF-8
- **Timeout API**: 30 segundos
- **Orden de procesamiento**: Las imágenes se procesan en orden numérico

## Troubleshooting

### Error: "No se encontró el comando 'docling'"
```bash
pip install docling
```

### Error: "Connection refused" en localhost:5000
Verificar que el servidor API esté ejecutándose en el puerto 5000.

### Error: "No se encontraron imágenes"
Verificar que el PDF contenga imágenes y que docling las haya extraído correctamente. 