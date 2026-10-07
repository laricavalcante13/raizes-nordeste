from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# Constantes exportadas para o deps.py
SECRET_KEY = "LOEMIPSUMBDJAJKAKVSDV_646DFBSF64_SDNOBOT562"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas de validade

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

def criar_token_acesso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    para_codificar = data.copy()
    if expires_delta:
        expirar = datetime.now(timezone.utc) + expires_delta
    else:
        expirar = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    para_codificar.update({"exp": expirar})
    token_jwt = jwt.encode(para_codificar, SECRET_KEY, algorithm=ALGORITHM)
    return token_jwt