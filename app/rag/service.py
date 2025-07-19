"""
RAG (Retrieval-Augmented Generation) service combining vector search with LLM
"""

from typing import List, Dict, Optional
from app.rag.vectorstore import vector_store
from app.chat.llm_service import llm_service


class RAGService:
    """
    RAG service that combines document retrieval with LLM generation.
    
    Single Responsibility: RAG pipeline coordination
    """
    
    def __init__(self, vector_store_instance=None, llm_service_instance=None):
        self.vector_store = vector_store_instance or vector_store
        self.llm_service = llm_service_instance or llm_service
    
    async def query_with_rag(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.3,
        model: str = None
    ) -> Dict[str, any]:
        """
        Perform RAG query: retrieve relevant documents and generate response.
        
        Single Responsibility: RAG pipeline execution
        """
        try:
            # Step 1: Retrieve relevant documents
            documents = await self.vector_store.similarity_search(
                query, k=k, score_threshold=score_threshold
            )
            
            if not documents:
                # No relevant documents found, generate response without context
                response = await self.llm_service.generate_response(
                    query, model=model
                )
                return {
                    "answer": response,
                    "sources": [],
                    "context_used": 0,
                    "message": "No relevant documents found in knowledge base"
                }
            
            # Step 2: Prepare context from retrieved documents
            context_parts = []
            for i, doc in enumerate(documents, 1):
                context_parts.append(f"Source {i}: {doc['content']}")
            
            context = "\n\n".join(context_parts)
            
            # Step 3: Generate response with context
            response = await self.llm_service.generate_response(
                query, context=context, model=model
            )
            
            return {
                "answer": response,
                "sources": documents,
                "context_used": len(documents),
                "message": f"Answer generated using {len(documents)} relevant sources"
            }
            
        except Exception as e:
            raise Exception(f"RAG query failed: {str(e)}")
    
    async def add_documents_to_knowledge_base(
        self, 
        documents: List[Dict[str, str]]
    ) -> bool:
        """
        Add documents to the knowledge base.
        
        Single Responsibility: Knowledge base expansion
        """
        return await self.vector_store.add_documents(documents)
    
    def get_knowledge_base_stats(self) -> Dict[str, int]:
        """
        Get statistics about the knowledge base.
        
        Single Responsibility: Statistics retrieval
        """
        return self.vector_store.get_stats()


# Global RAG service instance
rag_service = RAGService()
