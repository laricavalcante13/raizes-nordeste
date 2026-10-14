from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")

class PaginaResponseSchema(BaseModel, Generic[T]):
    itens: List[T]
    total_registros: int
    page: int
    limit: int
    total_paginas: int