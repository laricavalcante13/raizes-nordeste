from typing import List
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import (
    Pedido, ItemPedido, Produto, EstoqueUnidade, Unidade, Usuario,
    ContaFidelidade, HistoricoFidelidade, LogAuditoria
)
from app.domain.enums import StatusPedido, StatusPagamento, PerfilUsuario, CanalPedido
from app.api.deps import get_current_user, exigir_perfil
from app.schemas.pedido import (
    PedidoCreateSchema, PedidoResponseSchema, 
    PedidoCozinhaResponseSchema,
    ItemCozinhaResponseSchema,
    AtualizarStatusCozinhaResponseSchema,
    RelatorioVendasResponseSchema,
    VendasCanalItemSchema,
)

router = APIRouter(prefix="/pedidos", tags=["Gestão de Pedidos"])

FATOR_CONVERSAO_DESCONTO = Decimal("0.05") 

def obter_ou_criar_conta_fidelidade(usuario_id: int, db: Session) -> ContaFidelidade:
    conta = db.query(ContaFidelidade).filter(ContaFidelidade.usuario_id == usuario_id).first()
    if not conta:
        conta = ContaFidelidade(usuario_id=usuario_id, saldo_pontos=0)
        db.add(conta)
        db.flush()
    return conta


@router.post("", response_model=PedidoResponseSchema, status_code=status.HTTP_201_CREATED, summary="Criar novo pedido")
def criar_pedido(
    payload: PedidoCreateSchema,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    unidade = db.query(Unidade).filter(Unidade.id == payload.unidade_id, Unidade.ativo == True).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade informada não encontrada ou inativa.")

    # calcular o valor total dos produtos e validar estoque
    subtotal_pedido = Decimal("0.00")
    itens_para_inserir = []

    for item in payload.itens:
        produto = db.query(Produto).filter(Produto.id == item.produto_id, Produto.ativo == True).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto ID {item.produto_id} não encontrado.")

        estoque = db.query(EstoqueUnidade).filter(
            EstoqueUnidade.unidade_id == payload.unidade_id,
            EstoqueUnidade.produto_id == item.produto_id
        ).first()

        if not estoque or estoque.quantidade < item.quantidade:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente para o produto '{produto.nome}'. Disponível: {estoque.quantidade if estoque else 0}"
            )

        # Baixa no estoque
        estoque.quantidade -= item.quantidade
        item_subtotal = Decimal(str(produto.preco)) * item.quantidade
        subtotal_pedido += item_subtotal

        itens_para_inserir.append((produto, item.quantidade, item_subtotal))

    # Processar Desconto de Fidelidade
    desconto = Decimal("0.00")
    pontos_utilizados = 0

    if payload.pontos_para_usar and payload.pontos_para_usar > 0:
        conta = obter_ou_criar_conta_fidelidade(usuario_atual.id, db)
        if conta.saldo_pontos < payload.pontos_para_usar:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Saldo de pontos insuficiente. Saldo atual: {conta.saldo_pontos} pontos."
            )

        desconto_calculado = Decimal(str(payload.pontos_para_usar)) * FATOR_CONVERSAO_DESCONTO
        # O desconto não pode ser maior do que o valor total do pedido
        desconto = min(desconto_calculado, subtotal_pedido)
        pontos_utilizados = payload.pontos_para_usar

        # Deduzir os pontos da conta do cliente
        conta.saldo_pontos -= pontos_utilizados
        db.add(HistoricoFidelidade(
            conta_id=conta.id,
            quantidade_pontos=-pontos_utilizados,
            tipo_operacao="USO_PEDIDO",
            descricao=f"Pontos abatidos no pedido (Desconto: R$ {desconto:.2f})"
        ))

    valor_final_pedido = max(Decimal("0.00"), subtotal_pedido - desconto)

    novo_pedido = Pedido(
        cliente_id=usuario_atual.id,
        unidade_id=payload.unidade_id,
        canal_venda=payload.canal_venda,
        observacao=payload.observacao,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        status_pagamento=StatusPagamento.AGUARDANDO,
        valor_total=valor_final_pedido,
        desconto_aplicado=desconto,
        pontos_utilizados=pontos_utilizados
    )
    db.add(novo_pedido)
    db.flush()

    for produto, quantidade, subtotal_item in itens_para_inserir:
        db.add(ItemPedido(
            pedido_id=novo_pedido.id,
            produto_id=produto.id,
            quantidade=quantidade,
            preco=produto.preco,
            subtotal=subtotal_item
        ))

    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido


