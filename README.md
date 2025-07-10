# 🚀 TFM: Especialización de LLMs mediante Adapters LoRA

## 📘 Descripción

Este proyecto, desarrollado como Trabajo de Fin de Máster (TFM) por Adrián Gosálvez, implementa un sistema de especialización de modelos de lenguaje de gran escala utilizando técnicas de Parameter-Efficient Fine-Tuning (PEFT) mediante LoRA (Low-Rank Adaptation). El sistema procesa documentos de un dominio concreto multimodales y entrena adapters especializados sobre el modelo base PHI4-mini-instruct.

## ✨ Características Principales

- 🧠 Procesamiento multimodal con Docling para extracción de documentos académicos
- 🛠️ Entrenamiento eficiente mediante LoRA con reducción del 99.9% de parámetros entrenables
- 🧾 Especialización de dominio para conocimiento específico de papers académicos
- ⚙️ Optimizado para recursos limitados (GPU T4, 16GB VRAM)
- 📈 Pipeline completo desde extracción de datos hasta inferencia especializada
- 🌐 **Servidor API REST** para procesamiento de imágenes con Qwen2-VL
- 🐍 **Cliente Python** para interacción con la API
- 📄 **Extractor de documentos PDF** con descripciones automáticas de imágenes
- 🔄 **Sistema de reemplazo inteligente** que convierte enlaces en descripciones textuales

## 🧰 Requisitos del Sistema

- **Hardware**: GPU con mínimo 8GB VRAM (probado en T4)
- **Software**: Python 3.8+, CUDA 11.8+
- **Dependencias principales**: transformers, peft, torch, docling, flask
- **Configuración de pruebas**: 32GB RAM, 8 cores CPU, Tesla T4 (16GB VRAM)

## 🗂️ Estructura del Proyecto

```bash
tfm-lora-specialized-adapter/
├── apps/
│   ├── procesado-imagenes/        # Servidor API REST para análisis de imágenes
│   │   ├── setup.py              # Configuración del modelo Qwen2-VL
│   │   ├── server.py             # Servidor Flask con API REST
│   │   ├── client.py             # Cliente Python para la API
│   │   └── requirements.txt      # Dependencias del servidor
│   └── extractor-documentos-docling/ # Sistema de extracción y procesado de PDFs
│       ├── docling.py            # Script principal de extracción PDF
│       ├── process_document.py   # Orquestador completo del proceso
│       ├── requirements.txt      # Dependencias del extractor
│       └── README.md            # Documentación detallada del extractor
├── data/                          # Datasets y datos procesados
├── scripts/
│   ├── train.sh                  # Script de entrenamiento
│   └── inference.py              # Script de inferencia
├── models/
│   └── lora_adapters/            # Adapters LoRA entrenados
│       ├── adapter_config.json   # Configuración del adapter
│       └── adapter_model.safetensors # Pesos del adapter (~10MB)
├── config/
│   ├── dataset_config.json       # Configuración del dataset para LoRA
│   ├── tokenizer_config.json     # Configuración del tokenizer
│   └── special_tokens_map.json   # Mapeo de tokens especiales
├── results/
│   └── training_logs/             # Logs y métricas de entrenamiento
│       ├── trainer_log.jsonl     # Log detallado del entrenamiento
│       ├── trainer_state.json    # Estado final del entrenador
│       ├── train_results.json    # Resultados de entrenamiento
│       └── all_results.json      # Métricas completas
├── dependencies/                   # Framework y dependencias
│   ├── llamafactory_setup.md     # Configuración LlamaFactory
│   └── requirements_llamafactory.txt # Dependencias específicas
└── README.md
```

## ⚡ Uso Rápido

### 🔧 1. Configuración del entorno

```bash
# Instalar LlamaFactory framework
dependencies/llamafactory_setup.md
# Incluir dataset a entrenar
# Ajustar configuración en scripts/train.sh
```

### 🏋️‍♂️ 2. Entrenamiento del Adapter

```bash
cd scripts
chmod +x train.sh
./train.sh
```

### 🔍 3. Inferencia con Adapter Especializado

```bash
cd scripts
python inference.py
```

### 📄 4. Procesamiento de Documentos PDF

```bash
# Iniciar servidor API de imágenes
cd apps/procesado-imagenes
python setup.py && python server.py

# En otra terminal: procesar PDF
cd apps/extractor-documentos-docling
python process_document.py documento.pdf
```

## 🌐 Servidor API REST para Procesamiento de Imágenes

