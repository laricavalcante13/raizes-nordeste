from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.infrastructure.database import get_db
from app.domain.models import Pedido, ItemPedido, Produto, Usuario
from app.domain.enums import CanalPedido, StatusPedido
from app.schemas.pedido import PedidoCreate, PedidoResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    payload: PedidoCreate, 
    db: Session = Depends(get_db), 
    usuario_atual: Usuario = Depends(get_current_user)
):
    if not payload.itens:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="O pedido deve conter ao menos um item."
        )

    valor_total = 0.0
    itens_para_criar = []

    for item in payload.itens:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Produto ID {item.produto_id} não encontrado."
            )
        
        subtotal = produto.preco * item.quantidade
        valor_total += subtotal
        itens_para_criar.append(
            ItemPedido(
                produto_id=produto.id,
                quantidade=item.quantidade,
                preco_unitario=produto.preco
            )
        )

    novo_pedido = Pedido(
        cliente_id=usuario_atual.id,
        unidade_id=payload.unidade_id,
        canal_pedido=payload.canal_pedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        valor_total=valor_total,
        itens=itens_para_criar
    )

    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido

@router.get("", response_model=List[PedidoResponse])
def listar_pedidos(
    canal_pedido: Optional[CanalPedido] = Query(None, alias="canalPedido"), # Suporte ao filtro por canal
    status_pedido: Optional[StatusPedido] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    query = db.query(Pedido)
    if canal_pedido:
        query = query.filter(Pedido.canal_pedido == canal_pedido)
    if status_pedido:
        query = query.filter(Pedido.status == status_pedido)
    
    return query.all()