@router.get("", response_model=List[PedidoResponseSchema], summary="Listar pedidos")
def listar_pedidos(
    page: int = Query(default=1, ge=1, description="Número da página"),
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    query = db.query(Pedido)

    if usuario_atual.perfil not in [PerfilUsuario.GERENTE, PerfilUsuario.ADMIN, PerfilUsuario.ATENDENTE]:
        query = query.filter(Pedido.cliente_id == usuario_atual.id)

    offset = (page - 1) * limit
    return query.order_by(Pedido.criado_em.desc()).offset(offset).limit(limit).all()


@router.get(
    "/vendas-por-canal",
    response_model=RelatorioVendasResponseSchema,
    summary="Relatório de pedidos por canal de venda"
)
def consultar_relatorio_vendas_por_canal(
    unidade_id: int | None = Query(default=None, description="Filtrar por ID da Unidade/Filial"),
    data_inicio: str | None = Query(default=None, description="Data inicial no formato YYYY-MM-DD"),
    data_fim: str | None = Query(default=None, description="Data final no formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]))
):
    query = db.query(Pedido).filter(
        Pedido.status_pagamento == StatusPagamento.APROVADO,
        Pedido.status != StatusPedido.CANCELADO
    )

    if unidade_id is not None:
        query = query.filter(Pedido.unidade_id == unidade_id)

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Pedido.criado_em >= dt_inicio)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data_inicio inválido. Use YYYY-MM-DD."
            )

    if data_fim:
        try:
            dt_fim = datetime.strptime(f"{data_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")
            query = query.filter(Pedido.criado_em <= dt_fim)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data_fim inválido. Use YYYY-MM-DD."
            )

    pedidos = query.all()

    agregado = {canal: {"qtd": 0, "total": Decimal("0.00")} for canal in CanalPedido}
    faturamento_geral = Decimal("0.00")
    total_pedidos = len(pedidos)

    for p in pedidos:
        agregado[p.canal_venda]["qtd"] += 1
        agregado[p.canal_venda]["total"] += Decimal(str(p.valor_total))
        faturamento_geral += Decimal(str(p.valor_total))

    vendas_por_canal = [
        VendasCanalItemSchema(
            canal_venda=canal,
            quantidade_pedidos=dados["qtd"],
            faturamento_total=dados["total"]
        )
        for canal, dados in agregado.items()
    ]

    return RelatorioVendasResponseSchema(
        unidade_id=unidade_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        faturamento_geral=faturamento_geral,
        total_pedidos=total_pedidos,
        vendas_por_canal=vendas_por_canal
    )




@router.get("/{pedido_id}", response_model=PedidoResponseSchema, summary="Obter detalhes do pedido")
def obter_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    if pedido.cliente_id != usuario_atual.id and usuario_atual.perfil not in [PerfilUsuario.GERENTE, PerfilUsuario.ADMIN, PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA]:
        raise HTTPException(status_code=403, detail="Acesso negado aos detalhes deste pedido.")

    return pedido


