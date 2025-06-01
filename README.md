# TFM: Especialización de LLMs mediante Adapters LoRA

## Descripción

Este proyecto implementa un sistema de especialización de modelos de lenguaje de gran escala utilizando técnicas de Parameter-Efficient Fine-Tuning (PEFT) mediante LoRA (Low-Rank Adaptation). El sistema procesa documentos de un dominio concreto multimodales y entrena adapters especializados sobre el modelo base PHI4-mini-instruct.

## Características Principales

- Procesamiento multimodal con Docling para extracción de documentos académicos
- Entrenamiento eficiente mediante LoRA con reducción del 99.9% de parámetros entrenables
- Especialización de dominio para conocimiento específico de papers académicos
- Optimizado para recursos limitados (GPU T4, 16GB VRAM)
- Pipeline completo desde extracción de datos hasta inferencia especializada

## Requisitos del Sistema

- **Hardware**: GPU con mínimo 8GB VRAM (probado en T4)
- **Software**: Python 3.8+, CUDA 11.8+
- **Dependencias principales**: transformers, peft, torch, docling

## Estructura del Proyecto
```bash
tfm-lora-specialized-adapter/
├── data/                           # Datasets y datos procesados
├── scripts/
│   ├── train.sh                   # Script de entrenamiento
│   └── inference.py               # Script de inferencia
├── models/
│   └── lora_adapters/             # Adapters LoRA entrenados
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
## Uso Rápido

### 1. Configuración del entorno

```bash
# Instalar LlamaFactory framework
dependencies/llamafactory_setup.md
// Incluir dataset a entrenar
// Ajustar configuracion en scripts/traing.sh
```

### 2. Entrenamiento del Adapter

```bash
cd scripts
// Ajustar configuracion en scripts/traing.sh
chmod +x train.sh
./train.sh
```

### 3. Inferencia con Adapter Especializado

```bash
cd scripts
python inference.py
```
### Configuración
#### Parámetros LoRA
El archivo models/lora_adapters/adapter_config.json contiene la configuración utilizada:

- Rank (r): Dimensión de las matrices de bajo rango
- Alpha: Factor de escala para las actualizaciones
- Target modules: Capas del transformer adaptadas
- Learning rate: Tasa de aprendizaje específica para adapters

#### Dataset
El archivo config/dataset_config.json define la estructura y parámetros del dataset de entrenamiento.

## Resultados
- **Reducción de parámetros**: De 3.8B a ~234M parámetros entrenables (6.2% del modelo original)
- **Configuración LoRA**: Rank=128, Alpha=256, 4 módulos objetivo por capa
- **Tiempo de entrenamiento**: 21 minutos en GPU T4 (240 steps, 20 epochs)
- **Tamaño del adapter**: ~10MB (vs 7.6GB del modelo completo)
- **Convergencia**: Loss redujo de 2.09 a 0.07 durante el entrenamiento
- **Velocidad**: 2.8 samples/segundo en GPU T4
- **Especialización exitosa**: El modelo adquiere conocimiento específico del dominio sin perder capacidades generales

### Métricas de Entrenamiento
- **Train Loss**: 0.198 (promedio final)
- **Learning Rate**: 0.0005 (constante)
- **Total FLOPs**: 1.01e+16
- **Duración**: 1,273 segundos (21:14 minutos)

#### Métricas de Entrenamiento
Los resultados detallados están disponibles en:

- results/training_logs/train_results.json - Métricas finales
- results/training_logs/trainer_log.jsonl - Log completo del proceso
- results/training_logs/all_results.json - Todas las métricas registradas

#### Metodología

- Extracción de datos: Procesamiento multimodal de documentos académicos con Docling
- Preparación del dataset: Estructuración de datos para entrenamiento LoRA
- Entrenamiento: Fine-tuning eficiente mediante adapters de bajo rango usando LlamaFactory
- Evaluación: Validación de conocimiento especializado adquirido

#### Archivos No Incluidos
Por limitaciones de tamaño, los siguientes archivos no están en el repositorio:

- Checkpoints intermedios (~8GB) - Disponibles bajo solicitud
- Dataset original completo - Derivado de documentos académicos específicos
- Logs de entrenamiento completos - Solo métricas esenciales incluidas

El adapter entrenado final está disponible en models/lora_adapters/ y es completamente funcional para inferencia.

#### Frameworks y Dependencias
*LlamaFactory*

- Repositorio: https://github.com/hiyouga/LLaMA-Factory
- Uso: Framework principal para entrenamiento LoRA
- Paper: LlamaFactory: [Unified Efficient Fine-Tuning of 100+ Language Models](https://doi.org/10.48550/arXiv.2403.13372)
- Instalación: [README.md from LLamaFactory](https://github.com/hiyouga/LLaMA-Factory/blob/main/README.md)

### Contexto Académico
Este proyecto forma parte de un Trabajo de Fin de Máster en Inteligencia Artificial, enfocado en la democratización del fine-tuning de modelos de lenguaje de gran escala mediante técnicas parameter-efficient.
### Licencia
MIT License - Ver archivo LICENSE para más detalles.
### Autor
Desarrollado por Adrián Gosálvez como Trabajo de Fin de Máster en Inteligencia Artificial.

Para más detalles técnicos, consultar la documentación del proyecto y el código fuente.
