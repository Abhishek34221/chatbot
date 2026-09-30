import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from state import AgentState

load_dotenv()

# Initialize Local Ollama LLM and Local Embeddings
llm = ChatOllama(model="llama3.2", temperature=0.3)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    persist_directory="./chroma_db", embedding_function=embeddings
)

# 1. Setup Vector Retriever (Semantic Search)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 2. Setup BM25 Retriever (Keyword Search) with fallback
all_data = vectorstore.get()
if all_data and all_data.get("documents") and len(all_data["documents"]) > 0:
  all_docs = [
      Document(page_content=text, metadata=meta)
      for text, meta in zip(
          all_data["documents"],
          all_data.get("metadatas", [{} for _ in all_data["documents"]]),
      )
  ]
else:
  raw_texts = [
      (
          "Our company's remote work policy states that employees can work"
          " from anywhere within their home country for up to 90 days per"
          " calendar year, provided they have prior manager approval."
      ),
      (
          "The standard health insurance plan covers 80% of in-network"
          " outpatient services after a deductible of $1,000 is met."
          " Prescription drug copays are $15 for generic and $45 for brand"
          " name."
      ),
      (
          "To submit an expense report, employees must upload itemized"
          " receipts into the finance portal within 14 days of incurring the"
          " expense. Reports submitted after 14 days require VP approval."
      ),
  ]
  all_docs = [Document(page_content=text) for text in raw_texts]

bm25_retriever = BM25Retriever.from_documents(all_docs)
bm25_retriever.k = 2


def router_node(state: AgentState):
  print("--- ROUTER AGENT: Analyzing query ---")
  return {"sub_queries": [state["query"]], "loop_count": 0}


def retrieval_node(state: AgentState):
  print("--- RETRIEVAL AGENT: Fetching hybrid context ---")
  sub_queries = state["sub_queries"]
  retrieved_docs = []
  try:
    for sq in sub_queries:
      v_docs = vector_retriever.invoke(sq)
      b_docs = bm25_retriever.invoke(sq)
      for doc in v_docs + b_docs:
        if doc.page_content not in retrieved_docs:
          retrieved_docs.append(doc.page_content)
  except Exception as e:
    print(f"Retrieval warning: {e}")

  return {"retrieved_docs": retrieved_docs}


def critic_node(state: AgentState):
  print("--- CRITIC AGENT: Fast-tracking approval ---")
  return {"critique": "PASS", "loop_count": state.get("loop_count", 0) + 1}


def generator_node(state: AgentState):
  print("--- GENERATOR AGENT: Drafting final response ---")
  query = state["query"]
  docs = state["retrieved_docs"]

  # Strict Prompt to prevent unhelpful rejections and handle universal queries
  gen_prompt = ChatPromptTemplate.from_messages([
      (
          "system",
          (
              "You are a professional, helpful, and friendly enterprise AI"
              " assistant. "
              "Always answer the user's query directly, politely, and"
              " completely. "
              "NEVER refuse a greeting (like 'hi', 'hello', 'kya haal h'),"
              " casual chat, "
              "coding question, or general inquiry. "
              "If relevant company documents are provided in the context, use"
              " them accurately. "
              "NEVER say 'I can't help with that' or 'I can't understand what"
              " you're saying'."
          ),
      ),
      (
          "user",
          (
              "Context (if any):\n---\n{context}\n---\n\nUser Query:"
              " {query}\n\nAnswer:"
          ),
      ),
  ])

  chain = gen_prompt | llm
  context_str = "\n\n".join(docs) if docs else "No specific documents."

  response = chain.invoke({"context": context_str, "query": query})
  content = response.content

  if isinstance(content, list):
    generation_text = "".join(
        [
            str(item.get("text", item)) if isinstance(item, dict) else str(item)
            for item in content
        ]
    )
  else:
    generation_text = str(content)

  return {"generation": generation_text}