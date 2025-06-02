#!/usr/bin/env python3
"""
Cliente universal para análisis de imágenes
Compatible con TODOS los servidores: básico, detallado, avanzado y última generación
"""

import base64
import requests
import json
from PIL import Image
import argparse
import os
import time

class UniversalImageClient:
    def __init__(self, server_url="http://localhost:5004"):
        self.server_url = server_url.rstrip('/')
        self.available_prompts = {}
        self.available_models = []
        self.server_type = "unknown"
        self.server_info = {}
        self.get_server_info()
    
    def get_server_info(self):
        """Obtiene información del servidor y detecta el tipo"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.server_type = data.get('server_type', data.get('models_generation', 'basic'))
                self.available_models = data.get('available_models', [])
                self.available_prompts = data.get('available_prompts', data.get('available_analysis', {}))
                self.server_info = data
                
                print(f"✅ Conectado: {self.server_type}")
                print(f"🤖 Modelos: {len(self.available_models)}")
                if 'generation' in data:
                    print(f"🔥 Generación: {data['generation']}")
            else:
                print(f"⚠️ Servidor responde con código: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ No se puede conectar al servidor")
            print("💡 Servidores disponibles:")
            print("   python server_latest.py    # Puerto 5004 (Gemma3 + Qwen2.5)")
            print("   python server_advanced.py  # Puerto 5003 (LLaVA + CogVLM)")
            print("   python server_detailed.py  # Puerto 5002 (BLIP2 detallado)")
            print("   python server_amd.py       # Puerto 5000 (Básico AMD)")
        except Exception as e:
            print(f"⚠️ Error conectando: {str(e)}")
    
    def image_to_base64(self, image_path):
        """Convierte imagen a base64"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return encoded_string
        except Exception as e:
            print(f"❌ Error leyendo imagen: {str(e)}")
            return None
    
    def analyze_image(self, image_path, analysis_type="figure_analysis", custom_prompt="", model=None, max_length=400):
        """
        Análisis universal que se adapta al tipo de servidor
        """
        if not os.path.exists(image_path):
            return {"error": "Archivo de imagen no encontrado"}
        
        image_base64 = self.image_to_base64(image_path)
        if not image_base64:
            return {"error": "No se pudo convertir la imagen"}
        
        data = {
            "image": image_base64,
            "max_length": max_length
        }
        
        if model:
            data["model"] = model
        
        # Adaptar datos según el tipo de servidor
        if custom_prompt:
            data["custom_prompt"] = custom_prompt
            data["prompt"] = custom_prompt  # Fallback para servidores básicos
        else:
            data["analysis_type"] = analysis_type
            data["prompt_type"] = analysis_type  # Para servidores detallados
            data["prompt"] = f"Analyze the figure in this image: {analysis_type}"  # Fallback básico
        
        # Intentar endpoints en orden de preferencia
        endpoints_to_try = [
            "/analyze_latest",    # Servidor última generación
            "/analyze_figure",    # Servidor avanzado
            "/caption_detailed",  # Servidor detallado
            "/caption"           # Servidor básico
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.post(
                    f"{self.server_url}{endpoint}",
                    json=data,
                    timeout=120
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    continue  # Probar siguiente endpoint
                else:
                    print(f"⚠️ Error {response.status_code} en {endpoint}")
                    continue
                    
            except Exception as e:
                print(f"⚠️ Error en {endpoint}: {str(e)}")
                continue
        
        return {"error": "No se pudo conectar con ningún endpoint del servidor"}
    
    def compare_models(self, image_path, analysis_type="figure_analysis", max_models=3):
        """
        Compara múltiples modelos (si el servidor lo soporta)
        """
        if not os.path.exists(image_path):
            return {"error": "Archivo de imagen no encontrado"}
        
        image_base64 = self.image_to_base64(image_path)
        if not image_base64:
            return {"error": "No se pudo convertir la imagen"}
        
        data = {
            "image": image_base64,
            "analysis_type": analysis_type,
            "max_models": max_models
        }
        
        # Intentar endpoints de comparación
        comparison_endpoints = [
            "/compare_latest",
            "/compare_models",
            "/caption_multi_prompt"
        ]
        
        for endpoint in comparison_endpoints:
            try:
                response = requests.post(
                    f"{self.server_url}{endpoint}",
                    json=data,
                    timeout=300
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    continue
                    
            except Exception as e:
                continue
        
        return {"error": "El servidor no soporta comparación de modelos"}
    
    def get_server_capabilities(self):
        """Obtiene las capacidades del servidor"""
        capability_endpoints = [
            "/latest_capabilities",
            "/model_capabilities", 
            "/prompts",
            "/models"
        ]
        
        capabilities = {}
        
        for endpoint in capability_endpoints:
            try:
                response = requests.get(f"{self.server_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    capabilities[endpoint.replace('/', '')] = data
            except:
                continue
        
        return capabilities
    
    def switch_model(self, model_name):
        """Cambia modelo activo"""
        switch_endpoints = [
            "/switch_latest",
            "/switch_model"
        ]
        
        for endpoint in switch_endpoints:
            try:
                response = requests.post(
                    f"{self.server_url}{endpoint}",
                    json={"model": model_name}
                )
                if response.status_code == 200:
                    return response.json()
            except:
                continue
        
        return {"error": "No se pudo cambiar el modelo"}
    
    def interactive_mode(self):
        """Modo interactivo universal"""
        print("🎯 CLIENTE UNIVERSAL - Análisis de Imágenes")
        print("=" * 65)
        
        # Verificar servidor
        if not self.check_server():
            return
        
        self.show_help()
        
        while True:
            try:
                user_input = input(f"\n🎯 [{self.server_type}] Comando: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'salir', 'q']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if not user_input:
                    continue
                
                # Procesar comandos
                self.process_command(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def process_command(self, user_input):
        """Procesa comandos del usuario"""
        parts = user_input.split(' ', 3)
        command = parts[0].lower()
        
        if command == 'help':
            self.show_help()
        
        elif command == 'status':
            self.show_server_status()
        
        elif command == 'info':
            self.show_server_info()
        
        elif command == 'models':
            self.show_available_models()
        
        elif command == 'capabilities':
            self.show_capabilities()
        
        elif command == 'switch' and len(parts) >= 2:
            model_name = parts[1]
            result = self.switch_model(model_name)
            if result.get('success'):
                print(f"✅ {result.get('message', 'Modelo cambiado')}")
            else:
                print(f"❌ {result.get('error', 'Error cambiando modelo')}")
        
        elif command == 'compare' and len(parts) >= 2:
            image_path = parts[1]
            analysis_type = parts[2] if len(parts) >= 3 else "figure_analysis"
            print(f"🔄 Comparando modelos: {image_path}")
            result = self.compare_models(image_path, analysis_type)
            self.display_comparison_result(result)
        
        elif command in ['figure', 'emotional', 'behavioral', 'situational', 'comprehensive'] and len(parts) >= 2:
            image_path = parts[1]
            model = parts[2] if len(parts) >= 3 else None
            
            analysis_map = {
                'figure': 'figure_analysis',
                'emotional': 'emotional_state', 
                'behavioral': 'behavioral_analysis',
                'situational': 'situational_context',
                'comprehensive': 'comprehensive_analysis'
            }
            
            analysis_type = analysis_map[command]
            print(f"🔍 Análisis {command}: {image_path}")
            result = self.analyze_image(image_path, analysis_type, model=model)
            self.display_analysis_result(result)
        
        elif command == 'custom' and len(parts) >= 3:
            image_path = parts[1]
            custom_prompt = parts[2]
            model = parts[3] if len(parts) >= 4 else None
            print(f"🎯 Análisis personalizado: {image_path}")
            result = self.analyze_image(image_path, custom_prompt=custom_prompt, model=model)
            self.display_analysis_result(result)
        
        elif command == 'test':
            self.run_test_analysis()
        
        else:
            # Análisis básico por defecto
            image_path = user_input
            print(f"📸 Análisis básico: {image_path}")
            result = self.analyze_image(image_path)
            self.display_analysis_result(result)
    
    def show_help(self):
        """Muestra ayuda adaptada al tipo de servidor"""
        print(f"\n📋 COMANDOS DISPONIBLES [{self.server_type}]:")
        print("=" * 55)
        print("📸 ANÁLISIS DE IMÁGENES:")
        print("  imagen.jpg                        - Análisis básico")
        print("  figure imagen.jpg [modelo]        - Análisis de figura")
        print("  emotional imagen.jpg [modelo]     - Estado emocional") 
        print("  behavioral imagen.jpg [modelo]    - Análisis conductual")
        print("  situational imagen.jpg [modelo]   - Contexto situacional")
        print("  comprehensive imagen.jpg [modelo] - Análisis completo")
        print("  custom imagen.jpg 'prompt' [modelo] - Prompt personalizado")
        print("  compare imagen.jpg [tipo]         - Comparar modelos")
        print()
        print("🤖 GESTIÓN:")
        print("  models         - Ver modelos disponibles")
        print("  switch modelo  - Cambiar modelo activo")
        print("  capabilities   - Ver capacidades del servidor")
        print()
        print("ℹ️  INFORMACIÓN:")
        print("  status         - Estado del servidor")
        print("  info           - Información detallada del servidor")
        print("  test           - Ejecutar análisis de prueba")
        print("  help           - Mostrar esta ayuda")
        print("  quit           - Salir")
        print("=" * 55)
        
        # Mostrar información específica del servidor
        if self.server_type in ["latest_generation_2024", "2024_state_of_the_art"]:
            print("🔥 SERVIDOR ÚLTIMA GENERACIÓN 2024:")
            print("  • Qwen2.5-VL + PaliGemma (Gemma 3)")
            print("  • Estado del arte en análisis de figuras")
        elif "advanced" in self.server_type:
            print("🚀 SERVIDOR AVANZADO:")
            print("  • LLaVA-Next + CogVLM + Qwen2-VL")
            print("  • Modelos especializados 2024")
        elif "detailed" in self.server_type:
            print("🎯 SERVIDOR DETALLADO:")
            print("  • BLIP2 optimizado + InstructBLIP")
        
        print("=" * 55)
    
    def check_server(self):
        """Verifica disponibilidad del servidor"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servidor activo: {self.server_url}")
                print(f"🔧 Tipo: {data.get('server_type', 'unknown')}")
                print(f"🤖 Modelos: {len(data.get('available_models', []))}")
                
                if 'hardware' in data:
                    print(f"📱 Hardware: {data['hardware']}")
                if 'generation' in data:
                    print(f"🔥 Generación: {data['generation']}")
                    
                return True
            else:
                print("❌ Servidor no responde correctamente")
                return False
        except:
            print("❌ No se puede conectar al servidor")
            print("💡 Servidores comunes:")
            print("   http://localhost:5004 - Última generación (Gemma3 + Qwen2.5)")
            print("   http://localhost:5003 - Avanzado (LLaVA + CogVLM)")
            print("   http://localhost:5002 - Detallado (BLIP2)")
            print("   http://localhost:5000 - Básico (AMD optimizado)")
            return False
    
    def show_server_status(self):
        """Muestra estado detallado del servidor"""
        try:
            response = requests.get(f"{self.server_url}/health")
            if response.status_code == 200:
                data = response.json()
                print("\n📊 ESTADO DEL SERVIDOR:")
                print("=" * 45)
                for key, value in data.items():
                    if key in ['available_models', 'model_info']:
                        print(f"🤖 {key}: {len(value) if isinstance(value, (list, dict)) else value}")
                    elif key == 'hardware':
                        print(f"📱 {key}: {value}")
                    elif key in ['server_type', 'generation', 'models_generation']:
                        print(f"🔥 {key}: {value}")
                    else:
                        print(f"   {key}: {value}")
        except Exception as e:
            print(f"❌ Error obteniendo estado: {str(e)}")
    
    def show_server_info(self):
        """Muestra información completa del servidor"""
        print(f"\n🔍 INFORMACIÓN COMPLETA DEL SERVIDOR:")
        print("=" * 50)
        print(f"🌐 URL: {self.server_url}")
        print(f"🔧 Tipo: {self.server_type}")
        print(f"🤖 Modelos disponibles: {len(self.available_models)}")
        
        if self.available_models:
            print("📋 Lista de modelos:")
            for model in self.available_models:
                print(f"   • {model}")
        
        if hasattr(self, 'server_info') and self.server_info:
            print(f"\n📊 Detalles técnicos:")
            for key, value in self.server_info.items():
                if key not in ['available_models', 'model_info']:
                    print(f"   {key}: {value}")
    
    def show_available_models(self):
        """Muestra modelos con detalles si están disponibles"""
        capabilities = self.get_server_capabilities()
        
        if 'latest_capabilities' in capabilities or 'model_capabilities' in capabilities:
            cap_key = 'latest_capabilities' if 'latest_capabilities' in capabilities else 'model_capabilities'
            model_caps = capabilities[cap_key].get('latest_capabilities', capabilities[cap_key].get('model_capabilities', {}))
            
            print("\n🤖 MODELOS DISPONIBLES:")
            print("=" * 50)
            for model, info in model_caps.items():
                print(f"🎯 {model}")
                print(f"   📋 {info.get('specialty', 'N/A')}")
                if 'best_for' in info:
                    print(f"   🎪 Mejor para: {', '.join(info['best_for'])}")
                if 'type' in info:
                    print(f"   🔧 Tipo: {info['type']}")
                print()
        else:
            if self.available_models:
                print(f"\n🤖 Modelos disponibles: {', '.join(self.available_models)}")
            else:
                print("❌ No se pudieron obtener los modelos")
    
    def show_capabilities(self):
        """Muestra capacidades del servidor"""
        capabilities = self.get_server_capabilities()
        
        print(f"\n🔧 CAPACIDADES DEL SERVIDOR [{self.server_type}]:")
        print("=" * 55)
        
        for endpoint, data in capabilities.items():
            print(f"📊 {endpoint.upper()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (list, dict)):
                        print(f"   {key}: {len(value)} elementos")
                    else:
                        print(f"   {key}: {value}")
            print()
    
    def run_test_analysis(self):
        """Ejecuta un análisis de prueba"""
        print("🧪 Ejecutando análisis de prueba...")
        
        # Crear imagen de prueba
        test_image = Image.new('RGB', (400, 400), color=(100, 150, 200))
        test_path = "test_image.jpg"
        test_image.save(test_path)
        
        try:
            print("📸 Analizando imagen de prueba...")
            result = self.analyze_image(test_path, "figure_analysis")
            
            print("📊 RESULTADO DE PRUEBA:")
            print("=" * 40)
            if result.get('success'):
                print(f"✅ Análisis exitoso")
                print(f"📝 Descripción: {result.get('description', 'N/A')[:100]}...")
                print(f"⚡ Tiempo: {result.get('processing_time', 0):.2f}s")
                print(f"🤖 Modelo: {result.get('model_used', 'N/A')}")
            else:
                print(f"❌ Error: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            print(f"❌ Error en prueba: {str(e)}")
        
        finally:
            # Limpiar archivo de prueba
            try:
                os.remove(test_path)
            except:
                pass
    
    def display_analysis_result(self, result):
        """Muestra resultado de análisis formateado"""
        print("=" * 70)
        if result.get('success'):
            description = result['description']
            print(f"📝 ANÁLISIS:")
            print(f"{description}")
            
            # Información adicional
            details = []
            if 'processing_time' in result:
                details.append(f"⚡ {result['processing_time']:.2f}s")
            if 'model_used' in result:
                details.append(f"🤖 {result['model_used']}")
            if 'words_count' in result:
                details.append(f"📊 {result['words_count']} palabras")
            if 'generation' in result:
                details.append(f"🔥 {result['generation']}")
            
            if details:
                print(f"\n{' | '.join(details)}")
                
        else:
            print(f"❌ Error: {result.get('error', 'Error desconocido')}")
        print("=" * 70)
    
    def display_comparison_result(self, result):
        """Muestra comparación entre modelos"""
        print("=" * 70)
        if result.get('success'):
            results = result.get('results', {})
            print(f"🔄 COMPARACIÓN DE MODELOS ({len(results)} modelos):")
            
            for model_name, model_result in results.items():
                print(f"\n🤖 {model_name.upper()}:")
                print("-" * 45)
                if 'error' in model_result:
                    print(f"❌ Error: {model_result['error']}")
                else:
                    description = model_result.get('description', '')
                    print(f"{description}")
                    
                    details = []
                    if 'processing_time' in model_result:
                        details.append(f"⚡ {model_result['processing_time']:.1f}s")
                    if 'model_specialty' in model_result:
                        details.append(f"🎯 {model_result['model_specialty']}")
                    
                    if details:
                        print(f"   {' | '.join(details)}")
            
            if 'total_time' in result:
                print(f"\n⏱️ Tiempo total: {result['total_time']:.2f}s")
        else:
            print(f"❌ Error: {result.get('error', 'Error desconocido')}")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Cliente universal para análisis de imágenes')
    parser.add_argument('--server', default='http://localhost:5004',
                       help='URL del servidor')
    parser.add_argument('--image', help='Ruta de la imagen a analizar')
    parser.add_argument('--analysis', choices=[
        'figure_analysis', 'emotional_state', 'behavioral_analysis', 
        'situational_context', 'comprehensive_analysis'
    ], default='figure_analysis', help='Tipo de análisis')
    parser.add_argument('--custom-prompt', help='Prompt personalizado')
    parser.add_argument('--model', help='Modelo específico a usar')
    parser.add_argument('--compare', action='store_true', help='Comparar múltiples modelos')
    parser.add_argument('--interactive', action='store_true', help='Modo interactivo')
    parser.add_argument('--max-length', type=int, default=400, help='Longitud máxima')
    parser.add_argument('--test', action='store_true', help='Ejecutar análisis de prueba')
    
    args = parser.parse_args()
    
    client = UniversalImageClient(args.server)
    
    if args.interactive:
        client.interactive_mode()
        return
    
    if args.test:
        client.run_test_analysis()
        return
    
    if not args.image:
        print("❌ Se requiere --image, --interactive o --test")
        print("💡 Ejemplos:")
        print("  python client.py --interactive")
        print("  python client.py --image foto.jpg --analysis emotional_state")
        print("  python client.py --image foto.jpg --compare")
        print("  python client.py --test")
        return
    
    print(f"🔍 Analizando imagen: {args.image}")
    
    if args.compare:
        result = client.compare_models(args.image, args.analysis)
        client.display_comparison_result(result)
    else:
        result = client.analyze_image(
            args.image,
            analysis_type=args.analysis,
            custom_prompt=args.custom_prompt or "",
            model=args.model,
            max_length=args.max_length
        )
        client.display_analysis_result(result)

if __name__ == '__main__':
    main()