from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud
from dependencies import get_current_user, require_admin
import models

router = APIRouter(prefix="/products", tags=["Products"])


# -----------------------------
# 1. Create Product (POST)
# -----------------------------
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.APIResponse[schemas.ProductResponse],
    summary="Create a new product"
)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new product in the inventory.
    - Requires authentication.
    - Product ID, Price, and Quantity must pass validation rules.
    - Returns HTTP 400 if product_id already exists.
    """
    existing = crud.get_product(db, product.product_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with ID {product.product_id} already exists."
        )

    new_product = crud.create_product(db, product, user_id=current_user.id)
    product_data = schemas.ProductResponse.model_validate(new_product)

    return schemas.APIResponse(
        status="success",
        message="Product created successfully",
        data=product_data
    )


# -----------------------------
# 2. Retrieve All Products (GET)
# -----------------------------
@router.get(
    "",
    response_model=schemas.APIResponse[List[schemas.ProductResponse]],
    summary="Retrieve all products"
)
def get_products(
    category: Optional[str] = Query(None, description="Filter products by category"),
    search: Optional[str] = Query(None, description="Search products by name"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all products with optional category filtering, keyword search, and pagination.
    - Publicly accessible endpoint.
    """
    products = crud.get_products(db, category=category, search=search, skip=skip, limit=limit)
    product_list = [schemas.ProductResponse.model_validate(p) for p in products]

    return schemas.APIResponse(
        status="success",
        message="Products retrieved successfully",
        data=product_list
    )


# -----------------------------
# 3. Retrieve Product by ID (GET)
# -----------------------------
@router.get(
    "/{product_id}",
    response_model=schemas.APIResponse[schemas.ProductResponse],
    summary="Retrieve product by ID"
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve details of a specific product by its ID.
    - Returns HTTP 404 if product is not found.
    """
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    product_data = schemas.ProductResponse.model_validate(product)

    return schemas.APIResponse(
        status="success",
        message="Product retrieved successfully",
        data=product_data
    )


# -----------------------------
# 4. Update Product (PUT)
# -----------------------------
@router.put(
    "/{product_id}",
    response_model=schemas.APIResponse[schemas.ProductResponse],
    summary="Update product details"
)
def update_product(
    product_id: int,
    updated_product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update an existing product's details.
    - Requires authentication.
    - Partial or full payload updates accepted.
    - Returns HTTP 404 if product not found.
    """
    product = crud.update_product(
        db,
        product_id=product_id,
        product_update=updated_product,
        user_id=current_user.id
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    product_data = schemas.ProductResponse.model_validate(product)

    return schemas.APIResponse(
        status="success",
        message="Product updated successfully",
        data=product_data
    )


# -----------------------------
# 5. Delete Product (DELETE)
# -----------------------------
@router.delete(
    "/{product_id}",
    response_model=schemas.APIResponse[None],
    summary="Delete product (Admin only)"
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """
    Delete a product from inventory.
    - **Restricted to Admin role only** (Returns 403 Forbidden for standard users).
    - Returns HTTP 404 if product not found.
    """
    product = crud.delete_product(db, product_id=product_id, user_id=admin_user.id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    return schemas.APIResponse(
        status="success",
        message="Product deleted successfully",
        data=None
    )
