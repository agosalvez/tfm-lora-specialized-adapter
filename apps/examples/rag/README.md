# Estructura del proyecto RAG

```
examples/
└── rag/
    ├── rag.py                  # Script principal que hace RAG y consulta el modelo
    ├── documento.md            # Documento Markdown del dominio
    ├── requirements.txt        # Dependencias necesarias para este módulo
    └── README.md               # Instrucciones de uso
```

---

## ✅ `examples/rag/requirements.txt`
```txt
sentence-transformers
faiss-cpu
markdown
beautifulsoup4
requests
```

---

## ✅ `examples/rag/rag.py`
```python
from sentence_transformers import SentenceTransformer
from markdown import markdown
from bs4 import BeautifulSoup
from pathlib import Path
import numpy as np
import faiss
import re
import requests

# === Configuración ===
DOCUMENT_PATH = "documento.md"
MODEL_API_URL = "http://localhost:5000/generate"  # Cambia esto por la IP real del modelo
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
    response = requests.post(MODEL_API_URL, json={"prompt": prompt})
    return response.json()

# === Ejemplo de uso ===
if __name__ == "__main__":
    query = input("Pregunta: ")
    result = ask_rag(query)
    print("\nRespuesta: ", result.get("generated_text", result))
```

---

## ✅ `examples/rag/README.md`
```markdown
# Sistema RAG con documento Markdown y API de modelo LoRA

Este ejemplo implementa un flujo completo RAG:
- Lee un documento en Markdown,
- Lo divide en chunks,
- Usa embeddings para indexarlo con FAISS,
- Recupera contexto relevante según una consulta,
- Envía el prompt generado a una API REST con el modelo adaptado.

## 📦 Requisitos
```bash
pip install -r requirements.txt
```

## 🚀 Ejecución
```bash
python rag.py
```

## ⚙️ Configura tu API
Edita la variable `MODEL_API_URL` dentro de `rag.py` para apuntar a la IP o dominio donde tengas desplegado tu modelo con LoRA.

---

## 🧠 Entrada esperada del modelo (API REST)
```json
{
  "prompt": "..."
}
```

## 🧠 Salida esperada del modelo
```json
{
  "generated_text": "..."
}
```
```
