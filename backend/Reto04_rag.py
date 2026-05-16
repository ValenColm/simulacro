# Reto04-rag.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# URL que vamos a indexar — documentada aquí
# Elegimos créditos de Bancolombia porque tiene información
# relevante para usuarios financieros de FinBot
URL = "https://www.bancolombia.com/personas/productos/creditos"

# =============================================================================
# Fase 1 — Ingestión (corre una sola vez al arrancar)
# =============================================================================

def construir_base_vectorial():
    # 1. Carga el contenido de la URL con WebBaseLoader
    loader = WebBaseLoader(URL)
    documentos = loader.load()

    # 2. Divide el texto en chunks con overlap
    #    chunk_size=500, chunk_overlap=50
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documentos)

    # 3. Genera embeddings con OpenAIEmbeddings
    embeddings = OpenAIEmbeddings()

    # 4. Guarda en FAISS y retorna el vectorstore
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

# =============================================================================
# Fase 2 — Consulta (retorna contexto crudo)
# =============================================================================

def consultar_rag(pregunta: str, vectorstore) -> str:
    # 1. Busca los 3 chunks más relevantes en el vectorstore
    docs_relevantes = vectorstore.similarity_search(pregunta, k=3)

    # 2. Une el texto de los chunks como contexto
    contexto = "\n\n".join(doc.page_content for doc in docs_relevantes)

    # 3. Retorna el contexto para que el agente lo use
    return contexto

# =============================================================================
# Fase 3 — Respuesta (RAG completo: recuperación + generación)
# =============================================================================

def responder_rag(pregunta: str, vectorstore) -> str:
    # 1. Recupera el contexto relevante
    contexto = consultar_rag(pregunta, vectorstore)

    # 2. Construye el prompt con el contexto
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = [
        SystemMessage(content=(
            """Eres FinBot, el asistente virtual oficial de FinBot, una fintech
que opera en Colombia y Estados Unidos. Tienes acceso a información de la web
de productos financieros que se te provee como contexto.

Instrucciones:
- Responde SIEMPRE en el idioma del usuario.
- Usa el contexto provisto para responder la pregunta.
- Si el contexto no contiene la información exacta, responde con lo más cercano
  que encuentres y aclara que la información puede variar.
- NUNCA apliques restricciones de dominio — el contexto ya garantiza relevancia.
- Mantén el tono formal y profesional de FinBot.

Contexto de la web de Bancolombia (productos/créditos):
""" + contexto
        )),
        HumanMessage(content=pregunta)
    ]

    # 3. Genera y retorna la respuesta coherente
    respuesta = llm.invoke(messages)
    return respuesta.content

# =============================================================================
# Prueba
# =============================================================================
if __name__ == "__main__":
    print("Construyendo base vectorial...")
    vs = construir_base_vectorial()
    print("\n✅ Base lista. Escribe tu pregunta (o 'salir' para terminar)\n")

    while True:
        pregunta = input("Tu pregunta: ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue
        print("-" * 50)
        respuesta = responder_rag(pregunta, vs)
        print(respuesta)
        print("-" * 50 + "\n")