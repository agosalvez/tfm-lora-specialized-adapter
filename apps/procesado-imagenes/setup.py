#!/usr/bin/env python3
"""
Setup para Gemma 3 y Qwen2.5-VL
Modelos de última generación para análisis avanzado de imágenes
"""

import os
import torch
from transformers import (
    AutoProcessor, AutoModelForCausalLM,
    Qwen2VLForConditionalGeneration, Qwen2VLProcessor,
    PaliGemmaProcessor, PaliGemmaForConditionalGeneration
)
from PIL import Image
import requests
from io import BytesIO

def setup_latest_models():
    """Configura Gemma 3 y Qwen2.5-VL para tu hardware"""
    print("🚀 Configurando modelos de ÚLTIMA GENERACIÓN")
    print("=" * 65)
    print("🎯 Gemma 3 + Qwen2.5-VL para análisis avanzado de figuras")
    print("🔧 Optimizado para: AMD 6750XT + Ryzen 7 5700X + 32GB RAM")
    print("=" * 65)
    
    latest_models = [
        {
            "name": "Qwen2.5-VL-7B",
            "hf_name": "Qwen/Qwen2.5-VL-7B-Instruct",
            "processor": Qwen2VLProcessor,
            "model": Qwen2VLForConditionalGeneration,
            "dir": "./models/qwen25_vl_7b",
            "description": "Qwen2.5-VL - Última versión mejorada",
            "ram_needed": "12-18GB",
            "specialty": "Análisis multimodal avanzado con mejor comprensión",
            "release": "2024 - Estado del arte"
        },
        {
            "name": "Qwen2.5-VL-3B",
            "hf_name": "Qwen/Qwen2.5-VL-3B-Instruct", 
            "processor": Qwen2VLProcessor,
            "model": Qwen2VLForConditionalGeneration,
            "dir": "./models/qwen25_vl_3b",
            "description": "Qwen2.5-VL 3B - Versión más eficiente",
            "ram_needed": "6-12GB",
            "specialty": "Balance perfecto entre velocidad y calidad",
            "release": "2024 - Optimizado"
        },
        {
            "name": "PaliGemma-3B",
            "hf_name": "google/paligemma-3b-pt-448",
            "processor": PaliGemmaProcessor,
            "model": PaliGemmaForConditionalGeneration,
            "dir": "./models/paligemma_3b",
            "description": "PaliGemma 3B - Basado en Gemma de Google",
            "ram_needed": "8-14GB",
            "specialty": "Excelente para análisis detallado y comprensión visual",
            "release": "2024 - Google Research"
        },
        {
            "name": "PaliGemma-3B-Mix",
            "hf_name": "google/paligemma-3b-mix-448",
            "processor": PaliGemmaProcessor,
            "model": PaliGemmaForConditionalGeneration,
            "dir": "./models/paligemma_3b_mix",
            "description": "PaliGemma 3B Mix - Entrenamiento mejorado",
            "ram_needed": "8-14GB", 
            "specialty": "Versión optimizada para múltiples tareas visuales",
            "release": "2024 - Versión mejorada"
        },
        {
            "name": "Qwen2.5-VL-72B-AWQ",
            "hf_name": "Qwen/Qwen2.5-VL-72B-Instruct-AWQ",
            "processor": Qwen2VLProcessor,
            "model": Qwen2VLForConditionalGeneration,
            "dir": "./models/qwen25_vl_72b_awq",
            "description": "Qwen2.5-VL 72B AWQ - Modelo gigante cuantizado",
            "ram_needed": "24-32GB",
            "specialty": "Máxima calidad posible con cuantización AWQ",
            "release": "2024 - Flagship model"
        }
    ]
    
    print("🎯 Modelos disponibles:")
    for i, model in enumerate(latest_models, 1):
        print(f"  {i}. {model['name']}")
        print(f"     📋 {model['description']}")
        print(f"     🎪 {model['specialty']}")
        print(f"     💾 RAM: {model['ram_needed']}")
        print(f"     📅 {model['release']}")
        print()
    
    print("💡 Recomendaciones para tu caso:")
    print("   🥇 Qwen2.5-VL-7B - Mejor balance calidad/velocidad")
    print("   🥈 PaliGemma-3B-Mix - Excelente para figuras humanas")
    print("   🥉 Qwen2.5-VL-72B-AWQ - Máxima calidad (usa toda tu RAM)")
    print()
    
    # Selección interactiva
    choice = input("¿Qué modelo(s) prefieres? (1-5, múltiples separados por coma, o 'recommended'): ").strip()
    
    if choice.lower() == 'recommended':
        selected_models = [latest_models[0], latest_models[2]]  # Qwen2.5-VL-7B + PaliGemma
        print("✨ Seleccionados modelos recomendados: Qwen2.5-VL-7B + PaliGemma-3B-Mix")
    elif ',' in choice:
        indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip().isdigit()]
        selected_models = [latest_models[i] for i in indices if 0 <= i < len(latest_models)]
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(latest_models):
            selected_models = [latest_models[idx]]
        else:
            print("⚠️ Selección inválida, usando Qwen2.5-VL-7B")
            selected_models = [latest_models[0]]
    else:
        print("⚠️ Selección inválida, usando modelos recomendados")
        selected_models = [latest_models[0], latest_models[2]]
    
    for model_config in selected_models:
        download_latest_model(model_config)

