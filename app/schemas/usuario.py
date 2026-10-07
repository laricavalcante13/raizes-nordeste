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

class ColaboradorCreateSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, example="Carlos Atendente")
    email: EmailStr = Field(..., example="carlos@raizes.com.br")
    senha: str = Field(..., min_length=6, example="Senha@123")
    perfil: PerfilUsuario = Field(..., example=PerfilUsuario.ATENDENTE)

# Schema para atualização parcial de Usuário (UC04)
class UsuarioUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=100, example="Maria Silva Atualizada")
    email: EmailStr | None = Field(default=None, example="novo_email@exemplo.com")
    senha: str | None = Field(default=None, min_length=6, example="NovaSenha@123")
    perfil: PerfilUsuario | None = Field(default=None, example=PerfilUsuario.GERENTE)

# Resposta padrão para listagem e consulta
class UsuarioResponseSchema(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    consentimento_lgpd: bool
    criado_em: datetime

    class Config:
        from_attributes = True

UsuarioUpdateSchema.model_rebuild()