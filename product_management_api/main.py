from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
import crud

from database import engine, get_db

# Create Database Tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="Product Management REST API",
    version="1.0.0",
    description="Internship Project - Product Management REST API"
)


# -----------------------------
# Home API
# -----------------------------
@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Welcome to Product Management REST API"
    }


# -----------------------------
# Create Product
# -----------------------------
@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate,
                   db: Session = Depends(get_db)):

    existing = crud.get_product(db, product.product_id)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Product ID already exists."
        )

    new_product = crud.create_product(db, product)

    return {
        "status": "success",
        "message": "Product created successfully",
        "data": new_product
    }


# -----------------------------
# Get All Products
# -----------------------------
@app.get("/products")
def get_products(db: Session = Depends(get_db)):

    products = crud.get_products(db)

    return {
        "status": "success",
        "count": len(products),
        "data": products
    }


# -----------------------------
# Get Product By ID
# -----------------------------
@app.get("/products/{product_id}")
def get_product(product_id: int,
                db: Session = Depends(get_db)):

    product = crud.get_product(db, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    return {
        "status": "success",
        "data": product
    }


# -----------------------------
# Update Product
# -----------------------------
@app.put("/products/{product_id}")
def update_product(product_id: int,
                   updated_product: schemas.ProductUpdate,
                   db: Session = Depends(get_db)):

    product = crud.update_product(
        db,
        product_id,
        updated_product
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    return {
        "status": "success",
        "message": "Product updated successfully",
        "data": product
    }


# -----------------------------
# Delete Product
# -----------------------------
@app.delete("/products/{product_id}")
def delete_product(product_id: int,
                   db: Session = Depends(get_db)):

    product = crud.delete_product(db, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    return {
        "status": "success",
        "message": "Product deleted successfully"
    }