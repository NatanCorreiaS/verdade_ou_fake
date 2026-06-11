from pydantic import BaseModel, ConfigDict, Field

from Model.claim import Claim


class SearchResponse(BaseModel):
    """Response model for the fact-checking search endpoint."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    claims: list[Claim] = Field(default_factory=list)
    next_page_token: str = Field(alias="nextPageToken", default="")
    fallback: bool = Field(
        default=False,
        description="Indica se o resultado provem do modelo local (True) ou da API externa (False).",
    )