def download_latest_model(config):
    """Descarga un modelo de última generación"""
    print(f"\n📥 Descargando {config['name']}...")
    print(f"📁 Directorio: {config['dir']}")
    print(f"🎯 Especialidad: {config['specialty']}")
    print(f"⏰ Esto puede tardar 10-30 minutos dependiendo del modelo...")
    
    try:
        os.makedirs(config['dir'], exist_ok=True)
        
        # Configuraciones específicas por modelo
        model_kwargs = {
            "torch_dtype": torch.float32,
            "low_cpu_mem_usage": False,  # Tienes 32GB
            "device_map": None,          # CPU
        }
        
        # Configuraciones especiales
        if "qwen" in config['name'].lower():
            print("  🔧 Configurando Qwen2.5-VL...")
            model_kwargs.update({
                "trust_remote_code": True,
                "attn_implementation": "eager",  # Mejor compatibilidad CPU
            })
        elif "paligemma" in config['name'].lower() or "gemma" in config['name'].lower():
            print("  🔧 Configurando PaliGemma...")
            model_kwargs.update({
                "revision": "bfloat16",  # Usar versión optimizada
            })
        
        # Descargar procesador
        print("  📥 Descargando procesador...")
        if "qwen" in config['name'].lower():
            processor = config['processor'].from_pretrained(
                config['hf_name'],
                trust_remote_code=True
            )
        else:
            processor = config['processor'].from_pretrained(config['hf_name'])
        
        # Descargar modelo
        print("  📥 Descargando modelo...")
        print("      ⏳ Este paso puede tardar bastante para modelos grandes...")
        
        if "qwen" in config['name'].lower():
            model = config['model'].from_pretrained(
                config['hf_name'],
                trust_remote_code=True,
                **model_kwargs
            )
        else:
            model = config['model'].from_pretrained(
                config['hf_name'],
                **model_kwargs
            )
        
        # Guardar localmente
        print("  💾 Guardando modelo...")
        processor.save_pretrained(config['dir'])
        model.save_pretrained(config['dir'])
        
        # Crear configuración
        create_latest_model_config(config)
        
        # Probar modelo
        test_latest_model(processor, model, config)
        
        print(f"  ✅ {config['name']} instalado correctamente!")
        
    except Exception as e:
        print(f"  ❌ Error con {config['name']}: {str(e)}")
        print(f"  💡 Posibles soluciones:")
        print(f"     - Verificar conexión a internet")
        print(f"     - Actualizar transformers: pip install transformers>=4.44.0")
        print(f"     - Verificar espacio en disco disponible")
        
        # Intentar modelo alternativo más pequeño
        if "72b" in config['name'].lower():
            print(f"  🔄 Modelo muy grande, prueba la versión 7B o 3B")
        elif "qwen" in config['name'].lower():
            print(f"  🔄 Si falla, prueba: pip install qwen-vl")

