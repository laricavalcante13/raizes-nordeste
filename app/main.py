from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from app.api.v1 import pedidos, pagamentos

app = FastAPI(
    title="API Rede Raízes do Nordeste",
    version="1.0.0",
    description="API para gestão das unidades Raízes do Nordeste Restaurantes"
)

app.include_router(pedidos.router, prefix="/api/v1")
app.include_router(pagamentos.router, prefix="/api/v1")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "ERRO_INTERNO",
            "message": "Ocorreu um erro inesperado no servidor.",
            "details": [str(exc)],
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )