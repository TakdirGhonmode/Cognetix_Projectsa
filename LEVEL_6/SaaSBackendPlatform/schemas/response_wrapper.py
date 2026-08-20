from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str = "Operation failed"
    errors: List[Any] = []
