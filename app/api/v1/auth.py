from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import Usuario
from app.domain.enums import PerfilUsuario
from app.schemas.usuario import ClienteCreateSchema, UsuarioResponseSchema
from app.core.security import gerar_hash_senha, verificar_senha, criar_token_acesso

router = APIRouter(prefix="/auth", tags=["Autenticação de Usuários"])

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

@router.post("/login", summary="Autenticar usuário e retornar token JWT")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    # Valida se o usuário existe e se a senha está correta
    if not usuario or not verificar_senha(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Gera o token de acesso
    access_token = criar_token_acesso(data={"sub": str(usuario.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
