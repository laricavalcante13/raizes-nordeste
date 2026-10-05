from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database import get_db
from app.domain.models import Pedido
from app.domain.enums import StatusPedido
from app.infrastructure.mock_pagamento import ServicoPagamentoMock
from app.api.deps import get_current_user

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

class ProcessarPagamentoSchema(BaseModel):
    pedido_id: int
    forma_pagamento: str

@router.post("/processar")
def processar_pagamento_mock(
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

    # Executa mock externo
    resultado_mock = ServicoPagamentoMock.processar_pagamento(
        pedido_id=pedido.id, 
        valor=pedido.valor_total, 
        forma_pagamento=payload.forma_pagamento
    )

    # Atualiza o status do pedido com base na resposta da API mock
    if resultado_mock["status"] == "APROVADO":
        pedido.status = StatusPedido.EM_PREPARACAO
    else:
        pedido.status = StatusPedido.CANCELADO

    db.commit()
    db.refresh(pedido)

    return {
        "mensagem": "Processamento de pagamento concluído.",
        "resultado_mock": resultado_mock,
        "novo_status_pedido": pedido.status
    }