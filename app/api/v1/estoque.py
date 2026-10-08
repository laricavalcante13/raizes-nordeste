from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import Unidade, Categoria, Produto, EstoqueUnidade, Usuario
from app.domain.enums import PerfilUsuario
from app.api.deps import get_current_user, exigir_perfil
from app.schemas.estoque import (
    UnidadeCreateSchema, UnidadeUpdateSchema, UnidadeResponseSchema,
    CategoriaCreateSchema, CategoriaResponseSchema,
    ProdutoCreateSchema, ProdutoUpdateSchema, ProdutoResponseSchema,
    AtualizarEstoqueSchema, EstoqueResponseSchema
)

router = APIRouter(prefix="/estoque", tags=["Gestão de Estoque e Unidades"])

# =============================================================================
# UC07: CADASTRAR / EDITAR UNIDADES (Restrito: GERENTE / ADMIN)
# =============================================================================
@router.post("/unidades", response_model=UnidadeResponseSchema, status_code=status.HTTP_201_CREATED, summary="UC07: Cadastrar nova unidade/filial")
def criar_unidade(
    payload: UnidadeCreateSchema,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    unidade = Unidade(**payload.model_dump())
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade

@router.get("/unidades", response_model=List[UnidadeResponseSchema], summary="Listar unidades ativas")
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).filter(Unidade.ativo == True).all()

@router.patch("/unidades/{unidade_id}", response_model=UnidadeResponseSchema, summary="UC07: Editar dados da unidade")
def editar_unidade(
    unidade_id: int,
    payload: UnidadeUpdateSchema,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(unidade, key, value)

    db.commit()
    db.refresh(unidade)
    return unidade


# =============================================================================
# UC09: GERENCIAR CATEGORIA DE PRODUTOS
# =============================================================================
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


# =============================================================================
# UC08: CADASTRAR / EDITAR PRODUTOS (CARDÁPIO)
# =============================================================================
@router.post("/produtos", response_model=ProdutoResponseSchema, status_code=status.HTTP_201_CREATED, summary="UC08: Cadastrar produto no cardápio")
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

@router.get("/produtos", response_model=List[ProdutoResponseSchema], summary="Listar produtos do cardápio")
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).filter(Produto.ativo == True).all()

@router.patch("/produtos/{produto_id}", response_model=ProdutoResponseSchema, summary="UC08: Editar produto")
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


# =============================================================================
# UC10: GERENCIAR ESTOQUE POR UNIDADE
# =============================================================================
@router.put(
    "/unidades/{unidade_id}/produtos/{produto_id}/estoque",
    response_model=EstoqueResponseSchema,
    summary="UC10: Atualizar saldo de estoque do produto na unidade"
)
def atualizar_estoque_unidade(
    unidade_id: int,
    produto_id: int,
    payload: AtualizarEstoqueSchema,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.ATENDENTE, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    # Validar se unidade e produto existem
    if not db.query(Unidade).filter(Unidade.id == unidade_id).first():
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    if not db.query(Produto).filter(Produto.id == produto_id).first():
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    estoque = db.query(EstoqueUnidade).filter(
        EstoqueUnidade.unidade_id == unidade_id,
        EstoqueUnidade.produto_id == produto_id
    ).first()

    if not estoque:
        estoque = EstoqueUnidade(
            unidade_id=unidade_id,
            produto_id=produto_id,
            quantidade=payload.quantidade
        )
        db.add(estoque)
    else:
        estoque.quantidade = payload.quantidade

    db.commit()
    db.refresh(estoque)
    return estoque

@router.get(
    "/unidades/{unidade_id}/estoque",
    response_model=List[EstoqueResponseSchema],
    summary="UC10: Consultar todo o estoque de uma unidade"
)
def consultar_estoque_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user)
):
    return db.query(EstoqueUnidade).filter(EstoqueUnidade.unidade_id == unidade_id).all()