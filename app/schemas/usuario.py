from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.domain.enums import PerfilUsuario

class ClienteCreateSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, example="Larissa Cavalcante")
    email: EmailStr = Field(..., example="lari.cavalcante13@gmail.com")
    senha: str = Field(..., min_length=6, example="larissa1234")
    consentimento_lgpd: bool = Field(
        ..., 
        description="Aceite obrigatório dos termos da LGPD para criação de uma conta"
    )

class FuncionarioCreateSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, example="Amanda Silva")
    email: EmailStr = Field(..., example="amanda.gerenciafortaleza@raizesnordeste.com.br")
    senha: str = Field(..., min_length=6, example="raizes@@2025")
    perfil: PerfilUsuario = Field(..., example=PerfilUsuario.GERENTE)

class UsuarioUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=100, example="Amanda Silva")
    email: EmailStr | None = Field(default=None, example="amanda.gerenciamatriz@raizesnordeste.com.br")
    senha: str | None = Field(default=None, min_length=6, example="raizes@@2026")
    perfil: PerfilUsuario | None = Field(default=None, example=PerfilUsuario.GERENTE)

class LGPDResponseSchema(BaseModel):
    usuario_id: int
    consentimento_lgpd: bool
    mensagem: str

class UsuarioResponseSchema(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    consentimento_lgpd: bool
    criado_em: datetime

    class Config:
        from_attributes = True

#sCHEMA Programa de fidelidade

class TransacaoFidelidadeSchema(BaseModel):
    id: int
    quantidade_pontos: int
    tipo_operacao: str
    descricao: str | None = None
    criado_em: datetime

    class Config:
        from_attributes = True


class SaldoFidelidadeResponseSchema(BaseModel):
    usuario_id: int
    saldo_pontos: int
    historico_recente: list[TransacaoFidelidadeSchema]

    class Config:
        from_attributes = True


class ResgatarPontosSchema(BaseModel):
    pontos_para_resgatar: int = Field(..., gt=0, example=100)
    descricao_recompensa: str = Field(..., example="Cupom R$ 10 off")

UsuarioUpdateSchema.model_rebuild()