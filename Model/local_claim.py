from pydantic import BaseModel, ConfigDict, Field


class LocalClaim(BaseModel):
    """A claim verified by the local ML model (fallback)."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(description="Texto da afirmação analisada.")
    resultado: str = Field(description="Classificação: 'Verdadeiro' ou 'Falso'.")
    confianca_verdadeiro: float = Field(description="Probabilidade da classe Verdadeiro.")
    confianca_falso: float = Field(description="Probabilidade da classe Falso.")
    threshold: float = Field(description="Limiar de decisão utilizado.")
    fonte: str = Field(description="Origem da verificação — 'modelo_local'.")
