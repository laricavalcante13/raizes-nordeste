import pytest
from app.domain.models import Usuario, Unidade, Categoria, Produto, EstoqueUnidade, Pedido
from app.domain.enums import PerfilUsuario, StatusPedido
from app.core.security import gerar_hash_senha
from app.main import app

from app.api.deps import get_current_user


@pytest.fixture
def cliente_autenticado(db):
    """
    Cria a infraestrutura básica (unidade, produto, estoque) e o cliente,
    e injeta o override de autenticação no FastAPI.
    """
    # 1. Unidade
    unidade = Unidade(nome="Matriz", endereco="Recife", ativo=True)
    db.add(unidade)
    db.commit()

    # 2. Cliente
    cliente = Usuario(
        id=1,
        nome="Larissa Cavalcante",
        email="larissa.cavalcante@email.com",
        senha_hash=gerar_hash_senha("cliente123"),
        perfil=PerfilUsuario.CLIENTE,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    # 3. Categoria e Produto com Estoque
    categoria = Categoria(nome="Pratos", descricao="Regional")
    db.add(categoria)
    db.commit()

    produto = Produto(
        categoria_id=categoria.id,
        nome="Carne de Sol",
        descricao="Com macaxeira",
        preco=45.90,
        ativo=True
    )
    db.add(produto)
    db.commit()

    estoque = EstoqueUnidade(unidade_id=unidade.id, produto_id=produto.id, quantidade=20)
    db.add(estoque)
    db.commit()

    # Sobrescreve a dependência de autenticação do FastAPI para retornar este cliente diretamente
    app.dependency_overrides[get_current_user] = lambda: cliente

    yield {
        "unidade_id": unidade.id,
        "produto_id": produto.id,
        "preco_unitario": 45.90
    }

    # Limpa o override após o teste
    app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# TESTES DO FLUXO A
# ==============================================================================

def test_passo_1_criar_pedido_com_sucesso(client, db, cliente_autenticado):
    payload_pedido = {
        "unidade_id": cliente_autenticado["unidade_id"],
        "canal_venda": "APP",
        "itens": [
            {
                "produto_id": cliente_autenticado["produto_id"],
                "quantidade": 2,
                "preco_unitario": cliente_autenticado["preco_unitario"]
            }
        ]
    }

    # Requisição direta sem precisar passar headers de token
    response = client.post("/api/v1/pedidos", json=payload_pedido)

    assert response.status_code == 201
    dados = response.json()
    assert "id" in dados
    assert dados["status"] == StatusPedido.AGUARDANDO_PAGAMENTO.value


def test_passo_2_validar_regras_basicas_sem_estoque(client, cliente_autenticado):
    payload_invalido = {
        "unidade_id": cliente_autenticado["unidade_id"],
        "canal_venda": "APP",
        "itens": [
            {
                "produto_id": cliente_autenticado["produto_id"],
                "quantidade": 999,  # Acima do estoque (20)
                "preco_unitario": cliente_autenticado["preco_unitario"]
            }
        ]
    }

    response = client.post("/api/v1/pedidos", json=payload_invalido)
    assert response.status_code in [400, 409, 422]


def test_passo_3_e_4_registrar_pagamento_mock_e_atualizar_status(client, db, cliente_autenticado):
    # 1. Cria o Pedido
    payload_pedido = {
        "unidade_id": cliente_autenticado["unidade_id"],
        "canal_venda": "APP",
        "itens": [
            {
                "produto_id": cliente_autenticado["produto_id"],
                "quantidade": 1,
                "preco_unitario": cliente_autenticado["preco_unitario"]
            }
        ]
    }
    res_pedido = client.post("/api/v1/pedidos", json=payload_pedido)
    pedido_id = res_pedido.json()["id"]

    # 2. Processa Pagamento Mock
    res_pagamento = client.post(
        f"/api/v1/pedidos/{pedido_id}/pagamento-mock",
        json={"forma_pagamento": "PIX"}
    )

    assert res_pagamento.status_code == 200
    assert res_pagamento.json()["status"] == StatusPedido.EM_PREPARACAO.value

    # 3. Confirmação direta via ORM SQLAlchemy no banco
    db.expire_all()
    pedido_final = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    assert pedido_final.status == StatusPedido.EM_PREPARACAO