from fastapi import APIRouter, Depends, HTTPException, status
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


# -----------------------------------------------------------------------------
# Consultar Saldo e Extrato de Pontos
# -----------------------------------------------------------------------------
@router.get(
    "/saldo",
    response_model=SaldoFidelidadeResponseSchema,
    summary="Consultar saldo de pontos e extrato do cliente logado"
)
def consultar_saldo_fidelidade(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user)
):
    conta = obter_ou_criar_conta_fidelidade(usuario_atual.id, db)
    
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


# -----------------------------------------------------------------------------
# Resgatar Pontos por Recompensas
# -----------------------------------------------------------------------------
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

    # Deduz pontos e lança histórico
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