def create_latest_model_config(config):
    """Crea archivo de configuración para modelos nuevos"""
    config_content = f"""# Configuración para {config['name']}
MODEL_NAME={config['name']}
HF_NAME={config['hf_name']}
MODEL_DIR={config['dir']}
SPECIALTY={config['specialty']}
RAM_NEEDED={config['ram_needed']}
RELEASE={config['release']}
PROCESSOR_CLASS={config['processor'].__name__}
MODEL_CLASS={config['model'].__name__}

# Configuraciones especiales
TRUST_REMOTE_CODE={"true" if "qwen" in config['name'].lower() else "false"}
ATTN_IMPLEMENTATION=eager
TORCH_DTYPE=float32
"""
    
    config_file = os.path.join(config['dir'], "model_info.txt")
    with open(config_file, "w") as f:
        f.write(config_content)
    
    print(f"  📄 Configuración guardada en {config_file}")

def test_latest_model(processor, model, config):
    """Prueba los modelos de última generación"""
    try:
        print(f"  🧪 Probando {config['name']}...")
        
        # Crear imagen de prueba (evitar descargas que puedan fallar)
        image = Image.new('RGB', (448, 448), color=(100, 150, 200))
        print("    🖼️ Usando imagen de prueba generada")
        
        # Prompts específicos según el modelo
        if "qwen" in config['name'].lower():
            # Qwen2.5-VL usa formato de chat
            messages = [
                {
                    "role": "user", 
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": "Analyze this image and describe what you see, focusing on any people, their emotions, and the overall situation."}
                    ]
                }
            ]
            
            # Aplicar template de chat
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[text], images=[image], return_tensors="pt")
            
        elif "paligemma" in config['name'].lower():
            # PaliGemma usa formato directo
            prompt = "describe en detalle"
            inputs = processor(text=prompt, images=image, return_tensors="pt")
        
        else:
            # Formato genérico
            prompt = "Describe this image in detail"
            inputs = processor(text=prompt, images=image, return_tensors="pt")
        
        # Generar respuesta
        print("    ⚡ Generando descripción de prueba...")
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=50,  # Limitado para la prueba
                num_beams=2,
                early_stopping=True,
                do_sample=False
            )
        
        # Decodificar según el modelo
        if "qwen" in config['name'].lower():
            # Para Qwen, extraer solo la parte nueva
            input_len = inputs["input_ids"].shape[1]
            generated_ids = generated_ids[:, input_len:]
            description = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        else:
            # Para otros modelos
            description = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        print(f"    📝 Respuesta: {description[:100]}...")
        print(f"    ✅ {config['name']} funcionando correctamente")
        
    except Exception as e:
        print(f"    ⚠️ Error en prueba: {str(e)}")
        print(f"    💡 El modelo se instaló pero la prueba falló. Esto es normal para algunos modelos nuevos.")

