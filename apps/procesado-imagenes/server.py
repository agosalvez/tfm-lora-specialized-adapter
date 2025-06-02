#!/usr/bin/env python3
"""
Servidor para modelos de ÚLTIMA GENERACIÓN
Gemma 3 (PaliGemma) + Qwen2.5-VL optimizado para análisis de figuras
"""

import os
import torch
import base64
from flask import Flask, request, jsonify
from transformers import (
    AutoProcessor, AutoModelForCausalLM,
    Qwen2VLForConditionalGeneration, Qwen2VLProcessor,
    PaliGemmaProcessor, PaliGemmaForConditionalGeneration
)
from PIL import Image
from io import BytesIO
import logging
import time
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Prompts especializados para los nuevos modelos
LATEST_ANALYSIS_PROMPTS = {
    "figure_analysis": "Analyze the main human figure in this image. Describe their physical appearance, emotional state, body language, clothing, and the situation they find themselves in. Pay attention to facial expressions and posture.",
    
    "emotional_state": "Focus on the emotional and psychological state of the person in this image. What emotions are visible in their face and body language? What does their overall demeanor suggest about their mental state?",
    
    "comprehensive_analysis": "Provide the most detailed analysis possible of this image, focusing on any human subjects. Include physical appearance, emotional state, activities, environment, clothing, facial expressions, body language, and contextual information.",
    
    "situational_context": "Analyze the situation depicted in this image. What is happening? Who are the people involved? What is the context and what circumstances led to this moment?",
    
    "behavioral_analysis": "Examine the behavior and actions of any people in this image. What are they doing? How are they positioned? What does their body language communicate about their intentions or state of mind?"
}

