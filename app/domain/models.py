from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database import Base
from app.domain.enums import CanalPedido, StatusPedido, PerfilUsuario

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
    canal_pedido = Column(Enum(CanalPedido), nullable=False) # Requisito de Multicanalidade
    status = Column(Enum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO)
    valor_total = Column(Float, default=0.0)
    criado_em = Column(DateTime, default=datetime.utcnow)

    itens = relationship("ItemPedido", back_populates="pedido")

class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

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
    nome = Column(String(100), nullable=False, unique=True)  # ex: "Bebidas", "Tapiocas"
    descricao = Column(String(255), nullable=True)

    produtos = relationship("Produto", back_populates="categoria")

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)
    preco_base = Column(Float(10, 2), nullable=False)
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