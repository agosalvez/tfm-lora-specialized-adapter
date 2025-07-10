# Extractor de Documentos con Docling

Este proyecto permite procesar documentos PDF, extraer texto e imágenes, y generar descripciones automáticas de las imágenes mediante una API.

## Características

- **Extracción de PDF**: Convierte PDFs a Markdown con imágenes PNG
- **Renombrado automático**: Las imágenes se renombran correlativamente (image1.png, image2.png, etc.)
- **Procesamiento de imágenes**: Genera descripciones automáticas de cada imagen
- **Directorios con timestamp**: Cada ejecución crea un directorio único con fecha y hora
- **Preservación de historial**: Los procesamientos anteriores nunca se sobrescriben
- **Logging completo**: Registro detallado de todas las operaciones

## Estructura del Proyecto

```
├── docling.py              # Script principal de extracción PDF
├── process_document.py     # Orquestador completo del proceso
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Este archivo
└── artifacts_YYYYMMDD_HHMMSS/  # Carpeta principal de resultados (generado con timestamp)
    ├── texto.md           # Texto original extraído del PDF
    ├── texto_final.md     # Texto con descripciones insertadas
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

3. **Crear archivo de configuración .env**:
   ```bash
   # Crear archivo .env en el mismo directorio que process_document.py
   cat > .env << 'EOF'
   # Configuración de la API para el procesamiento de imágenes
   API_URL=http://localhost:5000/analyze
   AUTH_TOKEN=tu_token_aqui
   EOF
   ```

4. **Editar configuración**:
   ```bash
   # Editar .env con tu configuración real
   nano .env
   ```

5. **Verificar instalación**:
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

### Opción 3: Solo Crear Texto Final

Si ya tienes las descripciones generadas y solo quieres crear texto_final.md:

```bash
python process_document.py --insert-descriptions
```

### Opción 4: Crear Texto Final desde Carpeta Específica

Si quieres crear texto_final.md usando una carpeta artifacts específica (útil para re-procesar resultados anteriores):

```bash
python process_document.py --insert-descriptions-from artifacts_20240315_143022
```

**Características:**
- ✅ Usa una carpeta artifacts existente (no crea nueva)
- ✅ Corrige automáticamente enlaces de imágenes en texto.md
- ✅ Genera texto_final.md con descripciones insertadas
- ✅ Preserva el archivo texto.md original
- ✅ Ideal para re-procesar resultados anteriores

### Opción 5: Verificar Configuración

Para verificar que el archivo .env esté configurado correctamente:

```bash
python process_document.py --check-config
```

Esta opción te mostrará:
- ✅ Si el archivo .env existe y se carga correctamente
- ✅ Si la API URL está configurada
- ✅ Si el token está configurado
- ✅ Si la API responde correctamente
- ⚠️ Advertencias si falta configuración

### Opción 6: Probar Imagen Específica

Para probar el procesamiento de una sola imagen (útil para debugging):

```bash
python process_document.py --test-image ruta/a/imagen.png
```

**Ejemplo:**
```bash
python process_document.py --test-image ./artifacts_20240315_143022/imagenes_extraidas/image1.png
```

Esta opción:
- ✅ Prueba solo una imagen específica
- ✅ Muestra logging detallado del proceso
- ✅ Muestra la descripción generada
- ✅ Ideal para identificar problemas específicos

## Configuración de la API

### Archivo .env

El sistema utiliza un archivo `.env` para la configuración. Crea un archivo `.env` en el mismo directorio que `process_document.py` con el siguiente contenido:

```bash
# Configuración de la API para el procesamiento de imágenes
API_URL=http://localhost:5000/analyze
AUTH_TOKEN=tu_token_aqui
```

**Ejemplo de archivo .env:**
```bash
# .env
API_URL=http://localhost:5000/analyze
AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
```

### Configuración por defecto

Si no existe el archivo `.env`, el script usa:
- **URL**: `http://localhost:5000/analyze`
- **Token**: `TOKEN_FROM_ENV_FILE`
- **Headers**: `Authorization: Bearer TOKEN_FROM_ENV_FILE`

