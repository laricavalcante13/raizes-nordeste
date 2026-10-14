import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.database import SessionLocal, engine, Base
from app.domain.models import Usuario, Unidade, Categoria, Produto, EstoqueUnidade, ContaFidelidade
from app.domain.enums import PerfilUsuario
from passlib.context import CryptContext

# Configuração de hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash(senha: str) -> str:
    return pwd_context.hash(senha)

def popular_banco():
    # criação das tabelas
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Verificar se já existem dados
        if db.query(Usuario).first():
            print("O banco de dados já possui registros. Pressione Ctrl+C para cancelar ou aguarde a finalização.")
            return

        print("Iniciando criação de dados no banco...")

        # 2. Criar Unidades 
        unidade_matriz = Unidade(nome="Raízes do Nordeste - Matriz", cidade="Recife", endereco="Av. das Torres, 1500", ativo=True)
        unidade_olinda = Unidade(nome="Raízes do Nordeste - Olinda", cidade="Olinda", endereco="R. Marechal Deodoro, 520", ativo=True)
        unidade_joaopessoa = Unidade(nome="Raízes do Nordeste - João Pessoa", cidade="João Pessoa", endereco="Av. Cel. Laurindo, 849", ativo=True)

        db.add_all([unidade_matriz, unidade_joaopessoa, unidade_olinda])
        db.commit()

        # 3. Criar Usuários
        usuarios = [
            Usuario(
                nome="Administrador Geral",
                email="admin@raizesnordeste.com.br",
                senha_hash=gerar_hash("admin123"),
                perfil=PerfilUsuario.ADMIN,
                consentimento_lgpd=True
            ),
            Usuario(
                nome="Gerente Matriz",
                email="gerente.matriz@raizesnordeste.com.br",
                senha_hash=gerar_hash("gerente123"),
                perfil=PerfilUsuario.GERENTE,
                consentimento_lgpd=True
            ),
            Usuario(
                nome="Atendente",
                email="atendimento.matriz@raizesnordeste.com.br",
                senha_hash=gerar_hash("atendente123"),
                perfil=PerfilUsuario.ATENDENTE,
                consentimento_lgpd=True
            ),
            Usuario(
                nome="Equipe Cozinha",
                email="cozinha.matriz@raizesnordeste.com.br",
                senha_hash=gerar_hash("cozinha123"),
                perfil=PerfilUsuario.COZINHA,
                consentimento_lgpd=True
            ),
            Usuario(
                nome="Larissa Cruz (Cliente)",
                email="larissa.cruz@email.com",
                senha_hash=gerar_hash("cliente123"),
                perfil=PerfilUsuario.CLIENTE,
                consentimento_lgpd=True
            )
        ]
        db.add_all(usuarios)
        db.commit()

        # Criar Conta de Fidelidade para o cliente
        cliente_larissa = db.query(Usuario).filter_map(Usuario.email == "larissa.cruz@email.com").first() if hasattr(db.query(Usuario), 'filter_map') else db.query(Usuario).filter(Usuario.email == "maria.silva@email.com").first()
        if cliente_larissa:
            conta_fidelidade = ContaFidelidade(usuario_id=cliente_larissa.id, saldo_pontos=150)
            db.add(conta_fidelidade)
            db.commit()

        # 4. Categorias de produtos
        cat_pratos = Categoria(nome="Pratos Principais", descricao="Pratos principais e menu executivo")
        cat_bebidas = Categoria(nome="Bebidas", descricao="Sucos naturais, refrigerantes e drinks")
        cat_sobremesas = Categoria(nome="Sobremesas", descricao="Sobremesas e sorvetes")
        db.add_all([cat_pratos, cat_bebidas, cat_sobremesas])
        db.commit()

        # 5. Criar Produtos
        prod1 = Produto(categoria_id=cat_pratos.id, nome="Carne de Sol com Macaxeira", descricao="Servido com manteiga de garrafa e queijo coalho assado", preco=45.90, ativo=True)
        prod2 = Produto(categoria_id=cat_pratos.id, nome="Baião de Dois (para 2 pessoas)", descricao="Arroz, feijão de corda, carne seca, queijo coalho e bacon", preco=89.90, ativo=True)
        prod3 = Produto(categoria_id=cat_bebidas.id, nome="Suco de Caju Jarra 1L", descricao="Suco da fruta natural", preco=19.50, ativo=True)
        prod4 = Produto(categoria_id=cat_sobremesas.id, nome="Bolo de Rolo com Sorvete", descricao="Fatia de bolo de rolo tradicional com sorvete de creme", preco=18.00, ativo=True)
        db.add_all([prod1, prod2, prod3, prod4])
        db.commit()

        # 6. Criar Estoque por Unidade
        estoques = [
            EstoqueUnidade(unidade_id=unidade_matriz.id, produto_id=prod1.id, quantidade_disponivel=50, disponivel=True),
            EstoqueUnidade(unidade_id=unidade_matriz.id, produto_id=prod2.id, quantidade_disponivel=40, disponivel=True),
            EstoqueUnidade(unidade_id=unidade_matriz.id, produto_id=prod3.id, quantidade_disponivel=100, disponivel=True),
            EstoqueUnidade(unidade_id=unidade_joaopessoa.id, produto_id=prod4.id, quantidade_disponivel=30, disponivel=True),
            EstoqueUnidade(unidade_id=unidade_olinda.id, produto_id=prod1.id, quantidade_disponivel=25, disponivel=True),
            EstoqueUnidade(unidade_id=unidade_joaopessoa.id, produto_id=prod3.id, quantidade_disponivel=60, disponivel=True),
        ]
        db.add_all(estoques)
        db.commit()

        print("Dados criado com sucesso!")

    except Exception as e:
        print(f"Erro ao criar os dados no banco: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco()