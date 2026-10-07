from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import Usuario
from app.domain.enums import PerfilUsuario
from app.schemas.usuario import ClienteCreateSchema, UsuarioResponseSchema
from app.core.security import gerar_hash_senha

router = APIRouter(prefix="/auth", tags=["Autenticação & LGPD"])

@router.post(
    "/registrar-cliente", 
    response_model=UsuarioResponseSchema, 
    status_code=status.HTTP_201_CREATED,
    summary="UC01: Cadastrar Cliente com aceite de termos LGPD"
)
def registrar_cliente(payload: ClienteCreateSchema, db: Session = Depends(get_db)):
    # 1. Validação de Regra LGPD: O consentimento deve ser explicitamente True
    if not payload.consentimento_lgpd:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="É obrigatório aceitar os termos de consentimento da LGPD para prosseguir."
        )

    # 2. Verificar se o e-mail já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado no sistema."
        )

    # 3. Criar usuário garantindo perfil CLIENTE e hash de senha
    novo_cliente = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=gerar_hash_senha(payload.senha),
        perfil=PerfilUsuario.CLIENTE,
        consentimento_lgpd=payload.consentimento_lgpd
    )

    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)

    return novo_cliente