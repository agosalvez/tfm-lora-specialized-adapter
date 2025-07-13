import os
import requests
from dotenv import load_dotenv
from rag import retrieve_relevant_chunks, MODEL_API_URL, AUTH_TOKEN

# === Preguntas de validación ===
questions = [
    "¿Cuál es la función de la mirada antes del pase secreto en una técnica mágica?",
    "¿Por qué se considera efectiva la técnica de “no mirar” durante una técnica oculta?",
    "Explica el papel de la “idea obnubilante” en el desvío de atención.",
    "¿Qué efecto tiene en los espectadores el cambio súbito de mirada en una actuación?",
    "¿Cómo se combinan la mirada y las palabras para reforzar el misdirection durante una técnica?"
]

# === Cargar token desde .env ===
load_dotenv()

# === Headers para la API ===
headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# === Ejecutar preguntas ===
results = []

for i, query in enumerate(questions, 1):
    chunks = retrieve_relevant_chunks(query)
    context = "\n\n".join(chunks)

    prompt = f"""
Contesta la siguiente pregunta utilizando el contexto del documento y tu conocimiento especializado.

### Contexto:
{context}

### Pregunta:
{query}

### Respuesta:
"""

    data = {"instruction": prompt.strip()}
    print(f"\n🔹 Pregunta {i}: {query}")
    response = requests.post(MODEL_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        content = response.json().get("respuesta", response.json())
        print(f"✅ Respuesta: {content}\n")
        results.append({"pregunta": query, "respuesta": content})
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        results.append({"pregunta": query, "error": response.text})

# === Guardar resultados (opcional)
import json
with open("rag_resultados.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n📝 Resultados guardados en rag_resultados.json")
