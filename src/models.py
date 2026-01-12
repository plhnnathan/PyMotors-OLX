from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Anuncio(BaseModel):
    id: str = Field(alias="listId")
    titulo: str = Field(alias="subject")
    preco: float = Field(alias="price", default=0.0)
    ano: Optional[int] = Field(default=None)
    km: Optional[int] = Field(default=None)
    cambio: Optional[str] = Field(default="N/A")
    combustivel: Optional[str] = Field(default="N/A")
    cidade: str = Field(default="")
    estado: str = Field(default="")
    link: str = Field(alias="url", default="")
    imagem: Optional[str] = Field(default=None)
    data_publicacao: Optional[str] = Field(alias="listTime", default=None)
    
    tags: List[str] = Field(default_factory=list)
    score_preco: str = Field(default="Neutro")
    km_anual: int = Field(default=0)

    @field_validator('preco', mode='before')
    def limpar_preco(cls, v):
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            clean_value = v.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean_value) if clean_value else 0.0
        return 0.0

    class Config:
        populate_by_name = True
        extra = "ignore"