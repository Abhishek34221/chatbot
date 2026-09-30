import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Sample raw documents
raw_texts = [
    (
        "Our company's remote work policy states that employees can work from"
        " anywhere within their home country for up to 90 days per calendar"
        " year, provided they have prior manager approval."
    ),
    (
        "The standard health insurance plan covers 80% of in-network outpatient"
        " services after a deductible of $1,000 is met. Prescription drug"
        " copays are $15 for generic and $45 for brand name."
    ),
    (
        "To submit an expense report, employees must upload itemized receipts"
        " into the finance portal within 14 days of incurring the expense."
        " Reports submitted after 14 days require VP approval."
    ),
]

docs = [Document(page_content=text) for text in raw_texts]

# Chunking strategy
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)

# Initialize Free Local HuggingFace Embeddings & ChromaDB
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    documents=all_splits,
    embedding=embeddings,
    persist_directory="./chroma_db",
)

print(
    f"Successfully ingested {len(all_splits)} chunks into local ChromaDB using"
    " Local HuggingFace Embeddings."
)