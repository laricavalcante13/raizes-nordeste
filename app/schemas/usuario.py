from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.domain.enums import PerfilUsuario

class ClienteCreateSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, example="Maria Silva")
    email: EmailStr = Field(..., example="maria@exemplo.com")
    senha: str = Field(..., min_length=6, example="Senha@123")
    consentimento_lgpd: bool = Field(
        ..., 
        description="Aceite obrigatório dos termos da LGPD para criação de uma conta"
    )

class UsuarioResponseSchema(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    consentimento_lgpd: bool
    criado_em: datetime

    class Config:
        from_attributes = True