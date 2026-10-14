from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import Produto, Categoria, Unidade, EstoqueUnidade, Usuario
from app.domain.enums import PerfilUsuario
from app.api.deps import exigir_perfil
from app.schemas.estoque import (
    ProdutoCreateSchema, ProdutoUpdateSchema, ProdutoResponseSchema,
    CategoriaCreateSchema, CategoriaResponseSchema
)
from app.schemas.produto import (
    ProdutoCardapioSchema,
    CardapioUnidadeResponseSchema,
)

router = APIRouter(prefix="/produtos", tags=["Produtos"])

# --- CATEGORIAS (UC09) ---
@router.post("/categorias", response_model=CategoriaResponseSchema, status_code=status.HTTP_201_CREATED, summary="UC09: Cadastrar categoria")
def criar_categoria(
    payload: CategoriaCreateSchema,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    if db.query(Categoria).filter(Categoria.nome == payload.nome).first():
        raise HTTPException(status_code=409, detail="Categoria com este nome já existe.")

    categoria = Categoria(**payload.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria

@router.get("/categorias", response_model=List[CategoriaResponseSchema], summary="Listar categorias de produtos")
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).all()

# --- PRODUTOS BASE (UC08) ---
@router.post("", response_model=ProdutoResponseSchema, status_code=status.HTTP_201_CREATED, summary="UC08: Cadastrar produto")
def criar_produto(
    payload: ProdutoCreateSchema,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    if not db.query(Categoria).filter(Categoria.id == payload.categoria_id).first():
        raise HTTPException(status_code=404, detail="Categoria informada não existe.")

    produto = Produto(**payload.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto

@router.get("", response_model=List[ProdutoResponseSchema], summary="UC08: Listar produtos ativos no sistema")
def listar_produtos(
    page: int = Query(default=1, ge=1, description="Número da página"),
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página"),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    return db.query(Produto).filter(Produto.ativo == True).offset(offset).limit(limit).all()

@router.patch("/{produto_id}", response_model=ProdutoResponseSchema, summary="UC08: Editar produto")
def editar_produto(
    produto_id: int,
    payload: ProdutoUpdateSchema,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(produto, key, value)

    db.commit()
    db.refresh(produto)
    return produto

# --- CONSULTA DE CARDÁPIO POR UNIDADE (UC11 / UC12) ---
@router.get(
    "/cardapio/unidades/{unidade_id}",
    response_model=CardapioUnidadeResponseSchema,
    summary="UC11 e UC12: Consultar Cardápio por Unidade e Categoria",
)
def consultar_cardapio_unidade(
    unidade_id: int,
    categoria_id: int
    | None = Query(
        default=None,
        description="UC12: Filtrar produtos por ID da Categoria",
    ),
    apenas_disponiveis: bool = Query(
        default=True,
        description="Exibir apenas produtos com estoque positivo",
    ),
    db: Session = Depends(get_db),
):
    unidade = (
        db.query(Unidade)
        .filter(Unidade.id == unidade_id, Unidade.ativo == True)
        .first()
    )
    if not unidade:
        raise HTTPException(
            status_code=404, detail="Unidade não encontrada ou inativa."
        )

    query = (
        db.query(
            Produto.id,
            Produto.nome,
            Produto.descricao,
            Produto.preco,
            Produto.categoria_id,
            Categoria.nome.label("categoria_nome"),
            EstoqueUnidade.quantidade.label("quantidade_estoque"),
        )
        .join(EstoqueUnidade, EstoqueUnidade.produto_id == Produto.id)
        .join(Categoria, Categoria.id == Produto.categoria_id)
        .filter(EstoqueUnidade.unidade_id == unidade_id, Produto.ativo == True)
    )

    if categoria_id is not None:
        query = query.filter(Produto.categoria_id == categoria_id)

    if apenas_disponiveis:
        query = query.filter(EstoqueUnidade.quantidade > 0)

    resultados = query.all()

    produtos_list = []
    for item in resultados:
        produtos_list.append(
            ProdutoCardapioSchema(
                id=item.id,
                nome=item.nome,
                descricao=item.descricao,
                preco=item.preco,
                categoria_id=item.categoria_id,
                categoria_nome=item.categoria_nome,
                quantidade_estoque=item.quantidade_estoque,
                disponivel=item.quantidade_estoque > 0,
            )
        )

    return CardapioUnidadeResponseSchema(
        unidade_id=unidade.id,
        unidade_nome=unidade.nome,
        total_itens=len(produtos_list),
        produtos=produtos_list,
    )