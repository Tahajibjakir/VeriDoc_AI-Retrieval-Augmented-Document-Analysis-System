import chromadb
from chromadb.config import Settings
from app.core.config import settings

# Initialize ChromaDB client
# Using persistent storage for production-like feel
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Collection for document chunks
collection = chroma_client.get_or_create_collection(
    name="document_chunks",
    metadata={"hnsw:space": "cosine"}
)

def get_collection():
    return collection
