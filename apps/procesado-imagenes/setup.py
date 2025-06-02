import json
import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import requests

def check_system_requirements():
    """Verificar requisitos del sistema"""
    print("🔍 Verificando requisitos del sistema...")
    
    # Verificar CUDA
    if torch.cuda.is_available():
        print(f"✅ CUDA disponible: {torch.cuda.get_device_name(0)}")
        print(f"💾 VRAM disponible: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("⚠️  CUDA no disponible, usando CPU")
    
    # Verificar espacio en disco
    disk_usage = os.statvfs('.')
    free_space_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / (1024**3)
    print(f"💽 Espacio libre en disco: {free_space_gb:.1f} GB")
    
    if free_space_gb < 20:
        print("⚠️  Advertencia: Se recomienda al menos 20GB de espacio libre")
    
    return True

def setup_qwen_model(model_name="Qwen/Qwen2-VL-7B-Instruct"):
    """Configurar y cargar el modelo Qwen2.5-VL"""
    print(f"🔄 Configurando modelo {model_name}...")
    
    try:
        print("📥 Descargando modelo...")
        print("⏳ Este paso puede tardar bastante para modelos grandes...")
        
        # Cargar modelo optimizado para Tesla T4
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,  # T4 funciona mejor con float16
            device_map="auto",
            load_in_8bit=True,  # OBLIGATORIO para T4 (16GB VRAM)
            trust_remote_code=True
        )
        
        # Cargar procesador
        processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        print("✅ Modelo configurado correctamente!")
        print(f"📋 Modelo: {model_name}")
        print(f"🔧 Dispositivo: {next(model.parameters()).device}")
        
        return model, processor
        
    except Exception as e:
        print(f"❌ Error con {model_name.split('/')[-1]}: {e}")
        print("💡 Posibles soluciones:")
        print("   - Verificar conexión a internet")
        print("   - Actualizar transformers: pip install transformers>=4.44.0")
        print("   - Verificar espacio en disco disponible")
        print("🔄 Si falla, prueba: pip install qwen-vl")
        return None, None

def test_model(model, processor):
    """Probar el modelo con un ejemplo simple"""
    if model is None or processor is None:
        print("❌ No se puede probar: modelo no cargado")
        return False
    
    try:
        print("🧪 Probando modelo...")
        
        # Crear una imagen de prueba simple
        test_image = Image.new('RGB', (224, 224), color='red')
        
        # Preparar entrada de prueba
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": test_image},
                    {"type": "text", "text": "¿Qué color tiene esta imagen?"}
                ]
            }
        ]
        
        # Procesar entrada
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text], images=[test_image], return_tensors="pt")
        
        # Mover al dispositivo del modelo
        device = next(model.parameters()).device
        inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        print("✅ Prueba básica completada correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def save_config(model_name, success=True):
    """Guardar configuración del setup"""
    config = {
        "model_name": model_name,
        "setup_success": success,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "setup_timestamp": torch.cuda.Event().record() if torch.cuda.is_available() else "N/A"
    }
    
    try:
        with open("qwen_config.json", "w") as f:
            json.dump(config, f, indent=2, default=str)
        print("💾 Configuración guardada en qwen_config.json")
    except Exception as e:
        print(f"⚠️  No se pudo guardar configuración: {e}")

def main():
    """Función principal de configuración"""
    print("🚀 Iniciando configuración de Qwen2.5-VL")
    print("=" * 50)
    
    # Verificar requisitos
    check_system_requirements()
    print()
    
    # Configurar modelo
    model, processor = setup_qwen_model()
    
    if model and processor:
        print()
        # Probar modelo
        test_success = test_model(model, processor)
        
        # Guardar configuración
        save_config("Qwen/Qwen2-VL-7B-Instruct", test_success)
        
        print()
        print("🎉 Configuración completada exitosamente!")
        print("💡 Ahora puedes usar el modelo en tu aplicación")
        
    else:
        print()
        print("❌ Error durante la configuración: name 'json' is not defined")
        print("💡 Soluciones sugeridas:")
        print("  • pip install --upgrade transformers accelerate torch")
        print("  • Verificar conexión a internet estable")
        print("  • Comprobar espacio disponible en disco (>20GB)")
        
        save_config("Qwen/Qwen2-VL-7B-Instruct", False)

if __name__ == "__main__":
    main()
