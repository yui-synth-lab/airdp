from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TodoBase(BaseModel):
    title: str = Field(..., description="The title of the todo item", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Detailed description of the todo item")
    completed: bool = Field(False, description="Whether the todo item is completed")


class TodoCreate(TodoBase):
    pass


class TodoResponse(TodoBase):
    id: int = Field(..., description="Unique identifier for the todo item")

    model_config = ConfigDict(from_attributes=True)