El proyecto incluye un servidor API REST basado en Flask que utiliza el modelo Qwen2-VL para análisis de imágenes con lenguaje natural.

### ⚙️ Configuración del Servidor

```bash
cd apps/procesado-imagenes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py
python server.py
```

### 🔌 Endpoints Disponibles

#### 🖥️ GET `/` - Interfaz Web

[http://localhost:5000](http://localhost:5000)

#### 🔍 GET `/status` - Estado del Servidor

```bash
curl http://localhost:5000/status
```

#### 🧪 POST `/analyze` - Análisis de Imagen (Form-Data)

```bash
curl -X POST http://localhost:5000/analyze \
  -F "image=@ejemplo.jpg" \
  -F "text=¿Qué objetos ves en esta imagen?"
```

#### 🧪 POST `/analyze_base64` - Análisis de Imagen (Base64)

```bash
curl -X POST http://localhost:5000/analyze_base64 \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "text": "Describe esta imagen en detalle"
  }'
```

#### 💓 GET `/health` - Estado de Salud

```bash
curl http://localhost:5000/health
```

## 🐍 Cliente Python

```bash
python client.py --interactive
python client.py --image foto.jpg --text "¿Qué ves?"
python client.py --status
python client.py --server http://192.168.1.100:5000 --interactive
python client.py --batch ./imagenes --questions preguntas.txt
```

## 📄 Extractor de Documentos con Docling

El proyecto incluye un sistema completo de extracción y procesamiento de documentos PDF que combina Docling para la extracción con el servidor API de imágenes para generar descripciones automáticas.

### ✨ Características del Extractor

- 📄 **Extracción inteligente**: Convierte PDFs a Markdown con imágenes PNG
- 🖼️ **Procesamiento de imágenes**: Genera descripciones automáticas usando la API de Qwen2-VL
- 🔗 **Corrección de enlaces**: Actualiza automáticamente las rutas de imágenes
- 🔄 **Reemplazo inteligente**: Sustituye enlaces por descripciones del campo `response`
- ⏰ **Versionado temporal**: Directorios únicos con timestamp para cada procesamiento
- 🔤 **Codificación UTF-8**: Manejo correcto de acentos y caracteres especiales

### 🚀 Uso Rápido del Extractor

```bash
cd apps/extractor-documentos-docling

# Configurar entorno
pip install -r requirements.txt

# Crear archivo de configuración
echo "API_URL=http://localhost:5000/analyze" > .env
echo "AUTH_TOKEN=tu_token_aqui" >> .env

# Verificar configuración
python process_document.py --check-config

# Procesamiento completo de un PDF
python process_document.py documento.pdf
```

### 📂 Archivos Generados

```bash
artifacts_YYYYMMDD_HHMMSS/          # Directorio con timestamp único
├── texto.md                        # Texto original extraído (con enlaces corregidos)
├── texto_final.md                  # Texto final (enlaces reemplazados por descripciones)
├── imagenes_extraidas/             # Imágenes extraídas del PDF
│   ├── image1.png
│   ├── image2.png
│   └── ...
└── image_descriptions/             # Descripciones JSON de cada imagen
    ├── image1.md
    ├── image2.md
    └── ...
```

### 🔧 Modos de Operación

#### 1. **Procesamiento Completo** (Recomendado)
```bash
# Extrae PDF + genera descripciones + crea archivo final
python process_document.py documento.pdf
```

#### 2. **Solo Extracción PDF**
```bash
# Solo convierte PDF a Markdown con imágenes
python docling.py documento.pdf
```

#### 3. **Reprocessado desde Carpeta Específica**
```bash
# Usa una carpeta artifacts existente para crear texto_final.md
python process_document.py --insert-descriptions-from artifacts_20240315_143022
```

#### 4. **Verificación y Debugging**
```bash
# Verificar configuración
python process_document.py --check-config

# Probar imagen específica
python process_document.py --test-image ./artifacts_*/imagenes_extraidas/image1.png
```

### 🔄 Pipeline de Procesamiento

1. **Extracción** → Docling convierte PDF a Markdown + PNG
2. **Corrección** → Enlaces de imágenes se actualizan a rutas reales
3. **Análisis** → Cada imagen se envía a la API para descripción
4. **Procesamiento JSON** → Extrae solo el campo `response` del JSON
5. **Reemplazo** → Enlaces se sustituyen por descripciones en `texto_final.md`

### 📋 Ejemplo de Resultado

**Original (texto.md):**
```markdown
# Trucos de Magia
![Figura 1](imagenes_extraidas/image1.png)
El mago utiliza técnicas especiales.
```

**Final (texto_final.md):**
```markdown
# Trucos de Magia
En la imagen se observa un mago realizando un truco con cartas, mostrando el movimiento de las manos hacia la izquierda mientras sostiene una baraja. Las flechas indican la dirección del movimiento y la intención de desviar la atención del espectador.
El mago utiliza técnicas especiales.
```

### 🔗 Integración con API de Imágenes

El extractor está diseñado para trabajar en conjunto con el servidor API de procesamiento de imágenes:

1. **Servidor API** (`apps/procesado-imagenes/`) debe estar ejecutándose
2. **Configuración** se realiza mediante archivo `.env`
3. **Comunicación** automática para procesar cada imagen extraída
4. **Respuesta JSON** se procesa para extraer solo el campo `response`

### 📖 Documentación Completa

Para información detallada sobre configuración, troubleshooting y todas las funcionalidades disponibles, consulta:

**[📋 README del Extractor de Documentos](apps/extractor-documentos-docling/README.md)**

La documentación incluye:
- Instalación paso a paso
- Configuración del archivo `.env`
- Solución de problemas comunes
- Ejemplos de uso avanzados
- Formato de la API y endpoints
- Manejo de errores y logging

## 🧪 Configuración Hardware

- **CPU**: 8 cores
- **RAM**: 32GB
- **GPU**: Tesla T4 (16GB VRAM)
- **Sistema**: Ubuntu 20.04+ con CUDA 11.8

### 🔧 Optimizaciones para T4

- Cuantización 8-bit automática
- Timeout extendido
- Redimensionado de imágenes grandes

## ⚙️ Configuración Técnica

### 🔩 Parámetros LoRA

Archivo: `models/lora_adapters/adapter_config.json`

- Rank (r): 128
- Alpha: 256
- Target modules: 4 módulos por capa
- Learning rate: 0.0005

### 📂 Dataset

Archivo: `config/dataset_config.json`

## 📊 Resultados

- Reducción de parámetros: de 3.8B a \~234M (6.2%)
- Adapter final: \~10MB
- Tiempo de entrenamiento: 21 minutos (240 steps, 20 epochs)
- Loss: de 2.09 a 0.07
- Velocidad: 2.8 muestras/segundo (T4)

## 📈 Métricas de Entrenamiento

- Train Loss final: 0.198
- Learning Rate: 0.0005
- FLOPs totales: 1.01e+16
- Duración total: 1,273 segundos (\~21 min)

## 🌍 Métricas del Servidor API

- Tiempo de respuesta: 3–8 segundos por imagen
- VRAM usada: 8–12GB
- Concurrencia: múltiple
- Formatos: JPG, PNG, BMP, TIFF, GIF

## 🧪 Metodología

- **Extracción**: DocLING + API de imágenes para documentos académicos multimodales
- **Preparación**: Estructuración y reemplazo inteligente de contenido visual por descripciones
- **Entrenamiento**: Adapters LoRA con LlamaFactory sobre el dataset procesado
- **Evaluación**: Inferencia y validación del conocimiento especializado
- **Pipeline completo**: PDF → Markdown + descripciones → Dataset → LoRA → Modelo especializado

## 📦 Archivos No Incluidos

- Checkpoints intermedios (\~8GB)
- Dataset completo original
- Logs extensos (disponibles bajo petición)

## 🧱 Frameworks y Dependencias

### 🐪 LlamaFactory

- Repositorio: [https://github.com/hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- Paper: [https://doi.org/10.48550/arXiv.2403.13372](https://doi.org/10.48550/arXiv.2403.13372)

### 🖼️ Qwen2-VL

- Modelo: Qwen/Qwen2-VL-7B-Instruct
- Cuantización 8-bit para T4

### 📄 Docling

- Repositorio: [https://github.com/DS4SD/docling](https://github.com/DS4SD/docling)
- Extracción de documentos PDF a Markdown con imágenes

## 🎓 Contexto Académico

Trabajo de Fin de Máster (TFM) en Inteligencia Artificial, centrado en la democratización del fine-tuning de LLMs mediante PEFT.

## 🪪 Licencia

MIT License — ver archivo `LICENSE` para más detalles.

## 👤 Autor

Desarrollado por **Adrián Gosálvez** — TFM en IA.

Para más información técnica, consultar el código fuente y la documentación asociada.