class LatestModelServer:
    def __init__(self):
        self.models = {}
        self.processors = {}
        self.model_info = {}
        self.current_model = None
        self.device = "cpu"
        
        # Configurar optimizaciones
        self.setup_optimizations()
        self.load_latest_models()
    
    def setup_optimizations(self):
        """Configuraciones para máximo rendimiento con modelos nuevos"""
        cpu_count = os.cpu_count()
        torch.set_num_threads(cpu_count)
        
        # Variables de entorno optimizadas
        os.environ['OMP_NUM_THREADS'] = str(cpu_count)
        os.environ['MKL_NUM_THREADS'] = str(cpu_count)
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Evitar warnings
        
        torch.set_float32_matmul_precision('high')
        logger.info(f"🔧 Optimizaciones configuradas: {cpu_count} threads")
    
    def load_latest_models(self):
        """Carga los modelos de última generación"""
        model_configs = [
            # Qwen2.5-VL models
            {
                "name": "qwen25_vl_7b",
                "dir": "./models/qwen25_vl_7b",
                "processor_class": Qwen2VLProcessor,
                "model_class": Qwen2VLForConditionalGeneration,
                "type": "qwen25",
                "specialty": "Estado del arte en comprensión visual multimodal",
                "trust_remote_code": True
            },
            {
                "name": "qwen25_vl_3b",
                "dir": "./models/qwen25_vl_3b",
                "processor_class": Qwen2VLProcessor,
                "model_class": Qwen2VLForConditionalGeneration,
                "type": "qwen25",
                "specialty": "Balance perfecto velocidad/calidad",
                "trust_remote_code": True
            },
            {
                "name": "qwen25_vl_72b_awq",
                "dir": "./models/qwen25_vl_72b_awq",
                "processor_class": Qwen2VLProcessor,
                "model_class": Qwen2VLForConditionalGeneration,
                "type": "qwen25",
                "specialty": "Máxima calidad posible con cuantización",
                "trust_remote_code": True
            },
            # PaliGemma models (Gemma 3 based)
            {
                "name": "paligemma_3b",
                "dir": "./models/paligemma_3b",
                "processor_class": PaliGemmaProcessor,
                "model_class": PaliGemmaForConditionalGeneration,
                "type": "paligemma",
                "specialty": "Excelente comprensión visual de Google",
                "trust_remote_code": False
            },
            {
                "name": "paligemma_3b_mix",
                "dir": "./models/paligemma_3b_mix",
                "processor_class": PaliGemmaProcessor,
                "model_class": PaliGemmaForConditionalGeneration,
                "type": "paligemma",
                "specialty": "Versión optimizada para múltiples tareas",
                "trust_remote_code": False
            }
        ]
        
        loaded_count = 0
        for config in model_configs:
            if os.path.exists(config["dir"]):
                try:
                    logger.info(f"📂 Cargando {config['name']}...")
                    
                    # Cargar procesador
                    if config["trust_remote_code"]:
                        processor = config["processor_class"].from_pretrained(
                            config["dir"],
                            trust_remote_code=True
                        )
                    else:
                        processor = config["processor_class"].from_pretrained(config["dir"])
                    
                    # Cargar modelo
                    model_kwargs = {
                        "torch_dtype": torch.float32,
                        "low_cpu_mem_usage": False,  # Tienes 32GB
                    }
                    
                    if config["trust_remote_code"]:
                        model_kwargs["trust_remote_code"] = True
                    
                    model = config["model_class"].from_pretrained(
                        config["dir"],
                        **model_kwargs
                    )
                    model.eval()
                    
                    # Guardar modelo
                    self.processors[config["name"]] = processor
                    self.models[config["name"]] = model
                    self.model_info[config["name"]] = {
                        "type": config["type"],
                        "specialty": config["specialty"],
                        "dir": config["dir"],
                        "trust_remote_code": config["trust_remote_code"]
                    }
                    
                    if not self.current_model:
                        self.current_model = config["name"]
                    
                    loaded_count += 1
                    logger.info(f"✅ {config['name']} cargado - {config['specialty']}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando {config['name']}: {str(e)}")
        
        if loaded_count == 0:
            logger.error("❌ No se pudo cargar ningún modelo de última generación")
            raise Exception("No hay modelos disponibles")
        
        logger.info(f"🎯 {loaded_count} modelo(s) de última generación cargado(s)")
        logger.info(f"🚀 Modelo activo: {self.current_model}")
    
    def generate_latest_analysis(self, image_data, analysis_type="figure_analysis", custom_prompt="", model_name=None, max_length=500):
        """
        Genera análisis con modelos de última generación
        """
        start_time = time.time()
        
        try:
            # Seleccionar modelo
            if model_name and model_name in self.models:
                active_model = model_name
            else:
                active_model = self.current_model
            
            model = self.models[active_model]
            processor = self.processors[active_model]
            model_type = self.model_info[active_model]["type"]
            
            # Procesar imagen
            if isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes)).convert('RGB')
            elif isinstance(image_data, bytes):
                image = Image.open(BytesIO(image_data)).convert('RGB')
            else:
                image = image_data.convert('RGB')
            
            # Preparar prompt según el modelo
            if custom_prompt:
                final_prompt = custom_prompt
            else:
                final_prompt = LATEST_ANALYSIS_PROMPTS.get(analysis_type, LATEST_ANALYSIS_PROMPTS["figure_analysis"])
            
            # Generar inputs según el tipo de modelo
            if model_type == "qwen25":
                # Qwen2.5-VL usa formato de chat
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image},
                            {"type": "text", "text": final_prompt}
                        ]
                    }
                ]
                
                # Aplicar template de chat
                text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = processor(text=[text], images=[image], return_tensors="pt")
                
            elif model_type == "paligemma":
                # PaliGemma usa formato directo
                inputs = processor(text=final_prompt, images=image, return_tensors="pt")
            
            else:
                # Formato genérico para otros modelos
                inputs = processor(text=final_prompt, images=image, return_tensors="pt")
            
            # Configuración de generación optimizada por modelo
            if model_type == "qwen25":
                generation_config = {
                    "max_new_tokens": max_length,
                    "do_sample": False,
                    "num_beams": 3,
                    "early_stopping": True,
                    "repetition_penalty": 1.1,
                    "temperature": 0.7,
                }
            elif model_type == "paligemma":
                generation_config = {
                    "max_new_tokens": max_length,
                    "do_sample": False,
                    "num_beams": 4,
                    "early_stopping": True,
                    "pad_token_id": processor.tokenizer.eos_token_id,
                }
            else:
                generation_config = {
                    "max_length": max_length,
                    "do_sample": False,
                    "num_beams": 3,
                    "early_stopping": True,
                }
            
            # Generar análisis
            logger.info(f"🔄 Generando análisis con {active_model}...")
            with torch.no_grad():
                generated_ids = model.generate(**inputs, **generation_config)
            
            # Decodificar según el modelo
            if model_type == "qwen25":
                # Para Qwen2.5-VL, extraer solo la respuesta nueva
                input_len = inputs["input_ids"].shape[1]
                generated_ids = generated_ids[:, input_len:]
                description = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            else:
                # Para PaliGemma y otros
                description = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                # Limpiar prompt si aparece en la respuesta
                if final_prompt in description:
                    description = description.replace(final_prompt, "").strip()
            
            processing_time = time.time() - start_time
            
            logger.info(f"⚡ Análisis completado en {processing_time:.2f}s")
            
            return {
                "description": description.strip(),
                "processing_time": processing_time,
                "model_used": active_model,
                "model_type": model_type,
                "model_specialty": self.model_info[active_model]["specialty"],
                "prompt_used": final_prompt,
                "words_count": len(description.split()),
                "generation": "2024_latest"
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando análisis: {str(e)}")
            raise
    
    def compare_latest_models(self, image_data, analysis_type="figure_analysis", max_models=3):
        """Compara resultados entre los modelos más nuevos"""
        results = {}
        total_time = 0
        
        # Priorizar modelos por calidad
        available_models = list(self.models.keys())
        
        # Ordenar por preferencia: Qwen2.5-VL > PaliGemma
        priority_order = []
        
        # Primero Qwen2.5-VL (mejores primero)
        for model in available_models:
            if "qwen25_vl_7b" in model:
                priority_order.insert(0, model)  # Mejor balance
            elif "qwen25" in model:
                priority_order.append(model)
        
        # Luego PaliGemma
        for model in available_models:
            if "paligemma" in model and model not in priority_order:
                priority_order.append(model)
        
        # Limitar número de modelos
        selected_models = priority_order[:max_models]
        
        for model_name in selected_models:
            try:
                logger.info(f"🔄 Comparando con {model_name}...")
                result = self.generate_latest_analysis(
                    image_data, analysis_type, "", model_name, 300
                )
                results[model_name] = result
                total_time += result['processing_time']
                
            except Exception as e:
                results[model_name] = {
                    'error': str(e),
                    'model_specialty': self.model_info.get(model_name, {}).get('specialty', 'Unknown')
                }
        
        return {
            'results': results,
            'total_time': total_time,
            'models_compared': len(selected_models),
            'comparison_type': 'latest_generation_2024'
        }

# Inicializar servidor
caption_server = LatestModelServer()

@app.route('/health', methods=['GET'])
def health_check():
    """Estado del servidor con modelos de última generación"""
    return jsonify({
        'status': 'ok',
        'available_models': list(caption_server.models.keys()),
        'current_model': caption_server.current_model,
        'model_info': caption_server.model_info,
        'available_analysis': list(LATEST_ANALYSIS_PROMPTS.keys()),
        'device': 'cpu_optimized',
        'hardware': 'AMD 6750XT + Ryzen 7 5700X + 32GB RAM',
        'server_type': 'latest_generation_2024',
        'models_generation': '2024_state_of_the_art'
    })

@app.route('/analyze_latest', methods=['POST'])
def analyze_latest():
    """Endpoint principal para análisis con modelos de última generación"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'Campo "image" requerido'}), 400
        
        image_data = data['image']
        analysis_type = data.get('analysis_type', 'figure_analysis')
        custom_prompt = data.get('custom_prompt', '')
        model_name = data.get('model', None)
        max_length = min(data.get('max_length', 500), 800)
        
        # Validar tipo de análisis
        if analysis_type not in LATEST_ANALYSIS_PROMPTS and not custom_prompt:
            return jsonify({
                'error': f'analysis_type inválido. Opciones: {list(LATEST_ANALYSIS_PROMPTS.keys())}'
            }), 400
        
        # Generar análisis
        result = caption_server.generate_latest_analysis(
            image_data, analysis_type, custom_prompt, model_name, max_length
        )
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logger.error(f"Error en /analyze_latest: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/compare_latest', methods=['POST'])
def compare_latest():
    """Compara análisis entre los modelos más nuevos"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'Campo "image" requerido'}), 400
        
        image_data = data['image']
        analysis_type = data.get('analysis_type', 'figure_analysis')
        max_models = min(data.get('max_models', 3), 5)
        
        # Realizar comparación
        comparison_result = caption_server.compare_latest_models(
            image_data, analysis_type, max_models
        )
        
        return jsonify({
            'success': True,
            **comparison_result
        })
        
    except Exception as e:
        logger.error(f"Error en /compare_latest: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/model_recommendations', methods=['POST'])
def model_recommendations():
    """Recomienda el mejor modelo para análisis específico"""
    try:
        data = request.get_json()
        analysis_type = data.get('analysis_type', 'figure_analysis')
        
        # Recomendaciones específicas para modelos de 2024
        recommendations = {
            'figure_analysis': {
                'primary': 'qwen25_vl_7b',
                'alternative': 'paligemma_3b_mix',
                'reason': 'Qwen2.5-VL-7B ofrece el mejor análisis de figuras humanas con tecnología 2024'
            },
            'emotional_state': {
                'primary': 'qwen25_vl_7b',
                'alternative': 'qwen25_vl_3b',
                'reason': 'Qwen2.5-VL es líder en comprensión emocional y psicológica'
            },
            'comprehensive_analysis': {
                'primary': 'qwen25_vl_72b_awq',
                'alternative': 'qwen25_vl_7b',
                'reason': 'El modelo 72B AWQ ofrece la máxima calidad posible'
            },
            'situational_context': {
                'primary': 'paligemma_3b_mix',
                'alternative': 'qwen25_vl_7b',
                'reason': 'PaliGemma excele en comprensión contextual y situacional'
            },
            'behavioral_analysis': {
                'primary': 'qwen25_vl_7b',
                'alternative': 'paligemma_3b',
                'reason': 'Qwen2.5-VL tiene superior comprensión de comportamientos'
            }
        }
        
        recommendation = recommendations.get(analysis_type, recommendations['figure_analysis'])
        
        # Verificar disponibilidad
        available_models = list(caption_server.models.keys())
        
        if recommendation['primary'] in available_models:
            best_model = recommendation['primary']
        elif recommendation['alternative'] in available_models:
            best_model = recommendation['alternative']
        else:
            best_model = available_models[0] if available_models else None
        
        return jsonify({
            'success': True,
            'recommended_model': best_model,
            'analysis_type': analysis_type,
            'reason': recommendation['reason'],
            'available_models': available_models,
            'generation': '2024_latest'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/latest_capabilities', methods=['GET'])
def latest_capabilities():
    """Muestra capacidades de los modelos de última generación"""
    capabilities = {}
    
    for model_name, info in caption_server.model_info.items():
        model_type = info['type']
        
        if model_type == 'qwen25':
            if '72b' in model_name:
                capabilities[model_name] = {
                    'specialty': info['specialty'],
                    'best_for': ['comprehensive_analysis', 'complex_reasoning', 'detailed_descriptions'],
                    'strengths': ['Máxima calidad', 'Razonamiento complejo', 'Análisis profundo'],
                    'type': 'Qwen2.5-VL Large (Estado del arte 2024)',
                    'generation': '2024-flagship'
                }
            else:
                capabilities[model_name] = {
                    'specialty': info['specialty'],
                    'best_for': ['figure_analysis', 'emotional_state', 'behavioral_analysis'],
                    'strengths': ['Comprensión visual avanzada', 'Análisis emocional', 'Balance calidad/velocidad'],
                    'type': 'Qwen2.5-VL (Estado del arte 2024)',
                    'generation': '2024-advanced'
                }
        elif model_type == 'paligemma':
            capabilities[model_name] = {
                'specialty': info['specialty'],
                'best_for': ['situational_context', 'visual_understanding', 'detailed_descriptions'],
                'strengths': ['Comprensión visual Google', 'Análisis contextual', 'Eficiencia computacional'],
                'type': 'PaliGemma - Google Research (Gemma 3 base)',
                'generation': '2024-google'
            }
    
    return jsonify({
        'latest_capabilities': capabilities,
        'total_models': len(capabilities),
        'generation': '2024_state_of_the_art',
        'note': 'Modelos de última generación optimizados para análisis de figuras humanas'
    })

@app.route('/switch_latest', methods=['POST'])
def switch_latest():
    """Cambiar modelo activo entre los más nuevos"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        
        if model_name in caption_server.models:
            caption_server.current_model = model_name
            model_info = caption_server.model_info[model_name]
            return jsonify({
                'success': True,
                'current_model': model_name,
                'model_specialty': model_info['specialty'],
                'model_type': model_info['type'],
                'generation': '2024_latest',
                'message': f'Modelo cambiado a {model_name} (generación 2024)'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Modelo {model_name} no disponible',
                'available_models': list(caption_server.models.keys())
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/benchmark_latest', methods=['POST'])
def benchmark_latest():
    """Benchmark de rendimiento de los modelos más nuevos"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'Campo "image" requerido'}), 400
        
        image_data = data['image']
        
        benchmark_results = {}
        
        # Probar cada modelo con el mismo prompt
        test_prompt = "Analyze this image focusing on any people, their emotions, and the situation"
        
        for model_name in caption_server.models.keys():
            try:
                start_time = time.time()
                
                result = caption_server.generate_latest_analysis(
                    image_data, 
                    custom_prompt=test_prompt,
                    model_name=model_name,
                    max_length=200
                )
                
                benchmark_results[model_name] = {
                    'processing_time': result['processing_time'],
                    'words_generated': result['words_count'],
                    'words_per_second': result['words_count'] / result['processing_time'],
                    'model_specialty': result['model_specialty'],
                    'success': True
                }
                
            except Exception as e:
                benchmark_results[model_name] = {
                    'error': str(e),
                    'success': False
                }
        
        return jsonify({
            'success': True,
            'benchmark_results': benchmark_results,
            'test_prompt': test_prompt,
            'generation': '2024_latest'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Servidor para MODELOS DE ÚLTIMA GENERACIÓN 2024")
    print("=" * 65)
    print("🎯 Gemma 3 (PaliGemma) + Qwen2.5-VL")
    print(f"🤖 Modelos cargados: {list(caption_server.models.keys())}")
    print(f"🎯 Modelo activo: {caption_server.current_model}")
    print("🌐 Endpoints especializados:")
    print("  - POST /analyze_latest - Análisis con modelos 2024")
    print("  - POST /compare_latest - Comparar modelos nuevos")
    print("  - POST /model_recommendations - Recomendaciones")
    print("  - GET  /latest_capabilities - Capacidades 2024")
    print("  - POST /benchmark_latest - Benchmark de rendimiento")
    print("  - POST /switch_latest - Cambiar modelo")
    print("=" * 65)
    print("💡 Modelos de última generación para análisis de figuras:")
    
    for model_name, info in caption_server.model_info.items():
        print(f"  🎯 {model_name}: {info['specialty']}")
    
    print("\n🔥 Estado del arte 2024 - Máxima calidad disponible")
    
    app.run(
        host='0.0.0.0',
        port=5004,  # Puerto nuevo para modelos 2024
        debug=False,
        threaded=True
    )