from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from app.domain.enums import CanalPedido, StatusPedido, StatusPagamento

# --- UC14: Gestão do Carrinho/Itens ---
class ItemPedidoCreateSchema(BaseModel):
    produto_id: int = Field(..., example=1)
    quantidade: int = Field(..., gt=0, example=2)

class ItemPedidoResponseSchema(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True

# --- UC13: Criar Pedido ---
class PedidoCreateSchema(BaseModel):
    unidade_id: int = Field(..., example=1)
    canal_venda: CanalPedido = Field(..., example=CanalPedido.TOTEM)
    observacao: str | None = Field(default=None, example="Sem cebola na tapioca")
    itens: list[ItemPedidoCreateSchema] = Field(..., min_items=1)
    pontos_para_usar: int | None = Field(default=0, ge=0, description="Quantidade de pontos de fidelidade para abater no valor")

class PedidoResponseSchema(BaseModel):
    id: int
    cliente_id: int
    unidade_id: int
    canal_venda: CanalPedido
    status: StatusPedido
    status_pagamento: StatusPagamento
    valor_total: Decimal
    observacao: str | None
    criado_em: datetime
    itens: list[ItemPedidoResponseSchema]

    class Config:
        from_attributes = True

# --- UC15: Pagamento Mock ---
class ProcessarPagamentoSchema(BaseModel):
    forma_pagamento: str = Field(..., example="PIX", description="PIX, CARTAO_CREDITO, CARTAO_DEBITO")
    simular_sucesso: bool = Field(default=True, description="Flag para simular se o pagamento foi aprovado ou recusado")

class PagamentoResultadoSchema(BaseModel):
    pedido_id: int
    status_pagamento: StatusPagamento
    status_pedido: StatusPedido
    mensagem: str

class ItemKDSResponseSchema(BaseModel):
    produto_id: int
    produto_nome: str
    quantidade: int

    class Config:
        from_attributes = True

class PedidoKDSResponseSchema(BaseModel):
    id: int
    unidade_id: int
    canal_venda: CanalPedido
    status: StatusPedido
    observacao: str | None
    criado_em: datetime
    itens: list[ItemKDSResponseSchema]

    class Config:
        from_attributes = True


class AtualizarStatusKDSResponseSchema(BaseModel):
    pedido_id: int
    novo_status: StatusPedido
    mensagem: str

# --- UC21: Relatório de Vendas por Canal ---
class VendasPorCanalItemSchema(BaseModel):
    canal_venda: CanalPedido
    quantidade_pedidos: int
    faturamento_total: Decimal


class RelatorioVendasResponseSchema(BaseModel):
    unidade_id: int | None
    data_inicio: str | None
    data_fim: str | None
    faturamento_geral: Decimal
    total_pedidos: int
    vendas_por_canal: list[VendasPorCanalItemSchema]


# --- UC22: Auditoria e Log de Transações ---
class TransacaoAuditSchema(BaseModel):
    pedido_id: int
    cliente_id: int
    unidade_id: int
    canal_venda: CanalPedido
    status_pedido: StatusPedido
    status_pagamento: StatusPagamento
    valor_total: Decimal
    criado_em: datetime

    class Config:
        from_attributes = True


class HistoricoTransacoesResponseSchema(BaseModel):
    total_registros: int
    transacoes: list[TransacaoAuditSchema]