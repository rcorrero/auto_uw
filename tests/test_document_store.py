"""Tests for the DocumentStore class."""

import os
import json
import pytest
from unittest.mock import patch, Mock
from auto_uw.document_store import DocumentStore
from auto_uw.models import Document

@pytest.fixture
def temp_docs_dir(tmp_path):
    """Create a temporary directory for test documents."""
    docs_dir = tmp_path / "test_docs"
    docs_dir.mkdir()
    return docs_dir

@pytest.fixture
def document_store(temp_docs_dir):
    """Create a DocumentStore instance with test directory."""
    return DocumentStore(docs_dir=str(temp_docs_dir))

@pytest.fixture
def sample_document():
    """Create a sample document."""
    return Document(
        doc_id="test_doc_001",
        title="Test Document",
        content="This is a test document.",
        doc_type="guideline",
        metadata={
            "business_type": "restaurant",
            "version": "1.0",
            "last_updated": "2024-03-22"
        }
    )

def test_document_store_initialization(document_store, temp_docs_dir):
    """Test DocumentStore initialization."""
    assert document_store.docs_dir == str(temp_docs_dir)
    assert os.path.exists(document_store.docs_dir)

def test_add_document(document_store, sample_document):
    """Test adding a document."""
    # Add document
    document_store.add_document(
        doc_id=sample_document.doc_id,
        title=sample_document.title,
        content=sample_document.content,
        doc_type=sample_document.doc_type,
        metadata=sample_document.metadata
    )
    
    # Verify document was saved
    doc_path = os.path.join(document_store.docs_dir, f"{sample_document.doc_id}.json")
    assert os.path.exists(doc_path)
    
    # Verify document contents
    with open(doc_path, 'r') as f:
        saved_doc = json.load(f)
        assert saved_doc['doc_id'] == sample_document.doc_id
        assert saved_doc['title'] == sample_document.title
        assert saved_doc['content'] == sample_document.content
        assert saved_doc['doc_type'] == sample_document.doc_type
        assert saved_doc['metadata'] == sample_document.metadata

def test_get_document(document_store, sample_document):
    """Test retrieving a document."""
    # Add document first
    document_store.add_document(
        doc_id=sample_document.doc_id,
        title=sample_document.title,
        content=sample_document.content,
        doc_type=sample_document.doc_type,
        metadata=sample_document.metadata
    )
    
    # Retrieve document
    retrieved_doc = document_store.get_document(sample_document.doc_id)
    
    # Verify document contents
    assert retrieved_doc.doc_id == sample_document.doc_id
    assert retrieved_doc.title == sample_document.title
    assert retrieved_doc.content == sample_document.content
    assert retrieved_doc.doc_type == sample_document.doc_type
    assert retrieved_doc.metadata == sample_document.metadata

def test_list_documents(document_store, sample_document):
    """Test listing documents."""
    # Add multiple documents
    docs = [
        sample_document,
        Document(
            doc_id="test_doc_002",
            title="Another Document",
            content="This is another test document.",
            doc_type="guideline",
            metadata={"business_type": "retail"}
        )
    ]
    
    for doc in docs:
        document_store.add_document(
            doc_id=doc.doc_id,
            title=doc.title,
            content=doc.content,
            doc_type=doc.doc_type,
            metadata=doc.metadata
        )
    
    # List documents
    doc_list = document_store.list_documents()
    
    # Verify list contents
    assert len(doc_list) == 2
    doc_ids = {doc.doc_id for doc in doc_list}
    assert doc_ids == {doc.doc_id for doc in docs}

def test_search_documents(document_store, sample_document):
    """Test searching documents."""
    # Add document
    document_store.add_document(
        doc_id=sample_document.doc_id,
        title=sample_document.title,
        content=sample_document.content,
        doc_type=sample_document.doc_type,
        metadata=sample_document.metadata
    )
    
    # Search by content
    results = document_store.search_documents("test document")
    assert len(results) == 1
    assert results[0].doc_id == sample_document.doc_id
    
    # Search by metadata
    results = document_store.search_documents("restaurant", search_metadata=True)
    assert len(results) == 1
    assert results[0].doc_id == sample_document.doc_id
    
    # Search with no results
    results = document_store.search_documents("nonexistent")
    assert len(results) == 0

def test_update_document(document_store, sample_document):
    """Test updating a document."""
    # Add document first
    document_store.add_document(
        doc_id=sample_document.doc_id,
        title=sample_document.title,
        content=sample_document.content,
        doc_type=sample_document.doc_type,
        metadata=sample_document.metadata
    )
    
    # Update document
    new_content = "Updated content"
    document_store.update_document(
        doc_id=sample_document.doc_id,
        content=new_content
    )
    
    # Verify update
    updated_doc = document_store.get_document(sample_document.doc_id)
    assert updated_doc.content == new_content
    assert updated_doc.title == sample_document.title  # Unchanged

def test_delete_document(document_store, sample_document):
    """Test deleting a document."""
    # Add document first
    document_store.add_document(
        doc_id=sample_document.doc_id,
        title=sample_document.title,
        content=sample_document.content,
        doc_type=sample_document.doc_type,
        metadata=sample_document.metadata
    )
    
    # Delete document
    document_store.delete_document(sample_document.doc_id)
    
    # Verify deletion
    doc_path = os.path.join(document_store.docs_dir, f"{sample_document.doc_id}.json")
    assert not os.path.exists(doc_path)
    
    # Verify document is not retrievable
    with pytest.raises(FileNotFoundError):
        document_store.get_document(sample_document.doc_id)

def test_error_handling(document_store):
    """Test error handling in various scenarios."""
    # Test getting non-existent document
    with pytest.raises(FileNotFoundError):
        document_store.get_document("nonexistent")
    
    # Test updating non-existent document
    with pytest.raises(FileNotFoundError):
        document_store.update_document("nonexistent", "new content")
    
    # Test deleting non-existent document
    with pytest.raises(FileNotFoundError):
        document_store.delete_document("nonexistent")
    
    # Test invalid JSON in document file
    doc_path = os.path.join(document_store.docs_dir, "invalid.json")
    with open(doc_path, 'w') as f:
        f.write("invalid json")
    
    with pytest.raises(json.JSONDecodeError):
        document_store.get_document("invalid")

def test_business_type_guidelines(document_store):
    """Test business type guidelines."""
    # Add guidelines for different business types
    business_types = ["restaurant", "retail", "manufacturing", "construction"]
    for business_type in business_types:
        document_store.add_document(
            doc_id=f"guideline_{business_type}",
            title=f"{business_type.title()} Guidelines",
            content=f"Guidelines for {business_type} businesses",
            doc_type="guideline",
            metadata={"business_type": business_type}
        )
    
    # Verify all business types have guidelines
    for business_type in business_types:
        results = document_store.search_documents(
            business_type,
            search_metadata=True,
            doc_type="guideline"
        )
        assert len(results) == 1
        assert results[0].metadata["business_type"] == business_type 