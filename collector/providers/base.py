from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.common import ProductCandidate, ProductOffer


class PharmacyProvider(ABC):
    """Abstract base class for all pharmacy providers."""

    name: str = ""
    slug: str = ""

    @abstractmethod
    async def search(self, term: str) -> list["ProductCandidate"]:
        """Search for products matching the given term."""
        ...

    @abstractmethod
    async def get_prices(
        self,
        products: list["ProductCandidate"],
    ) -> list["ProductOffer"]:
        """Get current prices for a list of products already discovered."""
        ...
