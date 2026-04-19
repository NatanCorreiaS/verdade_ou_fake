"""Fact-checking endpoints backed by an external API."""

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from starlette import status

from Model.search_request import SearchRequest
from Model.search_response import SearchResponse


router = APIRouter(prefix="/fact-check", tags=["fact-check"])

FACT_CHECK_SEARCH_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def _get_api_key() -> str:
    """Return the API key used to authenticate external API requests."""

    api_key = os.getenv("API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "mensagem": "Configuração do servidor incompleta. Tente novamente mais tarde.",
            },
        )
    return api_key


def _raise_safe_upstream_error(*, status_code: int) -> None:
    """Raise a sanitized HTTPException for upstream failures.

    The returned error is intentionally generic to avoid leaking sensitive
    details about the upstream service or server configuration.
    """

    if status_code == status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"mensagem": "Parâmetros de consulta inválidos."},
        )

    if status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"mensagem": "Falha de autenticação com o serviço externo."},
        )

    if status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"mensagem": "Recurso não encontrado no serviço externo."},
        )

    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"mensagem": "Muitas requisições. Tente novamente mais tarde."},
        )

    if 500 <= status_code <= 599:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"mensagem": "O serviço externo está indisponível no momento."},
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"mensagem": "Não foi possível concluir a consulta ao serviço externo."},
    )


@router.get("/claims/search", response_model=SearchResponse)
async def search_claims(request: SearchRequest = Depends()) -> SearchResponse:
    """Search for fact-checked claims by a textual query."""

    params = {
        "query": request.query,
        "key": _get_api_key(),
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(FACT_CHECK_SEARCH_URL, params=params)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"mensagem": "Tempo limite ao consultar o serviço externo."},
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"mensagem": "Falha de conexão ao consultar o serviço externo."},
        )

    if response.is_error:
        _raise_safe_upstream_error(status_code=response.status_code)

    try:
        payload: Any = response.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"mensagem": "O serviço externo retornou uma resposta inválida."},
        )

    try:
        parsed = SearchResponse.model_validate(payload)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"mensagem": "O serviço externo retornou dados inesperados."},
        )

    if not parsed.claims:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "mensagem": "Nenhum resultado encontrado para a consulta informada.",
            },
        )

    return parsed
