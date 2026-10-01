import os
import traceback
from agents import critic_node, generator_node, retrieval_node, router_node
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from state import AgentState

load_dotenv()

app = FastAPI(
    title="Enterprise Multi-Agent RAG API",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://13.206.213.75",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retrieval_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("generator", generator_node)

    workflow.set_entry_point("router")
    workflow.add_edge("router", "retriever")
    workflow.add_edge("retriever", "critic")
    workflow.add_edge("critic", "generator")
    workflow.add_edge("generator", END)

    return workflow.compile()


rag_app = build_graph()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str


@app.get("/")
def root():
    return {
        "message": "Enterprise Multi-Agent RAG API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/ask", response_model=QueryResponse)
def ask_multi_agent_rag(request: QueryRequest):
    try:
        initial_state = {
            "query": request.query,
            "sub_queries": [],
            "retrieved_docs": [],
            "critique": "",
            "generation": "",
            "loop_count": 0,
        }

        final_state = rag_app.invoke(initial_state)

        return QueryResponse(
            answer=final_state["generation"]
        )

    except Exception as e:
        print("--- ERROR IN /ASK ENDPOINT ---")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    try:
        content = await file.read()

        text = content.decode(
            "utf-8",
            errors="ignore"
        )

        doc = Document(
            page_content=text,
            metadata={
                "source": file.filename
            }
        )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        splits = text_splitter.split_documents(
            [doc]
        )

        vectorstore.add_documents(
            splits
        )

        return {
            "message": (
                f"Successfully ingested "
                f"{len(splits)} chunks from "
                f"{file.filename}!"
            )
        }

    except Exception as e:
        print("--- ERROR IN /UPLOAD ENDPOINT ---")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )