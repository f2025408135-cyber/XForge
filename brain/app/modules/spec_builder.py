import json
from sqlalchemy.orm import Session
from .models import DiscoveredEndpoint

class SpecBuilder:
    """
    Synthesizes an OpenAPI-like dictionary from raw crawled data (Katana).
    This allows the AI agents (Theorist, BOLA, Logic Flow) to operate seamlessly 
    even when the target doesn't provide a public swagger.json.
    """
    @staticmethod
    def build_from_db(db: Session, target_id: int) -> dict:
        endpoints = db.query(DiscoveredEndpoint).filter_by(target_id=target_id).all()
        
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Synthesized Target Spec", "version": "1.0"},
            "paths": {}
        }
        
        for ep in endpoints:
            path = ep.path
            method = ep.method.lower()
            
            if path not in spec["paths"]:
                spec["paths"][path] = {}
                
            operation = {"parameters": []}
            
            # Reconstruct parameters from DB JSON strings
            if ep.parameters:
                try:
                    params_list = json.loads(ep.parameters)
                    for p in params_list:
                        # We blindly set 'in': 'query' for simplicity, but Theorist can infer body vs query by method
                        operation["parameters"].append({
                            "name": p,
                            "in": "query" if method == "get" else "body"
                        })
                except json.JSONDecodeError:
                    pass
                    
            spec["paths"][path][method] = operation
            
        return spec