@router.post("/{pedido_id}/cancelar", response_model=PedidoResponseSchema, summary="Cancelar Pedido")
def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    if pedido.cliente_id != usuario_atual.id and usuario_atual.perfil not in [PerfilUsuario.GERENTE, PerfilUsuario.ADMIN]:
        raise HTTPException(status_code=403, detail="Acesso negado para cancelar este pedido.")

    if pedido.status in [StatusPedido.CONCLUIDO]:
        raise HTTPException(status_code=400, detail="Pedidos concluídos/entregues não podem ser cancelados.")

    if pedido.status == StatusPedido.CANCELADO:
        raise HTTPException(status_code=400, detail="Este pedido já foi cancelado.")

    # estorno de Estoque
    for item in pedido.itens:
        estoque = db.query(EstoqueUnidade).filter(
            EstoqueUnidade.unidade_id == pedido.unidade_id,
            EstoqueUnidade.produto_id == item.produto_id
        ).first()
        if estoque:
            estoque.quantidade += item.quantidade

    # Estorno dos pontos de fidelidade utilizados no pedido
    conta = obter_ou_criar_conta_fidelidade(pedido.cliente_id, db)

    if pedido.pontos_utilizados > 0:
        conta.saldo_pontos += pedido.pontos_utilizados
        db.add(HistoricoFidelidade(
            conta_id=conta.id,
            quantidade_pontos=pedido.pontos_utilizados,
            tipo_operacao="ESTORNO_CANCELAMENTO",
            descricao=f"Devolução de pontos devido ao cancelamento do Pedido #{pedido.id}"
        ))

    # reverter pontos acumulados caso o pedido já tivesse sido pago
    if pedido.status_pagamento == StatusPagamento.APROVADO:
        pontos_para_remover = int(pedido.valor_total)
        conta.saldo_pontos = max(0, conta.saldo_pontos - pontos_para_remover)
        db.add(HistoricoFidelidade(
            conta_id=conta.id,
            quantidade_pontos=-pontos_para_remover,
            tipo_operacao="ESTORNO_PONTOS_PAGOS",
            descricao=f"Cancelamento de acúmulo referente ao Pedido #{pedido.id}"
        ))

    pedido.status = StatusPedido.CANCELADO
    db.commit()
    db.refresh(pedido)

    #log auditoria
    log = LogAuditoria(
        acao="CANCELAR_PEDIDO",
        usuario_id=usuario_atual.id,
        detalhes=f"Pedido {pedido.id} cancelado por {usuario_atual.email}."
    )
    db.add(log)
    
    db.commit()
    db.refresh(pedido)

    return Pedido

@router.get(
    "/unidades/{unidade_id}/fila-cozinha",
    response_model=List[PedidoCozinhaResponseSchema],
    summary="Consultar pedidos em preparação"
)
def visualizar_fila_kds(
    unidade_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(
        exigir_perfil([PerfilUsuario.COZINHA, PerfilUsuario.ATENDENTE, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN])
    )
):
    pedidos_db = (
        db.query(Pedido)
        .filter(
            Pedido.unidade_id == unidade_id,
            Pedido.status == StatusPedido.EM_PREPARACAO
        )
        .order_by(Pedido.criado_em.asc())
        .all()
    )

    resultado = []
    for pedido in pedidos_db:
        itens_formatados = []
        for item in pedido.itens:
            produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
            itens_formatados.append(
                ItemCozinhaResponseSchema(
                    produto_id=item.produto_id,
                    produto_nome=produto.nome if produto else "Produto Removido",
                    quantidade=item.quantidade
                )
            )

        resultado.append(
            PedidoCozinhaResponseSchema(
                id=pedido.id,
                unidade_id=pedido.unidade_id,
                canal_venda=pedido.canal_venda,
                status=pedido.status,
                observacao=pedido.observacao,
                criado_em=pedido.criado_em,
                itens=itens_formatados
            )
        )

    return resultado


@router.patch(
    "/{pedido_id}/pronto",
    response_model=AtualizarStatusCozinhaResponseSchema,
    summary="Atualizar status do pedido para PRONTO"
)
def marcar_pedido_pronto(
    pedido_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(
        exigir_perfil([PerfilUsuario.COZINHA, PerfilUsuario.ATENDENTE, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN])
    )
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    if pedido.status != StatusPedido.EM_PREPARACAO:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível marcar como PRONTO um pedido com status '{pedido.status.value}'."
        )

    pedido.status = StatusPedido.PRONTO
    db.commit()

    return AtualizarStatusCozinhaResponseSchema(
        pedido_id=pedido.id,
        novo_status=pedido.status,
        mensagem="Pedido finalizado na cozinha e pronto para entrega/retirada!"
    )


@router.patch(
    "/{pedido_id}/entregar",
    response_model=AtualizarStatusCozinhaResponseSchema,
    summary="Atualizar status do pedido para ENTREGUE/CONCLUÍDO"
)
def marcar_pedido_entregue(
    pedido_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(
        exigir_perfil([PerfilUsuario.ATENDENTE, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN])
    )
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    if pedido.status not in [StatusPedido.PRONTO]:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível concluir um pedido no status '{pedido.status.value}'. Ele precisa estar PRONTO primeiro."
        )

    pedido.status = StatusPedido.CONCLUIDO
    db.commit()

    return AtualizarStatusCozinhaResponseSchema(
        pedido_id=pedido.id,
        novo_status=pedido.status,
        mensagem="Pedido entregue com sucesso!"
    )


