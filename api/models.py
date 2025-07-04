from pydantic import BaseModel, Field
from typing import Optional

class FetchOABRequest(BaseModel):
    name: str = Field(..., description="Nome do advogado")
    uf: str = Field(..., description="UF (2 letras)", min_length=2, max_length=2)

class FetchOABResponse(BaseModel):
    """Resposta da busca na OAB"""
    oab: Optional[str] = Field(None, description="Número OAB")
    nome: Optional[str] = Field(None, description="Nome completo")
    uf: Optional[str] = Field(None, description="UF")
    categoria: Optional[str] = Field(None, description="Categoria")
    data_inscricao: Optional[str] = Field(None, description="Data de inscrição")
    situacao: Optional[str] = Field(None, description="Situação")

# Modelos pro agente
class AgentQueryRequest(BaseModel):
    query: str = Field(..., description="Pergunta")

class AgentQueryResponse(BaseModel):
    response: str = Field(..., description="Resposta")
    success: bool = True
    error: Optional[str] = None
