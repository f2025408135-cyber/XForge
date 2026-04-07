import chromadb
import os
import json

class PayloadMemory:
    """
    Manages the Vector Database (Chroma) to give the AI long-term memory.
    Stores successful fuzzing payloads (e.g. WAF bypasses) so they can be retrieved 
    contextually for future attacks on similar endpoints.
    """
    def __init__(self):
        # We use a persistent local client for the sandbox. In full prod, this connects to a chromadb server
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_data")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Collection for storing successfully executed payloads
        self.collection = self.client.get_or_create_collection(name="successful_payloads")

    def store_success(self, task_id: str, attack_type: str, payload_json: str, description: str):
        """
        Stores a successful payload into the vector memory.
        """
        # The document is the string representation that will be vectorized
        # We embed the attack type, description, and the payload itself
        document_text = f"Attack: {attack_type} | Description: {description} | Payload: {payload_json}"
        
        self.collection.add(
            documents=[document_text],
            metadatas=[{"task_id": task_id, "attack_type": attack_type}],
            ids=[f"{task_id}-mem"]
        )

    def retrieve_similar_payloads(self, attack_type: str, context: str, n_results: int = 3) -> list:
        """
        Queries the memory for past payloads that worked for similar scenarios.
        """
        query_text = f"Attack: {attack_type} | Context: {context}"
        
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"attack_type": attack_type}
            )
            
            if not results or "documents" not in results or not results["documents"]:
                return []
                
            return results["documents"][0]
        except Exception as e:
            print(f"Memory retrieval failed: {e}")
            return []
