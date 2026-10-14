import pytest
from app.domain.models import Usuario, Unidade, Categoria, Produto, EstoqueUnidade, Pedido
from app.domain.enums import PerfilUsuario, StatusPedido, CanalPedido
from app.core.security import gerar_hash_senha

@pytest.fixture
def dados_fluxo_a(db):
    """
    Fixture para criar a massa de dados inicial persistida no banco de testes:
    - 1 Unidade
    - 1 Cliente cadastrado (com senha hash)
    - 1 Categoria e 1 Produto com estoque disponível
    """
    # 1. Unidade
    unidade = Unidade(
        nome="Raízes do Nordeste - Matriz",
        endereco="Av. das Torres, 1500, Recife",
        ativo=True
    )
    db.add(unidade)

    # 2. Cliente
    cliente = Usuario(
        nome="Larissa Cavalcante",
        email="larissa.cavalcante@email.com",
        senha_hash=gerar_hash_senha("cliente123"),
        perfil=PerfilUsuario.CLIENTE,
        consentimento_lgpd=True
    )
    db.add(cliente)

    # 3. Categoria e Produto
    categoria = Categoria(nome="Pratos Principais", descricao="Pratos regionais")
    db.add(categoria)
    db.commit()

    produto = Produto(
        categoria_id=categoria.id,
        nome="Carne de Sol com Macaxeira",
        descricao="Servido com manteiga de garrafa e queijo coalho assado",
        preco=45.90,
        ativo=True
    )
    db.add(produto)
    db.commit()

    # 4. Estoque na Unidade
    estoque = EstoqueUnidade(
        unidade_id=unidade.id,
        produto_id=produto.id,
        quantidade=20,
    )
    db.add(estoque)
    db.commit()

    return {
        "unidade_id": unidade.id,
        "cliente_email": "larissa.cavalcante@email.com",
        "cliente_senha": "cliente123",
        "produto_id": produto.id,
        "preco_unitario": 45.90
    }


def obter_token_autenticado(client, email: str, senha: str) -> dict:
    """Helper para realizar login e retornar headers com JWT Bearer Token."""
    response = client.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# TESTES DO FLUXO A (PEDIDO -> PAGAMENTO MOCK -> ATUALIZAÇÃO DE STATUS)
# ==============================================================================

def test_passo_1_criar_pedido_com_sucesso(client, db, massa_dados_fluxo_a):
    """
    Passo 1: Cliente autenticado cria um pedido com itens válidos.
    Deverá persistir no banco com status inicial 'AGUARDANDO_PAGAMENTO'.
    """
    headers = obter_token_autenticado(
        client, 
        massa_dados_fluxo_a["cliente_email"], 
        massa_dados_fluxo_a["cliente_senha"]
    )

    payload_pedido = {
        "unidade_id": massa_dados_fluxo_a["unidade_id"],
        "canal_pedido": "APP",
        "itens": [
            {
                "produto_id": massa_dados_fluxo_a["produto_id"],
                "quantidade": 2,
                "preco_unitario": massa_dados_fluxo_a["preco_unitario"]
            }
        ]
    }

    response = client.post("/api/v1/pedidos", json=payload_pedido, headers=headers)

    assert response.status_code == 201
    dados = response.json()
    assert "id" in dados
    assert dados["status"] == StatusPedido.AGUARDANDO_PAGAMENTO.value
    assert dados["valor_total"] == 97.80  # 2 * 48.90

    # Valida persistência real no Banco de Dados
    pedido_db = db.query(Pedido).filter(Pedido.id == dados["id"]).first()
    assert pedido_db is not None
    assert pedido_db.status == StatusPedido.AGUARDANDO_PAGAMENTO


def test_passo_2_validar_regras_basicas_sem_estoque(client, massa_dados_fluxo_a):
    """
    Passo 2 (Validação/Regra de Negócio): Tentar criar pedido solicitando
    quantidade maior do que o estoque disponível.
    """
    headers = obter_token_autenticado(
        client, 
        massa_dados_fluxo_a["cliente_email"], 
        massa_dados_fluxo_a["cliente_senha"]
    )

    # Solicita 999 unidades (estoque disponível é 20)
    payload_invalido = {
        "unidade_id": massa_dados_fluxo_a["unidade_id"],
        "canal_pedido": "APP",
        "itens": [
            {
                "produto_id": massa_dados_fluxo_a["produto_id"],
                "quantidade": 999,
                "preco_unitario": massa_dados_fluxo_a["preco_unitario"]
            }
        ]
    }

    response = client.post("/api/v1/pedidos", json=payload_invalido, headers=headers)

    # Deve retornar Erro de Regra de Negócio 
    assert response.status_code in [400, 409]
    dados_erro = response.json()
    assert "error" in dados_erro
    assert "message" in dados_erro


def test_passo_3_e_4_registrar_pagamento_mock_e_atualizar_status(client, db, massa_dados_fluxo_a):
    """
    Passos 3 e 4: Registrar o pagamento mock de um pedido existente e verificar
    a atualização automática do status do pedido no banco para 'EM_PREPARACAO'.
    """
    headers = obter_token_autenticado(
        client, 
        massa_dados_fluxo_a["cliente_email"], 
        massa_dados_fluxo_a["cliente_senha"]
    )

    # 1. Cria o Pedido
    payload_pedido = {
        "unidade_id": massa_dados_fluxo_a["unidade_id"],
        "canal_pedido": "APP",
        "itens": [
            {
                "produto_id": massa_dados_fluxo_a["produto_id"],
                "quantidade": 1,
                "preco_unitario": massa_dados_fluxo_a["preco_unitario"]
            }
        ]
    }
    res_pedido = client.post("/api/v1/pedidos", json=payload_pedido, headers=headers)
    pedido_id = res_pedido.json()["id"]

    # 2. Processa Pagamento Mock
    payload_pagamento = {
        "forma_pagamento": "PIX"
    }
    res_pagamento = client.post(
        f"/api/v1/pedidos/{pedido_id}/pagamento-mock",
        json=payload_pagamento,
        headers=headers
    )

    assert res_pagamento.status_code == 200
    dados_pagamento = res_pagamento.json()
    assert dados_pagamento["status"] == StatusPedido.EM_PREPARACAO.value

    # 3. Consulta o pedido por GET para confirmar persistência e novo status
    res_consulta = client.get(f"/api/v1/pedidos/{pedido_id}", headers=headers)
    assert res_consulta.status_code == 200
    assert res_consulta.json()["status"] == StatusPedido.EM_PREPARACAO.value

    # 4. Confirmação direta via ORM SQLAlchemy no banco
    db.expire_all()
    pedido_final = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    assert pedido_final.status == StatusPedido.EM_PREPARACAO