from pydantic import BaseModel, ConfigDict


class Claim(BaseModel):
    """A single claim item returned by the fact-checking search API.

    The full schema of a claim was not provided, so this model is intentionally
    permissive and allows additional fields.
    """

    model_config = ConfigDict(extra="allow")
