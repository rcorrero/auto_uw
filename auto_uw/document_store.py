"""
Document store for managing insurance-related documents and guidelines.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class DocumentStore:
    """Store for managing insurance-related documents."""
    
    def __init__(self, docs_dir: str = "data"):
        """Initialize the document store."""
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.documents: Dict[str, Dict] = {}
        self._load_documents()
    
    def _load_documents(self) -> None:
        """Load all documents from the store."""
        for doc_path in self.docs_dir.glob("*.json"):
            try:
                with open(doc_path, "r") as f:
                    doc = json.load(f)
                    self.documents[doc["id"]] = doc
            except Exception as e:
                print(f"Error loading document {doc_path}: {e}")
    
    def add_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any]) -> None:
        """Add a new document to the store."""
        if not doc_id:
            raise ValueError("Document ID cannot be empty")
        if not title:
            raise ValueError("Document title cannot be empty")
        if not content:
            raise ValueError("Document content cannot be empty")
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")
        
        doc = {
            "id": doc_id,
            "title": title,
            "content": content,
            "metadata": metadata,
            "type": metadata.get("type", "document"),
            "last_updated": datetime.now().isoformat(),
            "applicable_states": metadata.get("applicable_states", ["all"])
        }
        
        doc_path = self.docs_dir / f"{doc_id}.json"
        with open(doc_path, 'w') as f:
            json.dump(doc, f, indent=2)
        self.documents[doc_id] = doc
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a document by ID."""
        if doc_id not in self.documents:
            raise FileNotFoundError(f"Document {doc_id} not found")
        return self.documents[doc_id]
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the store."""
        return list(self.documents.values())
    
    def search_documents(self, query: str, search_metadata: bool = False) -> List[Dict[str, Any]]:
        """Search documents by content and optionally metadata."""
        query = query.lower()
        results = []
        
        for doc in self.documents.values():
            # Search in content
            if query in doc["content"].lower():
                results.append(doc)
                continue
            
            # Search in metadata if requested
            if search_metadata:
                metadata_str = json.dumps(doc["metadata"]).lower()
                if query in metadata_str:
                    results.append(doc)
        
        return results
    
    def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID."""
        if doc_id not in self.documents:
            raise FileNotFoundError(f"Document {doc_id} not found")
        
        doc_path = self.docs_dir / f"{doc_id}.json"
        doc_path.unlink()
        del self.documents[doc_id]
    
    def update_document(self, doc_id: str, **kwargs) -> None:
        """Update a document's fields."""
        doc = self.get_document(doc_id)
        
        # Update only provided fields
        for key, value in kwargs.items():
            if key in doc:
                doc[key] = value
        
        # Update last_updated timestamp
        doc["last_updated"] = datetime.now().isoformat()
        
        # Save updated document
        doc_path = self.docs_dir / f"{doc_id}.json"
        with open(doc_path, 'w') as f:
            json.dump(doc, f, indent=2)
        self.documents[doc_id] = doc
    
    def get_documents_by_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """Get all documents of a specific type."""
        return [doc for doc in self.documents.values() if doc["type"] == doc_type]
    
    def get_documents_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get all documents specific to a state."""
        return [
            doc for doc in self.documents.values()
            if state in doc.get("applicable_states", []) or "all" in doc.get("applicable_states", [])
        ]
    
    def semantic_search(self, query: str) -> List[str]:
        """Perform semantic search on document contents."""
        query = query.lower()
        results = []
        
        for doc in self.documents.values():
            content = doc["content"].lower()
            if query in content:
                results.append(doc["content"])
        
        return results