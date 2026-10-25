# Rede de restaurantes Raízes do Nordeste - API Backend

API RESTful desenvolvida em FastAPI para gerenciamento e processamento de pedidos e pagamentos da rede de restaurantes **Rede Raízes do Nordeste**.

## Tecnologias Utilizadas

* **Python 3.10+**
* **FastAPI** 
* **SQLAlchemy** (ORM para gerenciamento do banco de dados relacional)
* **Pydantic** (Validação de dados e tipagem)
* **Uvicorn** (Servidor ASGI)
* **JWT (JSON Web Tokens)** (Autenticação segura)


## Funcionalidades

* **Autenticação e Autorização**: Rotas protegidas via tokens JWT e controle de usuários.
* **Gestão de Pedidos**: Validação de status (ex: `AGUARDANDO_PAGAMENTO`, `EM_PREPARACAO`, `CANCELADO`).
* **Processamento de Pagamentos**: 
  * Suporte a múltiplos métodos (`CARTAO_DEBITO`, `CARTAO_CREDITO`  e `PIX`) através de campos explícitos e schemas validados.
  * Simulação de Gateway integrado para testes de autorização e recusa de transações.
* **Auditoria**: Logs automáticos de ações críticas no sistema.
* **Documentação Automática**: Swagger UI (`/docs`) integrado nativamente.


## Estrutura do projeto

- **raizes-nordeste/**
  - **app/**
    - `api/v1/` - Rotas e endpoints da API
    - `core/` - Configurações globais e segurança
    - `infrastructure/` - Simulação de Gateway externo e serviços
    - `models/` - Modelos do SQLAlchemy (Banco de dados)
    - `schemas/` - Schemas do Pydantic (Validação de Payload)
    - `main.py` - Ponto de entrada da aplicação FastAPI
    - `postman/` - Coleção de testes realizados no Postman
  - `venv/` - Ambiente virtual Python
  - `requirements.txt` - Dependências do projeto
  - `README.md` - Documentação principal


## Como Executar o Projeto

### 1. Clonar o repositório
```bash
git clone https://github.com/laricavalcante13/raizes-nordeste.git
cd raizes-nordeste
```
### 2. Criar e ativar o ambiente
```bash
python -m venv venv

venv\Scripts\activate (Windows)
source venv/bin/activate (Linux)
```
### 3. Instalar dependências
```bash
pip install -r requirements.txt
```
### 4. Popular o banco de dados
```bash
python -m app.seed
```
### 5. Executar a aplicação
```bash
uvicorn app.main:app --reload
```
A API estará acessível em: http://localhost:8000
A documentação do Swagger UI poderá ser acessada em: http://localhost:8000/docs

