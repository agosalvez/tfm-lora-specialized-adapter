from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import os

# --- 1. Define las rutas y nombres ---
# Ruta donde guardaste tu adaptador LoRA entrenado.
# Ejemplo: "./mis_modelos/mi_lora_entrenado/"
lora_model_path = "./lora-phi4-magic1" 

# Identificador del modelo base que usaste para entrenar LoRA.
# ¡Debe ser EXACTAMENTE el mismo!
# Ejemplo: "mistralai/Mistral-7B-Instruct-v0.2"
base_model_id = "microsoft/Phi-4-mini-instruct" 

# --- 2. Cargar el Tokenizer del modelo base ---
print(f"Cargando el tokenizer para: {base_model_id}...")
tokenizer = AutoTokenizer.from_pretrained(base_model_id)
# Algunos modelos necesitan un token de padding explícito, especialmente para batch inference.
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token # O un token específico si lo tiene

# --- 3. Cargar el modelo base original ---
print(f"Cargando el modelo base: {base_model_id}...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        device_map="auto",          # Distribuye el modelo automáticamente en tu GPU/CPU
        torch_dtype=torch.bfloat16,  # Optimiza el uso de memoria y velocidad
        trust_remote_code=True      # Necesario para algunos modelos personalizados
    )
except Exception as e:
    print(f"Error al cargar en bfloat16: {e}. Intentando con float16...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
    except Exception as e:
        print(f"Error al cargar en float16: {e}. Intentando con load_in_4bit...")
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            device_map="auto",
            load_in_4bit=True, # Carga el modelo en 4-bit para ahorrar VRAM
            trust_remote_code=True
        )

print("Modelo base cargado.")

# --- 4. Cargar el adaptador LoRA y "pegarlo" al modelo base ---
print(f"Cargando el adaptador LoRA desde: {lora_model_path}...")
model = PeftModel.from_pretrained(model, lora_model_path)
print("Adaptador LoRA aplicado.")

# --- 5. Poner el modelo en modo de evaluación ---
model.eval()

print("\n--- ¡Modelo listo para la inferencia! ---")
print("Escribe tu pregunta y presiona Enter. Escribe 'salir' para terminar.")

# --- 6. Bucle para la inferencia interactiva ---
while True:
    user_input = input("\nTu pregunta: ")
    if user_input.lower() == 'salir':
        print("Saliendo del programa.")
        break
    
    # Prepara el prompt para el modelo Phi-4-mini-instruct
    # Asegúrate de usar el formato de instrucción que el modelo espera.
    # El modelo Phi-4-mini-instruct usa el formato de chat de Llama, por ejemplo:
    # "<s>[INST] {prompt} [/INST]"
    # Es crucial para que el modelo entienda tu instrucción correctamente.
    formatted_prompt = f"<s>[INST] {user_input} [/INST]"

    inputs = tokenizer(formatted_prompt, return_tensors="pt", padding=True).to(model.device)

    # --- 7. Generar la respuesta ---
    print("\nGenerando respuesta...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,    # Puedes ajustar esto según lo largas que quieras las respuestas
            num_beams=1,           # Para generación greedy simple
            do_sample=True,        # Para muestreo, si quieres diversidad
            temperature=0.7,       # Controla la aleatoriedad
            top_k=50,              # Considera los 50 tokens más probables
            top_p=0.95,            # Considera el subconjunto más pequeño de tokens cuya probabilidad acumulada es >= 0.95
            eos_token_id=tokenizer.eos_token_id, 
            pad_token_id=tokenizer.pad_token_id,
            # Añadir este parámetro puede ayudar a que el modelo no regenere el prompt en la salida
            # Aunque con el formato de instrucción, es menos común
            # return_full_text=False 
        )

    # Decodificar el texto generado y mostrarlo
    # Es importante decodificar solo la parte nueva generada por el modelo
    # Para ello, podemos calcular la longitud de la entrada original y cortar la salida.
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # En muchos modelos instruct, la salida incluye la pregunta.
    # Necesitamos encontrar el final de la instrucción y mostrar solo lo que sigue.
    # Para Phi-4-mini-instruct, la respuesta debería empezar después de "[/INST]"
    if "[/INST]" in generated_text:
        response_start = generated_text.find("[/INST]") + len("[/INST]")
        actual_response = generated_text[response_start:].strip()
    else:
        actual_response = generated_text.strip() # En caso de que el formato no sea el esperado

    print("\n--- Respuesta del Modelo ---")
    print(actual_response)
