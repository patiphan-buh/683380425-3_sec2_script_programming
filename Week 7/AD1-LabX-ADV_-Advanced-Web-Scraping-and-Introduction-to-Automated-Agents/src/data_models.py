# agentic-web-scraper/src/data_models.py
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Product:
    """Data model for a scraped product (dataclass = clean, explicit representation)."""

    name: str
    price: str
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None

    def to_dict(self):
        """Converts the Product dataclass instance to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        """Creates a Product instance from a dictionary."""
        return cls(**data)
