import random

class ServicoPagamentoMock:
    @staticmethod
    def processar_pagamento(pedido_id: int, valor: float, forma_pagamento: str) -> dict:
        # Simula aprovação de pagamento no mock (retorna status e payload)
        # Para fins de teste, formas contendo "FALHA" resultam em recusa
        se_aprovado = "FALHA" not in forma_pagamento.upper()
        
        return {
            "transacao_id": f"MOCK-{random.randint(10000, 99999)}",
            "pedido_id": pedido_id,
            "status": "APROVADO" if se_aprovado else "RECUSADO",
            "mensagem": "Pagamento efetuado com sucesso" if se_aprovado else "Saldo insuficiente ou transação negada"
        }