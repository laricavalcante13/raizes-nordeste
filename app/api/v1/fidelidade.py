from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import ContaFidelidade, HistoricoFidelidade, Usuario
from app.api.deps import get_current_user
from app.schemas.usuario import (
    SaldoFidelidadeResponseSchema,
    ResgatarPontosSchema,
    TransacaoFidelidadeSchema,
)

router = APIRouter(prefix="/fidelidade", tags=["Programa de Fidelidade"])


def obter_ou_criar_conta_fidelidade(usuario_id: int, db: Session) -> ContaFidelidade:
    conta = db.query(ContaFidelidade).filter(ContaFidelidade.usuario_id == usuario_id).first()
    if not conta:
        conta = ContaFidelidade(usuario_id=usuario_id, saldo_pontos=0)
        db.add(conta)
        db.commit()
        db.refresh(conta)
    return conta

@router.get(
    "/saldo",
    response_model=SaldoFidelidadeResponseSchema,
    summary="Consultar saldo de pontos e histórico de uso do programa de fidelidade"
)
def consultar_saldo_fidelidade(
    page: int = Query(default=1, ge=1, description="Número da página do histórico"),
    limit: int = Query(default=10, ge=1, le=100, description="Itens do histórico por página"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    conta = obter_ou_criar_conta_fidelidade(usuario_atual.id, db)
    
    offset = (page - 1) * limit
    historico = (
        db.query(HistoricoFidelidade)
        .filter(HistoricoFidelidade.conta_id == conta.id)
        .order_by(HistoricoFidelidade.criado_em.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return SaldoFidelidadeResponseSchema(
        usuario_id=usuario_atual.id,
        saldo_pontos=conta.saldo_pontos,
        historico_recente=historico
    )


@router.post(
    "/resgatar",
    response_model=SaldoFidelidadeResponseSchema,
    summary="Resgatar pontos acumulados por cupons/recompensas"
)
def resgatar_pontos_fidelidade(
    payload: ResgatarPontosSchema,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    conta = obter_ou_criar_conta_fidelidade(usuario_atual.id, db)

    if conta.saldo_pontos < payload.pontos_para_resgatar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Saldo insuficiente. Você possui {conta.saldo_pontos} pontos."
        )

    #subtrai pontos
    conta.saldo_pontos -= payload.pontos_para_resgatar

    transacao = HistoricoFidelidade(
        conta_id=conta.id,
        quantidade_pontos=-payload.pontos_para_resgatar,
        tipo_operacao="RESGATE_RECOMPENSA",
        descricao=payload.descricao_recompensa
    )
    db.add(transacao)
    db.commit()
    db.refresh(conta)

    historico = (
        db.query(HistoricoFidelidade)
        .filter(HistoricoFidelidade.conta_id == conta.id)
        .order_by(HistoricoFidelidade.criado_em.desc())
        .limit(20)
        .all()
    )

    return SaldoFidelidadeResponseSchema(
        usuario_id=usuario_atual.id,
        saldo_pontos=conta.saldo_pontos,
        historico_recente=historico
    )