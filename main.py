"""FastAPI application entry point."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

from Controller.fact_check import router as fact_check_router


load_dotenv()

app = FastAPI(title="Verdade ou Fake")
app.include_router(fact_check_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_request, exc: RequestValidationError):
    """Return sanitized, pt-BR validation errors.

    This prevents leaking implementation details and keeps client-facing errors
    consistent with the API's `detail.mensagem` format.
    """

    errors = exc.errors()
    for err in errors:
        loc = err.get("loc") or ()
        err_type = err.get("type") or ""

        # Handle missing/empty `query` parameter.
        if "query" in loc and (
            err_type == "missing" or err_type.startswith("string_too_short")
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": {"mensagem": "O parâmetro 'query' é obrigatório."}},
            )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": {"mensagem": "Requisição inválida."}},
    )


def main() -> None:
    """Run the development server via Uvicorn."""

    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
    