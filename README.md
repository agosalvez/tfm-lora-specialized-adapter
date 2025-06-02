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

## 🧰 Requisitos del Sistema

- **Hardware**: GPU con mínimo 8GB VRAM (probado en T4)
- **Software**: Python 3.8+, CUDA 11.8+
- **Dependencias principales**: transformers, peft, torch, docling, flask
- **Configuración de pruebas**: 32GB RAM, 8 cores CPU, Tesla T4 (16GB VRAM)

## 🗂️ Estructura del Proyecto

```bash
tfm-lora-specialized-adapter/
├── apps/
│   └── procesado-imagenes/        # Servidor API REST para análisis de imágenes
│       ├── setup.py              # Configuración del modelo Qwen2-VL
│       ├── server.py             # Servidor Flask con API REST
│       ├── client.py             # Cliente Python para la API
│       └── requirements.txt      # Dependencias del servidor
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

- Extracción: DocLING sobre documentos académicos
- Preparación: estructuración para LoRA
- Entrenamiento: Adapters LoRA con LlamaFactory
- Evaluación: Inferencia y validación del conocimiento

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

## 🎓 Contexto Académico

Trabajo de Fin de Máster (TFM) en Inteligencia Artificial, centrado en la democratización del fine-tuning de LLMs mediante PEFT.

## 🪪 Licencia

MIT License — ver archivo `LICENSE` para más detalles.

## 👤 Autor

Desarrollado por **Adrián Gosálvez** — TFM en IA.

Para más información técnica, consultar el código fuente y la documentación asociada.
