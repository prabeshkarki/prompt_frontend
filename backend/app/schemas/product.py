# app/schemas/product.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    screen: Optional[str] = Field(None, max_length=100)
    processor: Optional[str] = Field(None, max_length=100)
    ram: Optional[str] = Field(None, max_length=50)
    storage: Optional[str] = Field(None, max_length=100)
    camera: Optional[str] = Field(None, max_length=100)
    price: float = Field(..., gt=0)


class ProductOut(ProductBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = {
    "from_attributes": True
    }
