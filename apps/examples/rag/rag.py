# examples/rag/rag.py

from sentence_transformers import SentenceTransformer
from markdown import markdown
from bs4 import BeautifulSoup
from pathlib import Path
import numpy as np
import faiss
import re
import requests
import os
from dotenv import load_dotenv

# === Cargar token desde .env ===
load_dotenv()
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

# === Configuración ===
DOCUMENT_PATH = "documento.md"
MODEL_API_URL = "http://35.233.84.123:8000/generate"
CHUNK_SIZE = 200
TOP_K = 3

# === Cargar y chunkear el documento ===
def load_and_chunk_markdown(path, chunk_size=CHUNK_SIZE):
    text = Path(path).read_text(encoding='utf-8')
    html = markdown(text)
    soup = BeautifulSoup(html, 'html.parser')
    plain_text = soup.get_text()
    paragraphs = [p.strip() for p in re.split(r'\n+', plain_text) if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) < chunk_size:
            current += " " + p
        else:
            chunks.append(current.strip())
            current = p
    if current:
        chunks.append(current.strip())
    return chunks

# === Crear embeddings e indexar con FAISS ===
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chunks = load_and_chunk_markdown(DOCUMENT_PATH)
embeddings = embedding_model.encode(chunks, convert_to_numpy=True)
dim = embeddings.shape[1]
faiss_index = faiss.IndexFlatL2(dim)
faiss_index.add(embeddings)

# === Recuperar chunks relevantes ===
def retrieve_relevant_chunks(query, top_k=TOP_K):
    query_vec = embedding_model.encode([query])
    distances, indices = faiss_index.search(query_vec, top_k)
    return [chunks[i] for i in indices[0]]

# === Enviar al modelo vía API ===
def ask_rag(query):
    relevant_chunks = retrieve_relevant_chunks(query)
    context = "\n\n".join(relevant_chunks)

    prompt = f"""
Contesta la siguiente pregunta utilizando el contexto del documento y tu conocimiento especializado.

### Contexto:
{context}

### Pregunta:
{query}

### Respuesta:
"""

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "instruction": prompt.strip()
    }

    response = requests.post(MODEL_API_URL, headers=headers, json=data)

    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        print(f"❌ Error {response.status_code} - {response.text}")
        return {"error": response.json()}

# === Ejemplo de uso ===
if __name__ == "__main__":
    query = input("Pregunta: ")
    result = ask_rag(query)
    print("\nRespuesta:", result.get("respuesta", result))
