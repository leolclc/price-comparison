from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, pharmacies, products, search_terms
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="FarmaCompare API",
    description="API de comparação de preços de farmácias",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(pharmacies.router)
app.include_router(products.router)
app.include_router(search_terms.router)


@app.get("/")
async def root() -> dict:
    return {"message": "FarmaCompare API", "docs": "/docs"}
