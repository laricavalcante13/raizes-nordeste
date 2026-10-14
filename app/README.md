=============================================================
----------- API Restaurantes Raízes do Nordeste ------------
=============================================================

API RESTful para gestão centralizada de autenticação de usuários e clientes, gestão de estoque e unidades, produtos e cardápio, pagamentos e programa de fidelidade para a rede de restaurantes Raízes do Nordeste.

Desenvolvido com Python 3.11+, FastAPI, SQLAlchemy e Pydantic v2.


1. Requisitos do Sistema
Certifique-se de ter instalados na sua máquina local ou servidor os seguintes componentes:

- Linguagem: Python 3.11 ou superior (recomendado 3.11 ou 3.12).
- Gerenciador de Pacotes: pip e ambiente virtual venv.
- Banco de Dados:
- Desenvolvimento / Testes: SQLite3 
- Produção: PostgreSQL 14+ ou MySQL 8.0+.
- Ferramentas de Testes de API: Postman, Insomnia ou cURL (opcional, documentação Swagger é integrada).


2. Estrutura do Projeto

.
  app/
   ├── api/
   │   ├── deps.py             # Dependências da API (JWT, RBAC)
   │   └── v1/                 # Endpoints
   │       ├── auth.py
   │       ├── usuarios.py
   │       ├── unidades.py
   │       ├── produtos.py
   │       ├── estoque.py
   │       ├── pedidos.py
   │       ├── pagamentos.py
   │       └── fidelidade.py
   ├── domain/
   │   ├── enums.py            # Enums do sistema (Perfil, Status, Canais)
   │   └── models.py           # Modelos ORM SQLAlchemy
   ├── infrastructure/
   │   └── database.py         # Conexão e Sessão do Banco de Dados
   |   └── mock_pagamento.py   # Processamento mock de pagamentos
   ├── schemas/                # Schemas de validação Pydantic v2
   ├── main.py                 # Ponto de entrada FastAPI e Exception Handlers
   ├── tests/                  # Testes unitários e de integração
   ├── seed.py                 # Script para inserir dados no banco de dados
   ├── .env.example            # Modelo de variáveis de ambiente
   ├── requirements.txt        # Dependências do projeto
   └── README.md               # Instruções de execução


3. Configuração de Variáveis de Ambiente

Crie um arquivo .env na raiz do projeto com base no arquivo .env.example.

Passo a passo no terminal:
Bash
# Copiar o arquivo de exemplo para criar o arquivo .env
cp .env.example .env
Conteúdo esperado do .env.example:
Snippet de código
# Configurações Gerais da Aplicação
APP_NAME="Rede Raízes do Nordeste"
DEBUG=True
API_V1_STR="/api/v1"

# Banco de Dados (SQLite por padrão para ambiente de dev)
DATABASE_URL="sqlite:///./raizes_nordeste.db"
# Para PostgreSQL em produção, utilize:
# DATABASE_URL="postgresql://usuario:senha@localhost:5432/raizes_nordeste"

# Segurança e Autenticação JWT
SECRET_KEY = "LOEMIPSUMBDJAJKAKVSDV_646DFBSF64_SDNOBOT562"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 


4. Instalação de Dependências
Recomenda-se criar e ativar um ambiente virtual (venv) antes de instalar as dependências.

Linux/macOS:
Bash
# 1. Criar o ambiente virtual
python3 -m venv venv

# 2. Ativar o ambiente virtual
source venv/bin/activate

# 3. Atualizar o pip e instalar as dependências
pip install --upgrade pip
pip install -r requirements.txt
No Windows (PowerShell / CMD):
PowerShell
# 1. Criar o ambiente virtual
python -m venv venv

# 2. Ativar o ambiente virtual
.\venv\Scripts\Activate.ps1

# 3. Atualizar o pip e instalar as dependências
python -m pip install --upgrade pip
pip install -r requirements.txt


5. Criação do Banco de Dados e Seeds

O projeto utiliza o SQLAlchemy com criação automática de tabelas no momento em que a aplicação é iniciada.

Inserindo dados no Banco com Dados Iniciais
Foi disponibilizado o arquivo seed.py para popular o banco de dados com:

- Usuários Padrão (Admin, Gerente, Atendente, Cozinha e Cliente).
- Unidades/Filiais da Rede Raízes do Nordeste.
- Categorias e Produtos com cardápio típico regional.
- Estoque Inicial cadastrado por unidade.

Execute o script com o ambiente virtual ativo:

Bash
python seed.py

Credenciais de Teste Geradas pelo Seed:

Admin: admin@raizesnordeste.com.br / admin123
Gerente: gerente.matriz@raizesnordeste.com.br / gerente123
Atendente: atendimento.matriz@raizesnordeste.com.br / atendente123
Cozinha: cozinha.matriz@raizesnordeste.com.br / cozinha123
Cliente: larissa.cruz@email.com / cliente123


6. Execução da API
Para iniciar o servidor HTTP de desenvolvimento utilizando o Uvicorn:

Bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Se preferir rodar via Python direto:

Bash
python -m uvicorn app.main:app --reload
A API estará acessível em: http://localhost:8000

7. Acesso à Documentação (Swagger / OpenAPI)
Com o servidor rodando, acesse as documentações interativas geradas automaticamente pelo FastAPI no navegador:

Swagger UI (Recomendado): http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

OpenAPI Schema (JSON): http://localhost:8000/openapi.json

Como autenticar no Swagger:
Acesse http://localhost:8000/docs.

Clique no botão Authorize (cadeado no canto superior direito).

Faça requisição no endpoint POST /api/v1/auth/login com as credenciais acima para obter o access_token.

Insira o Token no modal do Swagger ou cole a credencial de login direto na autenticação OAuth2 da página.

8. Execução de Testes Automatizados
Os testes automatizados cobrem autenticação, validações do Pydantic, isolamento por perfis (RBAC), operações KDS e fluxo financeiro do programa de fidelidade.

Para rodar a suíte completa de testes utilizando o pytest:

Bash
# Rodar todos os testes
pytest

# Rodar os testes com exibição detalhada (verbose)
pytest -v

# Rodar os testes exibindo o relatório de cobertura de código
pytest --cov=app --cov-report=term-missing