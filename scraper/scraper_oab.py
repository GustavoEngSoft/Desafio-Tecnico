import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class AdvogadoData:
    """Dados do advogado - usei dataclass pra facilitar"""
    oab: Optional[str] = None
    nome: Optional[str] = None
    uf: Optional[str] = None
    categoria: Optional[str] = None
    data_inscricao: Optional[str] = None
    situacao: Optional[str] = None

class OABScraper:
    """
    Scraper pra buscar advogados na OAB
    Foi um trabalho configurar o Chrome direitinho
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configura o Chrome - a parte mais chata"""
        options = Options()
        
        # Configurações básicas
        if self.headless:
            options.add_argument('--headless=new')  # Versão nova do headless
        
        # Configurações que aprendi serem importantes no Windows
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--window-size=1920,1080')
        
        # User agent pra não parecer bot
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Outras configurações que achei na internet
        options.add_argument('--disable-web-security')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--log-level=3')  # Reduz logs
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        try:
            # WebDriverManager baixa o driver automaticamente
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # Remove indicadores de automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome configurado")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar: {e}")
            # Configuração mais simples se der erro
            try:
                options_simple = Options()
                if self.headless:
                    options_simple.add_argument('--headless')
                options_simple.add_argument('--no-sandbox')
                options_simple.add_argument('--disable-dev-shm-usage')
                options_simple.add_argument('--window-size=1920,1080')
                
                service_simple = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service_simple, options=options_simple)
                self.driver.set_page_load_timeout(30)
                logger.info("ChromeDriver configurado com configuração simplificada")
                
            except Exception as e2:
                logger.error(f"Erro na configuração alternativa: {e2}")
                raise
    
    def search_advogado(self, name: str, uf: str) -> AdvogadoData:
        """Busca dados de um advogado no site da OAB"""
        try:
            logger.info(f"Iniciando busca para: {name} - UF: {uf}")
            
            # Verifica se o driver está funcionando
            if not self.driver:
                logger.error("Driver não inicializado")
                return AdvogadoData()
            
            # Navega para o site
            logger.info("Navegando para o site da OAB...")
            self.driver.get("https://cna.oab.org.br/")
            
            # Aguarda a página carregar
            wait = WebDriverWait(self.driver, 20)
            
            logger.info("Aguardando campo nome...")
            # Preenche o nome - usando o seletor correto
            nome_input = wait.until(
                EC.presence_of_element_located((By.NAME, "NomeAdvo"))
            )
            nome_input.clear()
            nome_input.send_keys(name)
            logger.info(f"Nome '{name}' inserido")
            
            logger.info("Selecionando UF...")
            # Seleciona a UF - usando o seletor correto
            uf_select = Select(wait.until(
                EC.presence_of_element_located((By.NAME, "Uf"))
            ))
            uf_select.select_by_value(uf.upper())
            logger.info(f"UF '{uf}' selecionada")
            
            logger.info("Clicando no botão pesquisar...")
            # Clica no botão de pesquisar - usando texto do botão
            buscar_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Pesquisar')]"))
            )
            buscar_btn.click()
            
            # Aguarda os resultados carregarem
            logger.info("Aguardando resultados...")
            time.sleep(7)  # Aumenta tempo de espera
            
            try:
                # Como o site não usa IDs/classes específicas, vamos pegar o body inteiro
                logger.info("Aguardando carregamento da página de resultados...")
                
                # Aguarda um pouco mais para garantir que a página carregou
                time.sleep(3)
                
                # Pega o body inteiro
                body_element = self.driver.find_element(By.TAG_NAME, "body")
                body_text = body_element.text
                
                logger.info(f"Texto da página capturado: {len(body_text)} caracteres")
                
                # Verifica se há resultados
                if any(indicator in body_text for indicator in [
                    "RESULTADO", "Nome:", "Inscrição:", "Tipo:", "UF:"
                ]):
                    logger.info("Indicadores de resultado encontrados")
                    return self._extract_data(body_element, uf)
                else:
                    logger.warning("Nenhum indicador de resultado encontrado")
                    return AdvogadoData()
                
            except Exception as e:
                logger.error(f"Erro ao buscar resultados: {e}")
                return AdvogadoData()
                
        except Exception as e:
            logger.error(f"Erro durante scraping: {e}")
            logger.error(f"Tipo do erro: {type(e).__name__}")
            # Tenta capturar screenshot para debug se não estiver em headless
            if not self.headless:
                try:
                    self.driver.save_screenshot("debug_error.png")
                    logger.info("Screenshot salvo: debug_error.png")
                except:
                    pass
            return AdvogadoData()
    
    def _extract_data(self, resultado_element, uf: str) -> AdvogadoData:
        """Extrai os dados do elemento de resultado baseado na estrutura real do site OAB"""
        try:
            dados = {}
            
            # Obtém o texto completo do elemento
            texto_completo = resultado_element.text
            
            # Se o texto está vazio, tenta buscar em elementos filhos
            if not texto_completo.strip():
                try:
                    # Busca em células de tabela
                    cells = resultado_element.find_elements(By.TAG_NAME, "td")
                    if cells:
                        texto_completo = " ".join([cell.text for cell in cells])
                    else:
                        # Busca em divs
                        divs = resultado_element.find_elements(By.TAG_NAME, "div")
                        texto_completo = " ".join([div.text for div in divs if div.text.strip()])
                except:
                    pass
            
            logger.info(f"Texto extraído: {texto_completo[:500]}...")
            
            # Verifica se há indicação de "nenhum resultado"
            if any(phrase in texto_completo.lower() for phrase in [
                "nenhum resultado", "não encontrado", "não foram encontrados", 
                "sem resultados", "resultado não encontrado"
            ]):
                logger.info("Nenhum resultado encontrado no texto")
                return AdvogadoData()
            
            # Busca por padrões específicos da estrutura da OAB
            # Padrão: Nome: FULANO DE TAL Tipo: ADVOGADO Inscrição: 123456 UF: SP
            
            # Extrai dados usando regex mais específico
            import re
            
            # Busca por Nome seguido de Tipo/Inscrição
            nome_pattern = r'Nome:\s*([A-ZÁÇÃÕÊÉÍ\s]+?)(?:\s+Tipo:|$)'
            nome_match = re.search(nome_pattern, texto_completo, re.IGNORECASE)
            if nome_match:
                dados['nome'] = nome_match.group(1).strip()
                logger.info(f"Nome extraído: {dados['nome']}")
            
            # Busca por Tipo
            tipo_pattern = r'Tipo:\s*([A-ZÁÇÃÕÊÉÍ\s]+?)(?:\s+Inscrição:|$)'
            tipo_match = re.search(tipo_pattern, texto_completo, re.IGNORECASE)
            if tipo_match:
                dados['categoria'] = tipo_match.group(1).strip()
                logger.info(f"Categoria extraída: {dados['categoria']}")
            
            # Busca por Inscrição (número OAB)
            insc_pattern = r'Inscrição:\s*(\d+)'
            insc_match = re.search(insc_pattern, texto_completo, re.IGNORECASE)
            if insc_match:
                dados['oab'] = insc_match.group(1).strip()
                logger.info(f"OAB extraído: {dados['oab']}")
            
            # Busca por UF
            uf_pattern = r'UF:\s*([A-Z]{2})'
            uf_match = re.search(uf_pattern, texto_completo, re.IGNORECASE)
            if uf_match:
                dados['uf'] = uf_match.group(1).strip().upper()
                logger.info(f"UF extraída: {dados['uf']}")
            
            # Se não encontrou dados estruturados, tenta parsing alternativo
            if not dados.get('nome') and not dados.get('oab'):
                logger.info("Tentando parsing alternativo...")
                
                # Divide o texto em linhas e processa
                linhas = texto_completo.split('\n')
                
                for linha in linhas:
                    linha = linha.strip()
                    if not linha:
                        continue
                    
                    # Procura por números que podem ser OAB
                    if re.search(r'\d{4,8}', linha):
                        numeros = re.findall(r'\d{4,8}', linha)
                        if numeros and not dados.get('oab'):
                            dados['oab'] = numeros[0]
                            logger.info(f"OAB extraído (alternativo): {dados['oab']}")
                    
                    # Procura por nomes (linhas com palavras capitalizadas)
                    if (re.search(r'^[A-ZÁÇÃÕÊÉÍ\s]+$', linha) and 
                        len(linha.split()) >= 2 and 
                        not dados.get('nome')):
                        dados['nome'] = linha.strip()
                        logger.info(f"Nome extraído (alternativo): {dados['nome']}")
            
            # Se ainda não encontrou nada, tenta uma busca mais ampla
            if not dados.get('nome') and not dados.get('oab'):
                logger.info("Tentando busca mais ampla...")
                
                # Busca por qualquer sequência de letras maiúsculas (provável nome)
                nomes_possiveis = re.findall(r'[A-ZÁÇÃÕÊÉÍ]{2,}(?:\s+[A-ZÁÇÃÕÊÉÍ]{2,})+', texto_completo)
                if nomes_possiveis:
                    dados['nome'] = nomes_possiveis[0].strip()
                    logger.info(f"Nome extraído (busca ampla): {dados['nome']}")
                
                # Busca por qualquer número de 4-8 dígitos (provável OAB)
                numeros_possiveis = re.findall(r'\b\d{4,8}\b', texto_completo)
                if numeros_possiveis:
                    dados['oab'] = numeros_possiveis[0]
                    logger.info(f"OAB extraído (busca ampla): {dados['oab']}")
            
            # Define valores padrão se não encontrados
            if not dados.get('categoria'):
                dados['categoria'] = 'Advogado'
            
            if not dados.get('situacao'):
                dados['situacao'] = 'Ativo'
            
            if not dados.get('uf'):
                dados['uf'] = uf.upper()
            
            # Log final dos dados extraídos
            logger.info(f"Dados finais extraídos: {dados}")
            
            return AdvogadoData(
                oab=dados.get('oab'),
                nome=dados.get('nome'),
                uf=dados.get('uf'),
                categoria=dados.get('categoria'),
                data_inscricao=dados.get('data_inscricao'),
                situacao=dados.get('situacao')
            )
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return AdvogadoData()
    
    def close(self):
        """Fecha o driver"""
        try:
            if self.driver:
                logger.info("Fechando ChromeDriver...")
                self.driver.quit()
                self.driver = None
                logger.info("ChromeDriver fechado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao fechar driver: {e}")
    
    def __del__(self):
        try:
            self.close()
        except:
            pass

def fetch_oab_data(headless: bool = True) -> OABScraper:
    """Factory function para criar instância do scraper"""
    return OABScraper(headless=headless)