### Formato de la petición POST

```python
{
    "text": "Las imágenes se basan en una situación de una actuación de magia e ilusionismo. Quiero que describas lo que ves, haciendo hincapié en flechas, hacia dónde se dirigen, qué hacen o qué intención quiere aportar la imagen.",
    "image": <archivo_binario>
}
```

## Archivos Generados

### artifacts_TIMESTAMP/texto.md
Archivo Markdown con el texto original extraído del PDF. **Este archivo se mantiene intacto como referencia.**

### artifacts_TIMESTAMP/texto_final.md
Archivo Markdown final que incluye el texto extraído **con las descripciones de las imágenes insertadas automáticamente** justo después de cada enlace a imagen. **Este es el archivo que querrás usar como resultado final.**

### artifacts_TIMESTAMP/imagenes_extraidas/
Directorio con las imágenes extraídas:
- `image1.png`
- `image2.png`
- `image3.png`
- ...

### artifacts_TIMESTAMP/image_descriptions/
Directorio con las descripciones generadas:
- `image1.md` - Descripción de image1.png
- `image2.md` - Descripción de image2.png
- `image3.md` - Descripción de image3.png
- ...

## Logging

El script genera logs detallados en:
- **Consola**: Salida en tiempo real
- **Archivo**: `process_document.log`

## Directorios con Timestamp

El sistema crea automáticamente directorios únicos para cada ejecución:

- **Formato**: `artifacts_YYYYMMDD_HHMMSS` (ej: `artifacts_20240315_143022`)
- **Beneficios**: 
  - ✅ Nunca sobrescribe procesamientos anteriores
  - ✅ Mantiene un historial completo de todas las ejecuciones
  - ✅ Permite comparar resultados entre diferentes versiones
  - ✅ Facilita la organización y el control de versiones

**Ejemplo de estructura temporal:**
```
├── artifacts_20240315_143022/    # Primer procesamiento
│   ├── texto.md
│   ├── texto_final.md
│   └── ...
├── artifacts_20240315_150445/    # Segundo procesamiento
│   ├── texto.md
│   ├── texto_final.md
│   └── ...
└── artifacts_20240315_162130/    # Tercer procesamiento
    ├── texto.md
    ├── texto_final.md
    └── ...
```

## Corrección Automática de Enlaces de Imágenes

El sistema incluye una funcionalidad automática que corrige los enlaces de imágenes en `texto.md`:

1. **Detección inteligente**: Busca enlaces generados por docling (genéricos o temporales)
2. **Corrección automática**: Reemplaza con rutas correctas a `imagenes_extraidas/imageX.png`
3. **Formatos soportados**: 
   - `![alt](ruta_genérica.png)` → `![alt](imagenes_extraidas/image1.png)`
   - `[link](ruta_genérica.png)` → `[link](imagenes_extraidas/image1.png)`
   - `<img src="ruta_genérica.png">` → `<img src="imagenes_extraidas/image1.png">`
4. **Inserción inteligente**: Si no hay enlaces, detecta menciones como "figura", "imagen", etc. y agrega enlaces
5. **Orden correlativo**: Asocia automáticamente con image1.png, image2.png, etc.

**Ejemplo de corrección:**
```markdown
# Antes (generado por docling)
![Figura](ruta_temporal_12345.png)

# Después (corregido automáticamente)
![Figura](imagenes_extraidas/image1.png)
```

## Inserción Automática de Descripciones

El sistema incluye una funcionalidad automática que crea un archivo `texto_final.md` con las descripciones de las imágenes insertadas:

1. **Preservación del original**: Mantiene `texto.md` intacto como referencia
2. **Detección automática**: Busca todos los enlaces a imágenes en el texto extraído
3. **Formato reconocido**: Detecta enlaces como `![alt](imagenes_extraidas/image1.png)` o `![alt](image1.png)`
4. **Inserción inteligente**: Coloca la descripción correspondiente justo después de cada enlace
5. **Formato consistente**: Añade un título `**Descripción de la imagen X:**` seguido del contenido
6. **Archivo final**: Genera `texto_final.md` con el resultado completo

