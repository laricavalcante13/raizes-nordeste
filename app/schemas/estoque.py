from decimal import Decimal
from pydantic import BaseModel, Field

# Schemas Unidades
class UnidadeCreateSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, example="Unidade Matriz")
    endereco: str = Field(..., example="Rua Marechal Deodoro, 630, Centro, Curitiba - PR")
    telefone: str | None = Field(default=None, example="(41) 32240008")

class UnidadeUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=100)
    endereco: str | None = Field(default=None)
    telefone: str | None = Field(default=None)
    ativo: bool | None = Field(default=None)

class UnidadeResponseSchema(UnidadeCreateSchema):
    id: int
    ativo: bool

    class Config:
        from_attributes = True


# Schemas Categorias
class CategoriaCreateSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, example="Pratos executivos")
    descricao: str | None = Field(default=None, example="Pratos executivos individuais (válidos somente para almoço)")

class CategoriaResponseSchema(CategoriaCreateSchema):
    id: int

    class Config:
        from_attributes = True


# Schemas Produtos
class ProdutoCreateSchema(BaseModel):
    categoria_id: int = Field(..., example=1)
    nome: str = Field(..., min_length=2, max_length=100, example="Baião de Dois")
    descricao: str | None = Field(default=None, example="Feijão de corda acompanhado de arroz, queijo coalho e charque.")
    preco: Decimal = Field(..., gt=0, example=18.50)

class ProdutoUpdateSchema(BaseModel):
    categoria_id: int | None = Field(default=None)
    nome: str | None = Field(default=None)
    descricao: str | None = Field(default=None)
    preco: Decimal | None = Field(default=None, gt=0)
    ativo: bool | None = Field(default=None)

class ProdutoResponseSchema(ProdutoCreateSchema):
    id: int
    ativo: bool

    class Config:
        from_attributes = True


# Schemas Estoque
class AtualizarEstoqueSchema(BaseModel):
    quantidade: int = Field(..., ge=0, example=50, description="Quantidade total em estoque alterada")

class EstoqueResponseSchema(BaseModel):
    id: int
    unidade_id: int
    produto_id: int
    quantidade: int

    class Config:
        from_attributes = True