from datetime import datetime
from pydantic import BaseModel


class PharmacySchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    active: bool
    created_at: datetime
