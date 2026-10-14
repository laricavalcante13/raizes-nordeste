from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import Unidade, Usuario
from app.domain.enums import PerfilUsuario
from app.api.deps import exigir_perfil, get_current_user
from app.schemas.estoque import UnidadeCreateSchema, UnidadeUpdateSchema, UnidadeResponseSchema

router = APIRouter(prefix="/unidades", tags=["Unidades"])

@router.post("", response_model=UnidadeResponseSchema, status_code=status.HTTP_201_CREATED, summary="UC07: Cadastrar nova unidade")
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

@router.get("", response_model=List[UnidadeResponseSchema], summary="Listar unidades ativas")
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).filter(Unidade.ativo == True).all()

@router.get("/{unidade_id}", response_model=UnidadeResponseSchema, summary="Obter dados da unidade por ID")
def obter_unidade(unidade_id: int, db: Session = Depends(get_db)):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    return unidade

@router.patch("/{unidade_id}", response_model=UnidadeResponseSchema, summary="UC07: Editar unidade")
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