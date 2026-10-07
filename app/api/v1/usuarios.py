from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import Usuario
from app.domain.enums import PerfilUsuario
from app.schemas.usuario import (
    ColaboradorCreateSchema,
    UsuarioUpdateSchema,
    UsuarioResponseSchema
)
from app.core.security import gerar_hash_senha
from app.api.deps import get_current_user, exigir_perfil

router = APIRouter(prefix="/usuarios", tags=["Gestão de Usuários (CRUD)"])


# -----------------------------------------------------------------------------
# CREATE (UC03): Cadastrar Colaborador (Restrito a GERENTE e ADMIN)
# -----------------------------------------------------------------------------
@router.post(
    "",
    response_model=UsuarioResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="UC03: Cadastrar novo colaborador (Apenas Admin/Gerente)"
)
def criar_colaborador(
    payload: ColaboradorCreateSchema,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    # Verificar e-mail duplicado
    usuario_existente = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário cadastrado com este e-mail."
        )

    novo_usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=gerar_hash_senha(payload.senha),
        perfil=payload.perfil,
        consentimento_lgpd=True  # Colaboradores cadastrados internamente possuem termo corporativo
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario


# -----------------------------------------------------------------------------
# READ LIST: Listar todos os usuários (Restrito a GERENTE e ADMIN)
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[UsuarioResponseSchema],
    summary="Listar todos os usuários cadastrados"
)
def listar_usuarios(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return usuarios


# -----------------------------------------------------------------------------
# READ ONE: Obter perfil do usuário por ID
# -----------------------------------------------------------------------------
@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponseSchema,
    summary="Consultar dados do usuário por ID"
)
def obter_usuario_por_id(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    # O próprio usuário pode ver seus dados, ou um Gerente/Admin pode ver qualquer um
    if usuario_atual.id != usuario_id and usuario_atual.perfil not in [PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só tem permissão para visualizar seu próprio perfil."
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    return usuario


# -----------------------------------------------------------------------------
# UPDATE (UC04): Atualizar perfil / dados cadastrais
# -----------------------------------------------------------------------------
@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponseSchema,
    summary="UC04: Alterar perfil e dados cadastrais do usuário"
)
def atualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdateSchema,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    # Regra de Permissão: Apenas o próprio usuário ou Gerente/Admin podem alterar
    if usuario_atual.id != usuario_id and usuario_atual.perfil not in [PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para alterar o perfil deste usuário."
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    # Atualizações dos campos informados no payload
    if payload.nome:
        usuario.nome = payload.nome

    if payload.email and payload.email != usuario.email:
        email_em_uso = db.query(Usuario).filter(Usuario.email == payload.email).first()
        if email_em_uso:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O e-mail informado já está em uso por outro usuário."
            )
        usuario.email = payload.email

    if payload.senha:
        usuario.senha_hash = gerar_hash_senha(payload.senha)

    # Apenas Admin/Gerente pode mudar o campo perfil
    if payload.perfil and usuario_atual.perfil in [PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]:
        usuario.perfil = payload.perfil

    db.commit()
    db.refresh(usuario)

    return usuario


# -----------------------------------------------------------------------------
# DELETE (UC06): Excluir / Remover Usuário (LGPD ou Gestão Admin)
# -----------------------------------------------------------------------------
@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="UC06: Excluir registro de usuário"
)
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    # Regra de Permissão: O próprio usuário pode solicitar exclusão (LGPD) ou Admin/Gerente
    if usuario_atual.id != usuario_id and usuario_atual.perfil not in [PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para excluir este usuário."
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    db.delete(usuario)
    db.commit()

    return None