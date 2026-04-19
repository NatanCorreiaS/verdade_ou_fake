from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """Request model for the search endpoint.

    Per project requirements, this request includes only the query string.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=1,
        description="String de consulta textual obrigatória.",
    )