**Ejemplo de resultado en texto_final.md:**
```markdown
![Figura 1](imagenes_extraidas/image1.png)

**Descripción de la imagen 1:**
En la imagen se puede observar un mago realizando un truco con cartas, con flechas que indican el movimiento de las manos hacia la izquierda...
```

## Manejo de Errores

El sistema incluye manejo robusto de errores:
- Verificación de existencia de archivos
- Validación de respuestas de API
- Logging detallado de errores
- Continuación del proceso aunque fallen algunas imágenes

## Ejemplo de Uso Completo

```bash
# 0. Verificar configuración (recomendado antes del primer uso)
python process_document.py --check-config

# 1. Procesar un documento PDF (proceso completo)
python process_document.py mi_documento.pdf

# 2. Verificar resultados (reemplaza TIMESTAMP con el timestamp generado)
ls -la artifacts_TIMESTAMP/
ls -la artifacts_TIMESTAMP/imagenes_extraidas/
ls -la artifacts_TIMESTAMP/image_descriptions/

# 3. Ver archivos generados
cat artifacts_TIMESTAMP/texto.md          # Texto original con enlaces corregidos
cat artifacts_TIMESTAMP/texto_final.md    # Texto con descripciones insertadas

# 4. (Opcional) Re-procesar usando carpeta específica
python process_document.py --insert-descriptions-from artifacts_20240315_143022

# 5. (Opcional) Probar imagen específica para debugging
python process_document.py --test-image ./artifacts_*/imagenes_extraidas/image1.png
```

### Flujo de Trabajo Típico

```bash
# Primera ejecución - Procesamiento completo
python process_document.py documento.pdf
# → Genera: artifacts_20240315_143022/

# Si necesitas re-procesar solo las descripciones
python process_document.py --insert-descriptions-from artifacts_20240315_143022
# → Actualiza: artifacts_20240315_143022/texto_final.md

# Para debugging de una imagen específica
python process_document.py --test-image ./artifacts_20240315_143022/imagenes_extraidas/image3.png
# → Muestra solo el procesamiento de esa imagen
```

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

### Errores de conexión con la API

#### Error: "Connection refused" en localhost:5000
```bash
🔌 Error de conexión al procesar imagen.png - Verifica que la API esté ejecutándose
```

**Solución:**
1. Verificar que el servidor API esté ejecutándose en el puerto 5000
2. Usar el comando de verificación: `python process_document.py --check-config`

#### Error: "Timeout" 
```bash
⏰ Timeout al procesar imagen.png - La API tardó más de 60 segundos
```

**Solución:**
1. La imagen puede ser muy grande
2. El servidor puede estar sobrecargado
3. Verificar la conectividad de red

#### Error de autorización (401)
```bash
🔑 Error de autorización - Verifica el token en el archivo .env
```

**Solución:**
1. Verificar que el token en `.env` sea correcto
2. Verificar que el token no haya expirado

#### Error: Endpoint no encontrado (404)
```bash
🔍 Endpoint no encontrado - Verifica la URL de la API
```

**Solución:**
1. Verificar que la URL en `.env` sea correcta
2. Verificar que el endpoint `/analyze` esté disponible

### Error: "No se encontraron imágenes"
Verificar que el PDF contenga imágenes y que docling las haya extraído correctamente en el directorio `artifacts_TIMESTAMP/imagenes_extraidas/`.

### Problemas con la opción --insert-descriptions-from

#### Error: "La carpeta artifacts no existe"
```bash
❌ La carpeta artifacts no existe: artifacts_20240315_143022
```

**Solución:**
```bash
# Verificar carpetas artifacts disponibles
ls -d artifacts_*

# Usar la carpeta correcta
python process_document.py --insert-descriptions-from artifacts_20240315_143022
```

#### Error: "No se encontró texto.md"
```bash
❌ No se encontró texto.md en: artifacts_20240315_143022
```

**Solución:**
1. Verificar que la carpeta sea de un procesamiento completo
2. Ejecutar primero el procesamiento completo:
```bash
python process_document.py documento.pdf
```

