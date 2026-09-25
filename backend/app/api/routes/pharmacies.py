from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_pharmacy_repo
from app.repositories.pharmacy_repository import PharmacyRepository
from app.schemas.pharmacy import PharmacySchema

router = APIRouter(prefix="/api/pharmacies", tags=["pharmacies"])


@router.get("", response_model=list[PharmacySchema])
@router.get("/", response_model=list[PharmacySchema], include_in_schema=False)
async def list_pharmacies(
    repo: Annotated[PharmacyRepository, Depends(get_pharmacy_repo)],
) -> list[PharmacySchema]:
    pharmacies = await repo.get_all()
    return [PharmacySchema.model_validate(p) for p in pharmacies]
