from fastapi.testclient import TestClient
from .. import main

client = TestClient(main.app)

def setup_function():
    """Reset the mock database before each test."""
    main.todos_db.clear()
    main.id_counter = 1

def test_list_todos_empty():
    """Test retrieving list of todos when database is empty."""
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_list_todos_with_data():
    """Test retrieving list of todos with data."""
    # Seed data
    client.post("/todos", json={"title": "Todo 1"})
    client.post("/todos", json={"title": "Todo 2"})
    
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Todo 1"
    assert data[1]["title"] == "Todo 2"

def test_get_todo_by_id_success():
    """Test retrieving a single todo by ID."""
    # Seed data
    client.post("/todos", json={"title": "Specific Todo"})
    
    response = client.get("/todos/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Specific Todo"

def test_get_todo_by_id_not_found():
    """Test error when retrieving non-existent todo ID."""
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo with ID 999 not found"

def test_get_todo_by_id_invalid_type():
    """Test error when retrieving with invalid ID type."""
    response = client.get("/todos/abc")
    assert response.status_code == 422
