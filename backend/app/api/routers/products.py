# app/api/routers/products.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.logging import logger
from app.models import Product
from app.schemas import ProductBase, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=List[ProductOut])
def list_products(limit: int = Query(1000, ge=1, le=500), db: Session = Depends(get_db)) -> List[Product]:
    logger.info("Fetching products with limit=%s", limit)
    return db.query(Product).limit(limit).all()


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def add_product(product: ProductBase, db: Session = Depends(get_db)) -> Product:
    db_product = Product(
        name=product.name.strip(),
        category=product.category or None,
        brand=product.brand or None,
        screen=product.screen or None,
        processor=product.processor or None,
        ram=product.ram or None,
        storage=product.storage or None,
        camera=product.camera or None,
        price=product.price,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, product: ProductBase, db: Session = Depends(get_db)) -> Product:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    db_product.name = product.name.strip()
    db_product.category = product.category or None
    db_product.brand = product.brand or None
    db_product.screen = product.screen or None
    db_product.processor = product.processor or None
    db_product.ram = product.ram or None
    db_product.storage = product.storage or None
    db_product.camera = product.camera or None
    db_product.price = product.price

    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": f"Product ID {product_id} deleted successfully"}