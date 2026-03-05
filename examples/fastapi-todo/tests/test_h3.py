from fastapi.testclient import TestClient
from .. import main

client = TestClient(main.app)

def setup_function():
    """Reset the mock database before each test."""
    main.todos_db.clear()
    main.id_counter = 1

def test_update_todo_success():
    """Test successful update of a todo item."""
    # Seed data
    client.post("/todos", json={"title": "Old Title", "completed": False})
    
    payload = {"title": "New Title", "completed": True, "description": "Updated"}
    response = client.put("/todos/1", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "New Title"
    assert data["completed"] is True
    assert data["description"] == "Updated"
    
    # Verify via GET
    get_res = client.get("/todos/1")
    assert get_res.json()["title"] == "New Title"

def test_update_todo_not_found():
    """Test error when updating non-existent todo ID."""
    payload = {"title": "New Title"}
    response = client.put("/todos/999", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo with ID 999 not found"

def test_delete_todo_success():
    """Test successful deletion of a todo item."""
    # Seed data
    client.post("/todos", json={"title": "To be deleted"})
    
    response = client.delete("/todos/1")
    assert response.status_code == 204
    assert response.text == ""
    
    # Verify via GET
    get_res = client.get("/todos/1")
    assert get_res.status_code == 404

def test_delete_todo_not_found():
    """Test error when deleting non-existent todo ID."""
    response = client.delete("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo with ID 999 not found"

def test_update_todo_validation_error():
    """Test validation error during update."""
    # Seed data
    client.post("/todos", json={"title": "Valid"})
    
    payload = {"title": ""} # min_length=1
    response = client.put("/todos/1", json=payload)
    assert response.status_code == 422
