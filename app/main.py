from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

from app.api.v1 import pedidos, pagamentos, usuarios, auth, estoque, produtos, unidades, fidelidade
from app.infrastructure.database import Base, engine

app = FastAPI(
    title="API Restaurantes Raízes do Nordeste",
    version="1.0.0",
    description="API para gestão dos restaurantes Raízes do Nordeste"
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(produtos.router, prefix="/api/v1")
app.include_router(pedidos.router, prefix="/api/v1")
app.include_router(pagamentos.router, prefix="/api/v1")
app.include_router(estoque.router, prefix="/api/v1")
app.include_router(unidades.router, prefix="/api/v1")
app.include_router(fidelidade.router, prefix="/api/v1")

STATUS_CODE_MAP = {
    400: ("BAD_REQUEST", "Requisição inválida."),
    401: ("UNAUTHORIZED", "Não autorizado. Token ausente ou inválido."),
    403: ("FORBIDDEN", "Acesso negado. Você não tem permissão para acessar este recurso."),
    404: ("NOT_FOUND", "O recurso solicitado não foi encontrado."),
    405: ("METHOD_NOT_ALLOWED", "Método HTTP não permitido para esta rota."),
    409: ("CONFLICT", "Conflito de estado no recurso solicitado."),
    422: ("VALIDATION_ERROR", "Dados de entrada inválidos."),
    500: ("INTERNAL_SERVER_ERROR", "Ocorreu um erro interno no servidor."),
    503: ("SERVICE_UNAVAILABLE", "Serviço temporariamente indisponível."),
    504: ("GATEWAY_TIMEOUT", "Tempo limite de resposta excedido (Timeout)."),
}


#tratador para exceções HTTP disparadas com raise HTTPException
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_code, default_msg = STATUS_CODE_MAP.get(
        exc.status_code, 
        ("HTTP_ERROR", "Ocorreu um erro na requisição.")
    )
    
    # Se uma mensagem específica foi passada no 'detail', o sistema usa; senão, o sistema usa a mensagem padrão
    message = exc.detail if isinstance(exc.detail, str) else default_msg
    details = exc.detail if not isinstance(exc.detail, str) else [exc.detail]

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_code,
            "message": message,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path
        }
    )


#tratador para erros de validação do Pydantic 
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Erros de validação nos dados enviados.",
            "details": exc.errors(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path
        }
    )


#tratador genérico para 500
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Ocorreu um erro inesperado no servidor.",
            "details": [str(exc)],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path
        }
    )

Base.metadata.create_all(bind=engine)