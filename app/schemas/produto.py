from decimal import Decimal
from pydantic import BaseModel

class ProdutoCardapioSchema(BaseModel):
    id: int
    nome: str
    descricao: str | None
    preco_base: Decimal
    categoria_id: int
    categoria_nome: str
    quantidade_estoque: int
    disponivel: bool

    class Config:
        from_attributes = True

class CardapioUnidadeResponseSchema(BaseModel):
    unidade_id: int
    unidade_nome: str
    total_itens: int
    produtos: list[ProdutoCardapioSchema]