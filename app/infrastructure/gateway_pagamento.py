from http.client import HTTPException
import random

class Pagamento:
  @staticmethod
  def processar_pagamento(
      pedido_id: int,
      forma_pagamento: str,
      numero_cartao: str = None,
      chave_pix: str = None,) -> dict:
    forma = forma_pagamento.upper()

    if not numero_cartao and not chave_pix:
      raise HTTPException(
          status_code=400,
          detail=(
              "Erro: Informe os dados para pagamento: número do cartão ou chave PIX."
          ),
      )

    # regra de recusa para CARTÃO
    if "CARTAO" in forma and (
        numero_cartao == "0000-0000-0000-0000" or "ERRO" in (numero_cartao or "")
    ):
      raise HTTPException(
          status_code=400, detail="Transação não autorizada."
      )

    # regra de recusa para PIX
    if forma == "PIX" and (
        chave_pix == "erro@pix.com" or "ERRO" in (chave_pix or "").upper()
    ):
      raise HTTPException(
          status_code=400, detail="Transação não autorizada."
      )

    if "ERRO" in forma:
      raise HTTPException(
          status_code=400, detail="Transação não autorizada."
      )
        
    return {
        "transacao_id": f"ExpressWayPayment-{random.randint(10000, 99999)}",
        "pedido_id": pedido_id,
        "forma_pagamento": forma_pagamento,
        "status": "APROVADO",
        "mensagem": "Transação autorizada com sucesso."
    }