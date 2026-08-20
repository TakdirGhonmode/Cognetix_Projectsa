from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud
from dependencies import get_current_user
import models

router = APIRouter(prefix="/transactions", tags=["Transaction History"])


@router.get(
    "",
    response_model=schemas.APIResponse[List[schemas.TransactionHistoryResponse]],
    summary="Retrieve inventory transaction history"
)
def get_transaction_history(
    product_id: Optional[int] = Query(None, description="Filter transactions by product ID"),
    action: Optional[str] = Query(None, description="Filter by action: CREATE, UPDATE, or DELETE"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve audit transaction log of all product actions (CREATE, UPDATE, DELETE).
    - Requires authentication.
    """
    history_records = crud.get_transaction_history(
        db,
        product_id=product_id,
        action=action,
        skip=skip,
        limit=limit
    )
    
    response_data = [schemas.TransactionHistoryResponse.model_validate(r) for r in history_records]

    return schemas.APIResponse(
        status="success",
        message="Transaction history retrieved successfully",
        data=response_data
    )


@router.get(
    "/product/{product_id}",
    response_model=schemas.APIResponse[List[schemas.TransactionHistoryResponse]],
    summary="Retrieve audit history for a specific product"
)
def get_product_transaction_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve all audit transaction logs for a specific product ID.
    - Requires authentication.
    """
    history_records = crud.get_transaction_history(db, product_id=product_id)
    response_data = [schemas.TransactionHistoryResponse.model_validate(r) for r in history_records]

    return schemas.APIResponse(
        status="success",
        message=f"Transaction history for product ID {product_id} retrieved successfully",
        data=response_data
    )
