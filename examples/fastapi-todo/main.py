from typing import List
from fastapi import FastAPI, status, HTTPException
from .schemas import TodoCreate, TodoResponse

app = FastAPI(
    title="Todo API",
    description="A simple FastAPI REST API for managing todos",
    version="1.0.0"
)

# Mock database (in-memory list) for H1
# In future iterations, this will be replaced by a database layer
todos_db = []
id_counter = 1


@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate):
    global id_counter
    todo_data = todo.model_dump()
    todo_data["id"] = id_counter
    todos_db.append(todo_data)
    id_counter += 1
    return todo_data


@app.get("/todos", response_model=List[TodoResponse], status_code=status.HTTP_200_OK)
async def list_todos():
    return todos_db


@app.get("/todos/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
async def get_todo(todo_id: int):
    for todo in todos_db:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")


@app.put("/todos/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
async def update_todo(todo_id: int, todo_update: TodoCreate):
    for index, todo in enumerate(todos_db):
        if todo["id"] == todo_id:
            updated_todo = todo_update.model_dump()
            updated_todo["id"] = todo_id
            todos_db[index] = updated_todo
            return updated_todo
    raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int):
    for index, todo in enumerate(todos_db):
        if todo["id"] == todo_id:
            todos_db.pop(index)
            return
    raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")


@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    return {"message": "Welcome to the Todo API"}