#### Error: "No se encontró carpeta image_descriptions"
```bash
❌ No se encontró carpeta image_descriptions en: artifacts_20240315_143022
```

**Solución:**
1. Las descripciones no se generaron en esa carpeta
2. Ejecutar primero el procesamiento de imágenes:
```bash
# Opción 1: Procesamiento completo
python process_document.py documento.pdf

# Opción 2: Solo generar descripciones (si ya tienes las imágenes)
python process_document.py --insert-descriptions
```

### Problemas con la corrección de enlaces de imágenes

#### Los enlaces no se corrigen automáticamente
```bash
⚠️ No se pudieron corregir algunos enlaces de imágenes
```

**Diagnóstico:**
```bash
# Verificar contenido de texto.md
cat artifacts_*/texto.md | grep -i "imagen\|figura\|png\|jpg"

# Verificar imágenes disponibles
ls -la artifacts_*/imagenes_extraidas/
```

**Solución:**
1. El sistema detecta automáticamente varios formatos
2. Si los enlaces no se detectan, el sistema agrega enlaces después de menciones como "figura", "imagen", etc.
3. Puedes editar manualmente `texto.md` si es necesario

#### Los enlaces apuntan a rutas incorrectas
**Verificar:**
```bash
# Verificar estructura de carpetas
find artifacts_* -name "*.png" -o -name "*.md" | sort

# Verificar contenido de texto.md
grep -n "imagenes_extraidas" artifacts_*/texto.md
```

### Problemas con el archivo .env

#### Archivo .env no encontrado
```bash
# El log mostrará:
⚠️ Archivo .env no encontrado en: /ruta/completa/.env
ℹ️  Se usarán valores por defecto para configuración
```

**Solución:**
1. Crea el archivo `.env` en el mismo directorio que `process_document.py`
2. Asegúrate de que el archivo no tenga extensión adicional (no `.env.txt`)

#### Verificar configuración cargada
```bash
# Al ejecutar el script, verás:
🔧 Configuración del procesador:
   - API URL: http://localhost:5000/analyze
   - Token: ***kAi9
📁 Directorio de salida: artifacts_20240315_143022
```

#### Problema con permisos del archivo .env
```bash
# Verificar permisos
ls -la .env

# Dar permisos de lectura si es necesario
chmod 644 .env
```

### Encontrar el directorio correcto
Para encontrar el directorio más reciente:
```bash
ls -la artifacts_* | tail -1    # Mostrar el directorio más reciente
```

### Navegación rápida
```bash
# Entrar al directorio más reciente
cd $(ls -d artifacts_* | tail -1)

# Ver todos los archivos generados
find . -type f -name "*.md" -o -name "*.png" | sort
```

### Configuración rápida del archivo .env
```bash
# Crear archivo .env básico
echo "API_URL=http://localhost:5000/analyze" > .env
echo "AUTH_TOKEN=tu_token_aqui" >> .env

# Verificar que se creó correctamente
cat .env

# Probar la configuración
python process_document.py --check-config
```

### Debugging del procesamiento de imágenes

#### Probar una imagen específica
```bash
# Probar procesamiento de una imagen
python process_document.py --test-image ./artifacts_*/imagenes_extraidas/image1.png

# Ver logs detallados
tail -f process_document.log
```

#### Verificar imágenes disponibles
```bash
# Listar todas las imágenes procesables
find ./artifacts_* -name "*.png" -type f | sort

# Verificar tamaño de las imágenes
ls -lh ./artifacts_*/imagenes_extraidas/
```

#### Probar la API manualmente con curl
```bash
# Cargar token desde .env
TOKEN=$(grep '^AUTH_TOKEN=' .env | cut -d '=' -f2)

# Probar con una imagen específica
curl -X POST http://localhost:5000/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@./artifacts_*/imagenes_extraidas/image1.png" \
  -F "text=Describe esta imagen brevemente." \
  -v
```

#### Verificar conectividad
```bash
# Verificar que la API responde
curl -I http://localhost:5000/analyze

# Verificar configuración completa
python process_document.py --check-config
``` 