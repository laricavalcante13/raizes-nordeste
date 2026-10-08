from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.models import Unidade, Produto, Categoria, EstoqueUnidade
from app.schemas.cardapio import CardapioUnidadeResponseSchema, ProdutoCardapioSchema

router = APIRouter(prefix="/cardapio", tags=["Cardápio e Pré-Pedido"])

# =============================================================================
# UC11: Consultar Cardápio por Unidade
# UC12: Filtrar Produtos por Categoria
# =============================================================================
@router.get(
    "/unidades/{unidade_id}",
    response_model=CardapioUnidadeResponseSchema,
    summary="UC11 e UC12: Consultar Cardápio da Unidade com filtros"
)
def consultar_cardapio_unidade(
    unidade_id: int,
    categoria_id: Optional[int] = Query(None, description="UC12: Filtrar produtos por ID da Categoria"),
    apenas_disponiveis: bool = Query(True, description="Exibir apenas produtos com estoque disponível (>0)"),
    db: Session = Depends(get_db)
):
    # Validar existência da unidade
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id, Unidade.ativo == True).first()
    if not unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada ou inativa."
        )

    # Consulta dos produtos associados ao estoque da unidade
    query = db.query(
        Produto, Categoria, EstoqueUnidade
    ).join(
        Categoria, Produto.categoria_id == Categoria.id
    ).join(
        EstoqueUnidade, Produto.id == EstoqueUnidade.produto_id
    ).filter(
        EstoqueUnidade.unidade_id == unidade_id,
        Produto.ativo == True
    )

    # UC12: Filtro opcional por Categoria
    if categoria_id:
        query = query.filter(Produto.categoria_id == categoria_id)

    # Filtro opcional de disponibilidade de estoque
    if apenas_disponiveis:
        query = query.filter(EstoqueUnidade.quantidade > 0)

    resultados = query.all()

    produtos_resposta = []
    for produto, categoria, estoque in resultados:
        produtos_resposta.append(
            ProdutoCardapioSchema(
                id=produto.id,
                nome=produto.nome,
                descricao=produto.descricao,
                preco_base=produto.preco_base,
                categoria_id=categoria.id,
                categoria_nome=categoria.nome,
                quantidade_estoque=estoque.quantidade,
                disponivel=estoque.quantidade > 0
            )
        )

    return CardapioUnidadeResponseSchema(
        unidade_id=unidade.id,
        unidade_nome=unidade.nome,
        total_itens=len(produtos_resposta),
        produtos=produtos_resposta
    )