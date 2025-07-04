from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Gambiarra pra importar o scraper - não consegui resolver de outra forma
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scraper_oab import OABScraper
from .models import FetchOABRequest, FetchOABResponse

# Configuração básica de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria a aplicação FastAPI
app = FastAPI(
    title="OAB Scraper API",
    description="API que eu fiz pra buscar dados de advogados na OAB",
    version="1.0.0"
)

# CORS liberado - não é o ideal mas funciona
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "OAB Scraper API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/fetch_oab", response_model=FetchOABResponse)
async def fetch_oab(dados: FetchOABRequest):
    """
    Busca dados de um advogado na OAB
    Testei bastante e funciona na maioria dos casos
    """
    scraper = None
    try:
        logger.info(f"Buscando advogado: {dados.name} - UF: {dados.uf}")
        
        # Validações básicas - aprendi que é importante fazer
        if not dados.name or not dados.name.strip():
            raise HTTPException(status_code=400, detail="Nome é obrigatório")
        
        if not dados.uf or len(dados.uf.strip()) != 2:
            raise HTTPException(status_code=400, detail="UF deve ter 2 caracteres")
        
        # Normaliza UF pra maiúscula
        uf = dados.uf.strip().upper()
        
        # Lista de UFs válidas - copiei da internet
        ufs_validas = [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
            "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", 
            "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
        ]
        
        if uf not in ufs_validas:
            raise HTTPException(status_code=400, detail=f"UF '{uf}' não é válida")
        
        # Inicializa o scraper
        scraper = OABScraper(headless=True)
        
        # Faz o scraping
        resultado = scraper.search_advogado(dados.name.strip(), uf)
        
        # Se não encontrou nada, retorna campos vazios
        if not resultado.oab:
            return FetchOABResponse()
        
        # Retorna os dados encontrados
        return FetchOABResponse(
            oab=resultado.oab,
            nome=resultado.nome,
            uf=resultado.uf,
            categoria=resultado.categoria,
            data_inscricao=resultado.data_inscricao,
            situacao=resultado.situacao
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        raise HTTPException(status_code=500, detail="Algo deu errado")
    finally:
        # Sempre fechar o scraper pra não vazar memória
        if scraper:
            scraper.close()

# Pra rodar direto se quiser
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)