from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database import get_db
from app.domain.models import Pedido, LogAuditoria
from app.domain.enums import StatusPedido
from app.infrastructure.gateway_pagamento import Pagamento
from app.api.deps import get_current_user

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

class ProcessarPagamentoSchema(BaseModel):
    pedido_id: int
    forma_pagamento: str

@router.post(
        "/processar",
        summary="Processa pagamentos através de um gateway mock externo"
)

def processar_pagamento(
    payload: ProcessarPagamentoSchema, 
    db: Session = Depends(get_db),
    usuario_atual = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == payload.pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="O pedido não está no status AGUARDANDO_PAGAMENTO."
        )

    #executa pagamento externo
    result_pgto = Pagamento.processar_pagamento(
        pedido_id=pedido.id, 
        valor=pedido.valor_total, 
        forma_pagamento=payload.forma_pagamento
    )

    # atualiza o status do pedido com base na resposta do gateway de pagamento
    if result_pgto["status"] == "APROVADO":
        pedido.status = StatusPedido.EM_PREPARACAO
    else:
        pedido.status = StatusPedido.CANCELADO


    # log de auditoria
    log = LogAuditoria(
        acao="PROCESSAR_PAGAMENTO",
        usuario_id=usuario_atual.id,
        detalhes=f"Pagamento do Pedido #{pedido.id} {pedido.status_pagamento} via {payload.forma_pagamento} no valor de R$ {pedido.valor_total}."
    )
    db.add(log)

    db.commit()
    db.refresh(pedido)

    return {
        "mensagem": "Processamento de pagamento concluído.",
        "result_pgto": result_pgto,
        "novo_status_pedido": pedido.status
    }