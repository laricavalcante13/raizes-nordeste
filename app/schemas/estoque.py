from decimal import Decimal
from pydantic import BaseModel, Field

# --- Schemas UC07: Unidades ---
class UnidadeCreateSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, example="Unidade Salvador - Pelourinho")
    endereco: str = Field(..., example="Rua das Laranjeiras, 10 - Salvador/BA")
    telefone: str | None = Field(default=None, example="(71) 99999-8888")

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


# --- Schemas UC09: Categorias ---
class CategoriaCreateSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, example="Tapiocas Doces")
    descricao: str | None = Field(default=None, example="Tapiocas tradicionais recheadas com doces")

class CategoriaResponseSchema(CategoriaCreateSchema):
    id: int

    class Config:
        from_attributes = True


# --- Schemas UC08: Produtos ---
class ProdutoCreateSchema(BaseModel):
    categoria_id: int = Field(..., example=1)
    nome: str = Field(..., min_length=2, max_length=100, example="Tapioca de Carne de Sol")
    descricao: str | None = Field(default=None, example="Acompanha queijo coalho e manteiga de garrafa")
    preco_base: Decimal = Field(..., gt=0, example=18.50)

class ProdutoUpdateSchema(BaseModel):
    categoria_id: int | None = Field(default=None)
    nome: str | None = Field(default=None)
    descricao: str | None = Field(default=None)
    preco_base: Decimal | None = Field(default=None, gt=0)
    ativo: bool | None = Field(default=None)

class ProdutoResponseSchema(ProdutoCreateSchema):
    id: int
    ativo: bool

    class Config:
        from_attributes = True


# --- Schemas UC10: Estoque ---
class AtualizarEstoqueSchema(BaseModel):
    quantidade: int = Field(..., ge=0, example=50, description="Nova quantidade total em estoque")

class EstoqueResponseSchema(BaseModel):
    id: int
    unidade_id: int
    produto_id: int
    quantidade: int

    class Config:
        from_attributes = True