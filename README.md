# TFM: Especialización de LLMs mediante Adapters LoRA

## Descripción

Este proyecto implementa un sistema de especialización de modelos de lenguaje de gran escala utilizando técnicas de Parameter-Efficient Fine-Tuning (PEFT) mediante LoRA (Low-Rank Adaptation). El sistema procesa documentos académicos multimodales y entrena adapters especializados sobre el modelo base PHI4-mini-instruct.

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
tfm-lora-adapter/
├── data/                    # Datasets y datos procesados
├── scripts/
│   ├── train.sh            # Script de entrenamiento
│   └── inference.py        # Script de inferencia
├── models/                  # Adapters entrenados y checkpoints
├── config/
│   └── dataset_config.json # Configuración del dataset para LoRA
├── results/                 # Logs y resultados de entrenamiento
└── README.md
```
## Uso Rápido

### 1. Entrenamiento del Adapter

```bash
cd scripts
chmod +x train.sh
./train.sh
```

### 2. Inferencia con Adapter Especializado

cd scripts
python inference.py

## Configuración

El archivo config/dataset_config.json contiene los parámetros de configuración para el entrenamiento LoRA:

- **Rank (r)**: Dimensión de las matrices de bajo rango
- **Alpha**: Factor de escala para las actualizaciones
- **Target modules**: Capas del transformer a adaptar
- **Learning rate**: Tasa de aprendizaje específica para adapters

## Resultados

- **Reducción de parámetros**: De 3.8B a ~18M parámetros entrenables
- **Tiempo de entrenamiento**: Optimizado para completarse en hardware convencional
- **Especialización exitosa**: El modelo adquiere conocimiento específico del dominio sin perder capacidades generales

## Metodología

1. **Extracción de datos**: Procesamiento multimodal de documentos académicos con Docling
2. **Preparación del dataset**: Estructuración de datos para entrenamiento LoRA
3. **Entrenamiento**: Fine-tuning eficiente mediante adapters de bajo rango
4. **Evaluación**: Validación de conocimiento especializado adquirido

## Contexto Académico

Este proyecto forma parte de un Trabajo de Fin de Máster en Inteligencia Artificial, enfocado en la democratización del fine-tuning de modelos de lenguaje de gran escala mediante técnicas parameter-efficient.

## Licencia

MIT License - Ver archivo LICENSE para más detalles.

## Autor

Desarrollado por Adrián Gosálvez como Trabajo de Fin de Máster en Inteligencia Artificial.
