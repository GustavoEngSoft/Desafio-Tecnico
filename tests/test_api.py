import pytest
from fastapi.testclient import TestClient
from api.main import app

# Criei um cliente de teste pra testar os endpoints
client = TestClient(app)

def test_root_endpoint():
    # Testa se a página inicial funciona
    resp = client.get("/")
    assert resp.status_code == 200
    # Verifica se retorna a mensagem esperada
    assert resp.json() == {"message": "OAB Scraper API is running"}

def test_health_endpoint():
    # Endpoint de saúde - básico mas importante
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}

def test_fetch_oab_validation():
    # Aqui eu testo se a validação funciona com dados errados
    # Nome vazio deve dar erro
    resp = client.post("/fetch_oab", json={"name": "", "uf": "SP"})
    assert resp.status_code == 400
    
    # UF com só 1 letra também deve dar erro
    resp = client.post("/fetch_oab", json={"name": "João Silva", "uf": "S"})
    assert resp.status_code == 400

def test_fetch_oab_valid_request():
    # Teste com dados válidos - pode não achar o advogado mas a API deve funcionar
    resp = client.post("/fetch_oab", json={"name": "João Silva", "uf": "SP"})
    assert resp.status_code == 200
    # TODO: melhorar este teste, por enquanto só verifica se tem o campo success
    assert "success" in resp.json()

def test_agent_endpoint():
    # Testando o agente inteligente
    resp = client.post("/agent", json={"query": "Busque o advogado João Silva em SP"})
    assert resp.status_code == 200
    assert "response" in resp.json()
    assert "success" in resp.json()

def test_agent_validation():
    # Query vazia deve dar erro
    resp = client.post("/agent", json={"query": ""})
    assert resp.status_code == 400

# Testes do parser do agente - essa parte foi meio complicada de fazer
def test_parse_oab_query():
    from agent.agent_llm import parse_oab_query
    
    # Teste básico de parsing - espero que funcione
    resultado = parse_oab_query("Busque o advogado João Silva em SP")
    assert resultado["name"] == "João Silva"
    assert resultado["uf"] == "SP"
    
    # Outro teste com formato diferente
    resultado = parse_oab_query("Consulte Maria Santos do Rio de Janeiro")
    assert resultado["name"] == "Maria Santos"
    assert resultado["uf"] == "RJ"

def test_fetch_oab_tool():
    from agent.agent_llm import fetch_oab_tool
    
    # Teste da ferramenta - meio instável, depende da API estar rodando
    resultado = fetch_oab_tool("João Silva", "SP")
    assert isinstance(resultado, dict)  # Deve retornar um dict
    # Pelo menos deve ter as chaves básicas
    assert "oab" in resultado