def create_latest_prompts():
    """Crea prompts optimizados para Gemma 3 y Qwen2.5-VL"""
    latest_prompts = {
        # Prompts para Qwen2.5-VL (formato chat)
        "qwen25_figure_analysis": {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "Analyze the main human figure in this image. Provide a detailed description of their physical appearance, emotional state, body language, clothing, and the situation they find themselves in. Pay attention to facial expressions, posture, and any contextual clues about their circumstances."}
            ]
        },
        
        "qwen25_emotional_deep": {
            "role": "user", 
            "content": [
                {"type": "image"},
                {"type": "text", "text": "Focus deeply on the emotional and psychological aspects of the person in this image. What emotions are visible? What does their body language suggest about their mental state? What situation might have led to this emotional expression?"}
            ]
        },
        
        "qwen25_comprehensive": {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "Provide the most comprehensive analysis possible of this image, focusing particularly on any human subjects. Include physical appearance, emotional state, activities, environment, clothing, facial expressions, body language, and any contextual information that helps understand the scene and the person's situation."}
            ]
        },
        
        # Prompts para PaliGemma (formato directo)
        "paligemma_detailed": "Describe en gran detalle esta imagen, enfocándote en las personas, sus emociones, actividades y el contexto de la situación",
        
        "paligemma_figure": "Analiza la figura principal en esta imagen: apariencia física, expresión facial, lenguaje corporal, ropa y situación",
        
        "paligemma_emotional": "Describe el estado emocional y psicológico de la persona en esta imagen, incluyendo expresiones faciales y lenguaje corporal",
        
        # Prompts genéricos optimizados para modelos nuevos
        "latest_comprehensive": "Provide an extremely detailed and comprehensive analysis of this image, with special focus on any human figures, their emotional states, activities, and the overall context of the scene.",
        
        "latest_figure_focus": "Focus specifically on analyzing any human figures in this image. Describe their appearance, emotions, actions, and the situation they appear to be in.",
        
        "latest_situational": "Analyze the situation depicted in this image. What is happening? Who are the people involved? What is the context and what might have led to this moment?"
    }
    
    # Guardar prompts
    with open("latest_prompts.py", "w", encoding="utf-8") as f:
        f.write("# Prompts optimizados para Gemma 3 y Qwen2.5-VL\n\n")
        f.write("import json\n\n")
        f.write("LATEST_PROMPTS = {\n")
        
        for key, prompt in latest_prompts.items():
            if isinstance(prompt, dict):
                # Para prompts de chat (Qwen)
                f.write(f'    "{key}": {json.dumps(prompt, ensure_ascii=False, indent=8)},\n\n')
            else:
                # Para prompts de texto directo
                f.write(f'    "{key}": """{prompt}""",\n\n')
        
        f.write("}\n\n")
        
        f.write("""
def get_qwen25_prompt(prompt_type, custom_text=""):
    \"\"\"Genera prompt para Qwen2.5-VL en formato chat\"\"\"
    base_prompts = {
        'figure': LATEST_PROMPTS['qwen25_figure_analysis'],
        'emotional': LATEST_PROMPTS['qwen25_emotional_deep'],
        'comprehensive': LATEST_PROMPTS['qwen25_comprehensive']
    }
    
    if custom_text:
        return {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": custom_text}
            ]
        }
    
    return base_prompts.get(prompt_type, base_prompts['figure'])

def get_paligemma_prompt(prompt_type, custom_text=""):
    \"\"\"Genera prompt para PaliGemma\"\"\"
    base_prompts = {
        'figure': LATEST_PROMPTS['paligemma_figure'],
        'emotional': LATEST_PROMPTS['paligemma_emotional'],
        'detailed': LATEST_PROMPTS['paligemma_detailed']
    }
    
    if custom_text:
        return custom_text
    
    return base_prompts.get(prompt_type, base_prompts['detailed'])

# Ejemplo de uso:
# from latest_prompts import get_qwen25_prompt, get_paligemma_prompt
# qwen_prompt = get_qwen25_prompt('figure')
# gemma_prompt = get_paligemma_prompt('emotional')
""")
    
    print("📚 Prompts optimizados guardados en 'latest_prompts.py'")

if __name__ == "__main__":
    print("🎯 Setup para MODELOS DE ÚLTIMA GENERACIÓN")
    print("🔧 Gemma 3 (PaliGemma) + Qwen2.5-VL")
    print("💻 Hardware: AMD 6750XT + Ryzen 7 5700X + 32GB RAM")
    print("=" * 70)
    
    try:
        setup_latest_models()
        create_latest_prompts()
        
        print("\n🎉 ¡Configuración de modelos de última generación completada!")
        print("📋 Próximos pasos:")
        print("  1. Usar server_latest.py para cargar estos modelos")
        print("  2. Probar con client_complete.py")
        print("  3. Experimentar con latest_prompts.py")
        
        print("\n💡 Modelos recomendados para análisis de figuras:")
        print("  🥇 Qwen2.5-VL-7B - Estado del arte en comprensión visual")
        print("  🥈 PaliGemma-3B-Mix - Excelente de Google Research")
        print("  🥉 Qwen2.5-VL-72B-AWQ - Máxima calidad posible")
        
        print("\n⚠️ Nota importante:")
        print("  Estos son modelos muy nuevos (2024). Si alguno falla:")
        print("  • Actualiza transformers: pip install transformers>=4.44.0")
        print("  • Verifica dependencias: pip install qwen-vl accelerate")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {str(e)}")
        print("💡 Soluciones sugeridas:")
        print("  • pip install --upgrade transformers accelerate torch")
        print("  • Verificar conexión a internet estable")
        print("  • Comprobar espacio disponible en disco (>20GB)")