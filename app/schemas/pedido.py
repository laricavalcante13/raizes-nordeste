from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.domain.enums import CanalPedido, StatusPedido

class ItemPedidoCreate(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0, description="A quantidade deve ser maior que zero")

class PedidoCreate(BaseModel):
    unidade_id: int
    canal_pedido: CanalPedido = Field(..., description="Canal de origem do pedido (obrigatório)")
    itens: List[ItemPedidoCreate]
    forma_pagamento: str

class ItemPedidoResponse(BaseModel):
    produto_id: int
    quantidade: int
    preco_unitario: float

    class Config:
        from_attributes = True

class PedidoResponse(BaseModel):
    id: int
    cliente_id: int
    unidade_id: int
    canal_pedido: CanalPedido
    status: StatusPedido
    valor_total: float
    criado_em: datetime
    itens: List[ItemPedidoResponse]

    class Config:
        from_attributes = True