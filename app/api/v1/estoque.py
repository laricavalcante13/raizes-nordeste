from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import Unidade, Produto, EstoqueUnidade, Usuario
from app.domain.enums import PerfilUsuario
from app.api.deps import exigir_perfil, get_current_user
from app.schemas.estoque import AtualizarEstoqueSchema, EstoqueResponseSchema

router = APIRouter(prefix="/estoque", tags=["Controle de Estoque"])

@router.get("/unidades/{unidade_id}", response_model=List[EstoqueResponseSchema], summary="UC10: Consultar saldo de estoque por unidade")
def consultar_estoque_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user)
):
    if not db.query(Unidade).filter(Unidade.id == unidade_id).first():
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    return db.query(EstoqueUnidade).filter(EstoqueUnidade.unidade_id == unidade_id).all()

@router.put("/unidades/{unidade_id}/produtos/{produto_id}", response_model=EstoqueResponseSchema, summary="UC10: Entradas/Saídas de estoque por produto e unidade")
def atualizar_estoque_unidade(
    unidade_id: int,
    produto_id: int,
    payload: AtualizarEstoqueSchema,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.ATENDENTE, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
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