"""
FAISS vector store implementation for RAG
Reference: https://faiss.ai/index.html
"""

import faiss
import numpy as np
from typing import List, Dict, Optional
import pickle
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer

from app.shared.config import settings


class FAISSVectorStore:
    """
    FAISS-based vector store for document embeddings and similarity search.
    
    Single Responsibility: Vector storage and similarity search operations
    """
    
    def __init__(self, embedding_model: str = None, index_path: str = None):
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index_path = Path(index_path or settings.faiss_index_path)
        self.index = None
        self.document_store = {}
        
        # Ensure index directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing index or create new one
        self._initialize_index()
    
    def _initialize_index(self):
        """
        Initialize FAISS index, loading from disk if available.
        
        Single Responsibility: Index initialization
        """
        index_file = self.index_path / "faiss.index"
        docs_file = self.index_path / "documents.pkl"
        
        if index_file.exists() and docs_file.exists():
            try:
                self.index = faiss.read_index(str(index_file))
                with open(docs_file, 'rb') as f:
                    self.document_store = pickle.load(f)
                print(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"Failed to load existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """
        Create new FAISS index.
        
        Single Responsibility: New index creation
        """
        # Use HNSW for better performance with moderate datasets
        self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        self.index.hnsw.efConstruction = 200
        self.index.hnsw.efSearch = 100
        self.document_store = {}
        print("Created new FAISS HNSW index")
    
    async def add_documents(self, documents: List[Dict[str, str]]) -> bool:
        """
        Add documents to the vector store.
        
        Single Responsibility: Document addition to vector store
        """
        try:
            if not documents:
                return True
            
            # Extract texts for embedding
            texts = [doc["content"] for doc in documents]
            
            # Generate embeddings in batches for memory efficiency
            batch_size = 32
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_embeddings = self.embedding_model.encode(
                    batch_texts,
                    batch_size=min(batch_size, len(batch_texts)),
                    show_progress_bar=True
                )
                embeddings.extend(batch_embeddings)
            
            # Convert to numpy array and normalize
            embeddings_array = np.array(embeddings).astype(np.float32)
            faiss.normalize_L2(embeddings_array)
            
            # Add to index
            start_idx = self.index.ntotal
            self.index.add(embeddings_array)
            
            # Store document metadata
            for i, doc in enumerate(documents):
                self.document_store[start_idx + i] = {
                    'content': doc["content"],
                    'metadata': doc.get("metadata", {})
                }
            
            # Save index
            self.save_index()
            
            print(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
            return False
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Perform similarity search for query.
        
        Single Responsibility: Similarity search execution
        """
        try:
            if self.index.ntotal == 0:
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            query_embedding = query_embedding.astype(np.float32)
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding, k)
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                    
                if score_threshold and score < score_threshold:
                    continue
                
                if idx in self.document_store:
                    result = {
                        'content': self.document_store[idx]['content'],
                        'metadata': self.document_store[idx]['metadata'],
                        'similarity_score': float(score)
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []
    
    def save_index(self):
        """
        Save index and document store to disk.
        
        Single Responsibility: Index persistence
        """
        try:
            index_file = self.index_path / "faiss.index"
            docs_file = self.index_path / "documents.pkl"
            
            faiss.write_index(self.index, str(index_file))
            
            with open(docs_file, 'wb') as f:
                pickle.dump(self.document_store, f)
                
            print("FAISS index saved successfully")
            
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get vector store statistics.
        
        Single Responsibility: Statistics retrieval
        """
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_documents": len(self.document_store),
            "dimension": self.dimension
        }


# Global vector store instance
vector_store = FAISSVectorStore()
