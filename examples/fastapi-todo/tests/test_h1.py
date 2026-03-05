from fastapi.testclient import TestClient
from .. import main

client = TestClient(main.app)

def setup_function():
    """Reset the mock database before each test."""
    main.todos_db.clear()
    main.id_counter = 1

def test_create_todo_success():
    """Test successful creation of a todo item."""
    payload = {
        "title": "Test Todo",
        "description": "A description for the test todo",
        "completed": False
    }
    response = client.post("/todos", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["completed"] == payload["completed"]

def test_create_todo_minimal_payload():
    """Test creation with only the required fields."""
    payload = {"title": "Minimal Todo"}
    response = client.post("/todos", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == payload["title"]
    assert data["description"] is None
    assert data["completed"] is False

def test_create_todo_validation_error_missing_title():
    """Test validation error when title is missing."""
    payload = {"description": "Missing title"}
    response = client.post("/todos", json=payload)
    
    assert response.status_code == 422
    assert "detail" in response.json()

def test_create_todo_validation_error_invalid_types():
    """Test validation error with incorrect field types."""
    payload = {
        "title": 123,  # Should be string
        "completed": "NotABoolean"  # Should be boolean
    }
    response = client.post("/todos", json=payload)
    
    assert response.status_code == 422
    assert "detail" in response.json()

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Todo API"}
