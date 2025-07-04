"""
Agente pra processar consultas em linguagem natural
Feito com base no que aprendi sobre processamento de texto
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Log básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UFs do Brasil - lista que peguei na internet
UFS_BRASIL = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
}

class AgenteLLM:
    """Agente que usa Cloudflare - meio instável mas funciona"""
    
    def __init__(self):
        self.token = os.getenv('CF_API_TOKEN')
        self.account_id = os.getenv('CF_ACCOUNT_ID')
        
        if not self.token or not self.account_id:
            logger.warning("Sem credenciais Cloudflare - vai usar só o parser")
            self.ativo = False
        else:
            self.ativo = True
            
    def chamar_llm(self, texto: str) -> str:
        """Chama o LLM da Cloudflare"""
        if not self.ativo:
            return "Agente não configurado"
            
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/meta/llama-2-7b-chat-fp16"
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {
                        "role": "user",
                        "content": texto
                    }
                ]
            }
            
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            
            if resp.status_code == 200:
                result = resp.json()
                return result.get('result', {}).get('response', '')
            else:
                logger.error(f"Erro Cloudflare: {resp.status_code}")
                return "Erro no LLM"
                
        except Exception as e:
            logger.error(f"Erro: {str(e)}")
            return "Erro interno"

# Instância global
agente = AgenteLLM()

def parse_oab_query(texto: str) -> Dict[str, Any]:
    """
    Extrai nome e UF de uma consulta
    Função que mais me deu trabalho pra fazer
    """
    try:
        # Normaliza o texto
        texto = texto.strip().upper()
        
        # Padrões que tentei e funcionaram
        padroes = [
            # "nome: João Silva, uf: SP"
            r'NOME:\s*([^,]+),?\s*UF:\s*([A-Z]{2})',
            # "João Silva em SP"
            r'([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s]+)\s+EM\s+([A-Z]{2})',
            # "João Silva de SP"
            r'([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s]+)\s+DE\s+([A-Z]{2})',
            # "João Silva do Rio de Janeiro"
            r'([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s]+)\s+D[AO]\s+([A-Z\s]+)',
            # Palavras-chave
            r'(?:BUSQUE|CONSULTE|DADOS|ADVOGADO|DR\.?|DRA\.?)\s+([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s]+)',
        ]
        
        nome = None
        uf = None
        
        # Primeiro procura a UF
        for sigla, nome_completo in UFS_BRASIL.items():
            if sigla in texto:
                uf = sigla
                break
            if nome_completo.upper() in texto:
                uf = sigla
                break
        
        # Depois procura o nome
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                nome_encontrado = match.group(1).strip()
                
                # Limpa o nome
                nome_encontrado = re.sub(r'\b(?:BUSQUE|CONSULTE|DADOS|ADVOGADO|DR\.?|DRA\.?)\b', '', nome_encontrado)
                nome_encontrado = re.sub(r'\s+', ' ', nome_encontrado).strip()
                
                if len(nome_encontrado) >= 2:
                    nome = nome_encontrado
                    
                    # Se achou UF no padrão, usa ela
                    if len(match.groups()) >= 2:
                        uf_encontrada = match.group(2).strip()
                        if uf_encontrada in UFS_BRASIL:
                            uf = uf_encontrada
                    break
        
        # Se não achou nome, tenta extrair da query toda
        if not nome:
            limpo = re.sub(r'\b(?:BUSQUE|CONSULTE|DADOS|ADVOGADO|DR\.?|DRA\.?|PRECISO|DOS|DA|DO|O|A|EM|DE)\b', '', texto)
            limpo = re.sub(r'\b[A-Z]{2}\b', '', limpo)  # Remove UFs
            limpo = re.sub(r'\s+', ' ', limpo).strip()
            
            if len(limpo) >= 2:
                nome = limpo
        
        # Valores default
        if not nome:
            nome = "NOME_NAO_ENCONTRADO"
        if not uf:
            uf = "SP"  # Default SP
            
        return {
            'name': nome.title(),
            'uf': uf
        }
        
    except Exception as e:
        logger.error(f"Erro no parsing: {str(e)}")
        return {
            'name': 'ERRO_PARSING',
            'uf': 'SP'
        }

def fetch_oab_tool(nome: str, uf: str) -> Dict[str, Any]:
    """
    Busca na API da OAB
    Função simples que chama a API
    """
    try:
        url = "http://localhost:8000/fetch_oab"
        
        dados = {
            "name": nome,
            "uf": uf
        }
        
        resp = requests.post(url, json=dados, timeout=30)
        
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.error(f"Erro API: {resp.status_code}")
            return {
                "oab": None,
                "nome": None,
                "uf": None,
                "categoria": None,
                "data_inscricao": None,
                "situacao": None,
                "error": f"Erro HTTP {resp.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Erro na busca: {str(e)}")
        return {
            "oab": None,
            "nome": None,
            "uf": None,
            "categoria": None,
            "data_inscricao": None,
            "situacao": None,
            "error": str(e)
        }

def formatar_resposta(dados: Dict[str, Any]) -> str:
    """
    Formata a resposta de forma mais amigável
    """
    try:
        if dados.get('error'):
            return f"❌ **Erro:** {dados['error']}"
        
        if not dados.get('oab'):
            return "❌ **Advogado não encontrado** na OAB."
        
        resposta = f"✅ **Advogado encontrado:**\n\n"
        resposta += f"**Nome:** {dados.get('nome', 'N/A')}\n"
        resposta += f"**OAB:** {dados.get('oab', 'N/A')}\n"
        resposta += f"**UF:** {dados.get('uf', 'N/A')}\n"
        resposta += f"**Categoria:** {dados.get('categoria', 'N/A')}\n"
        resposta += f"**Situação:** {dados.get('situacao', 'N/A')}\n"
        
        if dados.get('data_inscricao'):
            resposta += f"**Data de Inscrição:** {dados['data_inscricao']}\n"
        
        resposta += f"\n_Consulta em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_"
        
        return resposta
        
    except Exception as e:
        logger.error(f"Erro ao formatar: {str(e)}")
        return f"❌ **Erro:** {str(e)}"

def run_agent(consulta: str) -> str:
    """
    Função principal do agente
    """
    try:
        logger.info(f"Processando: {consulta}")
        
        # 1. Fazer parsing da consulta
        parsed = parse_oab_query(consulta)
        logger.info(f"Parsing: {parsed}")
        
        # 2. Buscar na OAB
        dados_oab = fetch_oab_tool(parsed['name'], parsed['uf'])
        logger.info(f"Dados OAB: {dados_oab}")
        
        # 3. Formatar resposta
        resposta = formatar_resposta(dados_oab)
        
        # 4. Se o LLM estiver ativo, tenta melhorar a resposta
        if agente.ativo:
            prompt = f"""
            Você é um assistente para consultas da OAB.
            
            Consulta: {consulta}
            Dados: {json.dumps(dados_oab, indent=2)}
            
            Dê uma resposta profissional sobre o resultado.
            """
            
            resposta_llm = agente.chamar_llm(prompt)
            if resposta_llm and "erro" not in resposta_llm.lower():
                return resposta_llm
        
        return resposta
        
    except Exception as e:
        logger.error(f"Erro no agente: {str(e)}")
        return f"❌ **Erro:** {str(e)}"

# Função compatível com versões antigas
def run_simple_agent(consulta: str) -> str:
    """Mesma coisa que run_agent"""
    return run_agent(consulta)

# Teste direto
if __name__ == "__main__":
    # Alguns testes básicos
    testes = [
        "Busque o advogado João Silva em SP",
        "Preciso dos dados da Maria Santos do Rio de Janeiro",
        "nome: Ana Rosa, uf: MS",
        "Consulte Dr. Pedro Costa em MG"
    ]
    
    for teste in testes:
        print(f"\n{'='*50}")
        print(f"Teste: {teste}")
        print(f"{'='*50}")
        
        resultado = run_agent(teste)
        print(resultado)
