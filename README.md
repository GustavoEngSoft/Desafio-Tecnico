# 🚀 Sistema de Busca de Advogados na OAB

Projeto que desenvolvi para buscar dados de advogados na OAB usando web scraping e processamento de linguagem natural.

## 📋 O que o sistema faz

Criei um sistema que:
- **API REST** para consultar dados de advogados
- **Web Scraper** que acessa o site oficial da OAB
- **Agente inteligente** que entende perguntas em português
- **Containerização** com Docker para facilitar o deploy

## 🏗️ Como funciona

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agente LLM    │    │   API REST      │    │  Web Scraper    │
│                 │    │                 │    │                 │
│ • Processa      │───▶│ • FastAPI       │───▶│ • Selenium      │
│   perguntas     │    │ • Validação     │    │ • Chrome        │
│ • Cloudflare    │    │ • JSON          │    │ • Site OAB      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Como executar o projeto

### O que você precisa ter instalado
- **Python 3.11+**
- **Docker e Docker Compose** (recomendo usar)
- **Chrome** (para o scraper funcionar)
- **Conta Cloudflare** (opcional, só se quiser usar o LLM)

### 1. Configurar as credenciais (opcional)

Se quiser usar o agente LLM, crie um arquivo `.env`:

```powershell
# Copiar o exemplo
Copy-Item .env.example .env

# Ou criar manualmente
New-Item -ItemType File -Name .env
```

Adicione suas credenciais da Cloudflare:

```env
CF_API_TOKEN=seu_token_aqui
CF_ACCOUNT_ID=seu_account_id_aqui
```

### 2. Rodar com Docker (mais fácil)

```powershell
# Baixar e rodar tudo
docker-compose up --build

# Ou rodar em background
docker-compose up -d --build

# Ver se está funcionando
docker-compose ps

# Parar tudo
docker-compose down
```

### 3. Rodar local (se não quiser usar Docker)

```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows)
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar a API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🧪 Como testar se está funcionando

### Teste básico
```powershell
# Ver se a API está no ar
curl http://localhost:8000/health

# Documentação automática
# http://localhost:8000/docs
```

### Testar o scraper

```powershell
# Busca básica
curl -X POST "http://localhost:8000/fetch_oab" -H "Content-Type: application/json" -d "{\"name\": \"Maria Silva\", \"uf\": \"SP\"}"
```

**Se funcionar, vai retornar algo assim:**
```json
{
  "oab": "19051",
  "nome": "ANA CAROLINA GUEDES ROSA CURY",
  "uf": "MS",
  "categoria": "ADVOGADA",
  "situacao": "Ativo"
}
```

### Testar o agente inteligente

```python
# Abrir o Python e testar
from agent.agent_llm import run_agent

# Perguntas que o agente entende
resultado = run_agent("Busque o advogado Maria Silva em SP")
print(resultado)
```

## 📁 Estrutura do projeto

```
Desafio-Tecnico/
├── api/                    # API REST
│   ├── main.py            # Servidor principal
│   └── models.py          # Modelos de dados
├── scraper/               # Web Scraper
│   └── scraper_oab.py     # Scraper do site da OAB
├── agent/                 # Agente inteligente
│   └── agent_llm.py       # Agente com IA
├── tests/                 # Testes
│   └── test_api.py        # Testes da API
├── docker-compose.yml     # Configuração Docker
├── Dockerfile            # Imagem Docker
├── requirements.txt      # Dependências Python
└── README.md            # Este arquivo
```

## 🔧 Tecnologias que usei

### Backend:
- **FastAPI** - Framework web moderno
- **Selenium** - Automação do navegador
- **Cloudflare AI** - Modelo de linguagem

### DevOps:
- **Docker** - Containerização
- **pytest** - Testes automatizados

## 🐛 Problemas que podem acontecer

### Chrome não encontrado:
```powershell
docker-compose build --no-cache
docker-compose up
```

### Site da OAB fora do ar:
```powershell
curl -I https://cna.oab.org.br/
```

## 🎯 Resumo do que aprendi

Esse projeto me ensinou muito sobre:
- **Web Scraping** com Selenium
- **APIs REST** com FastAPI
- **Processamento de linguagem natural**
- **Containerização** com Docker
- **Tratamento de erros** e validações
- **Testes automatizados**

O sistema está funcional e pronto para uso! 🎉

## 🚀 Quick Start

1. **Clone:**
```powershell
git clone <repositorio>
cd Desafio-Tecnico
```

2. **Execute:**
```powershell
docker-compose up --build
```

3. **Teste:**
```powershell
curl http://localhost:8000/health
```

4. **API:** http://localhost:8000/docs
