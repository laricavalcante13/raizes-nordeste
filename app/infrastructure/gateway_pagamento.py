from http.client import HTTPException
import random

class Pagamento:
  @staticmethod
  def processar_pagamento(
      pedido_id: int,
      forma_pagamento: str,
      info_pagamento: dict = None,
  ) -> dict:
 
    info_pagamento = info_pagamento or {}
    forma = forma_pagamento.upper()

    # Regra de recusa para CARTÃO
    numero_cartao = info_pagamento.get("numero_cartao", "")
    if "CARTAO" in forma and (
        numero_cartao == "0000-0000-0000-0000" or "ERRO" in numero_cartao
    ):
      raise HTTPException(
          status_code=400,
          detail=(
              "Transação não autorizada."
          ),
      )

    # regra de recusa para PIX
    chave_pix = info_pagamento.get("chave_pix", "")
    if forma == "PIX" and (
        chave_pix == "erro@pix.com" or "ERRO" in chave_pix.upper()
    ):
      raise HTTPException(
          status_code=400,
          detail="Transação não autorizada.",
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