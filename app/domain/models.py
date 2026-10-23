from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.infrastructure.database import Base
from app.domain.enums import CanalPedido, StatusPedido, PerfilUsuario, StatusPagamento

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, 
                   index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(Enum(PerfilUsuario), default=PerfilUsuario.CLIENTE)
    consentimento_lgpd = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    canal_venda = Column(Enum(CanalPedido), nullable=False)
    status = Column(Enum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO, nullable=False)
    status_pagamento = Column(Enum(StatusPagamento), default=StatusPagamento.AGUARDANDO, nullable=False)
    valor_total = Column(Numeric(10, 2), default=0.00, nullable=False)
    desconto_aplicado = Column(Numeric(10, 2), default=0.00, nullable=False)
    pontos_utilizados = Column(Integer, default=0, nullable=False)
    observacao = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    cliente = relationship("Usuario")
    unidade = relationship("Unidade")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto")

class Unidade(Base):
    __tablename__ = "unidades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False) 
    endereco = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    estoques = relationship("EstoqueUnidade", back_populates="unidade")

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True) 
    descricao = Column(String(255), nullable=True)

    produtos = relationship("Produto", back_populates="categoria")

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)
    preco = Column(Float(10, 2), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    categoria = relationship("Categoria", back_populates="produtos")
    estoques = relationship("EstoqueUnidade", back_populates="produto")

class EstoqueUnidade(Base):
    __tablename__ = "estoque_unidades"

    id = Column(Integer, primary_key=True, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, default=0, nullable=False)

    unidade = relationship("Unidade", back_populates="estoques")
    produto = relationship("Produto", back_populates="estoques")

class ContaFidelidade(Base):
    __tablename__ = "contas_fidelidade"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, unique=True)
    saldo_pontos = Column(Integer, default=0, nullable=False)

    usuario = relationship("Usuario")
    historico = relationship("HistoricoFidelidade", back_populates="conta", cascade="all, delete-orphan")

class HistoricoFidelidade(Base):
    __tablename__ = "historico_fidelidade"

    id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_fidelidade.id"), nullable=False)
    quantidade_pontos = Column(Integer, nullable=False) # Positivo (acúmulo) ou Negativo (resgate)
    tipo_operacao = Column(String(50), nullable=False) # ACUMULO_PEDIDO, RESGATE_RECOMPENSA, AJUSTE_ADMIN
    descricao = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conta = relationship("ContaFidelidade", back_populates="historico")

class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    acao = Column(String, nullable=False)      
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    detalhes = Column(String, nullable=True)
    data_hora = Column(DateTime, default=datetime.utcnow)