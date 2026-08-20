from typing import List, Optional
from sqlalchemy.orm import Session
from models import Product, User, TransactionHistory
from schemas import ProductCreate, ProductUpdate, UserCreate
from auth import hash_password, verify_password


# -----------------------------
# Transaction Logging Helper & Query
# -----------------------------
def log_transaction(db: Session, action: str, product_id: int, user_id: Optional[int] = None):
    """Record product operation history into transaction_history table."""
    history_entry = TransactionHistory(
        action=action,
        product_id=product_id,
        user_id=user_id
    )
    db.add(history_entry)
    db.commit()


def get_transaction_history(
    db: Session,
    product_id: Optional[int] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TransactionHistory]:
    """Retrieve list of recorded transaction history logs."""
    query = db.query(TransactionHistory)
    if product_id is not None:
        query = query.filter(TransactionHistory.product_id == product_id)
    if action is not None:
        query = query.filter(TransactionHistory.action.ilike(action))
    return query.order_by(TransactionHistory.timestamp.desc()).offset(skip).limit(limit).all()


# -----------------------------
# User CRUD Operations
# -----------------------------
def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user with hashed password."""
    hashed_pwd = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        password=hashed_pwd,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieve user by username."""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Verify user credentials and return user object if valid."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


# -----------------------------
# Product CRUD Operations
# -----------------------------
def create_product(db: Session, product: ProductCreate, user_id: Optional[int] = None) -> Product:
    """Create a new product in the database and log transaction."""
    db_product = Product(
        product_id=product.product_id,
        product_name=product.product_name,
        description=product.description,
        price=product.price,
        quantity=product.quantity,
        category=product.category
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    log_transaction(db, action="CREATE", product_id=db_product.product_id, user_id=user_id)
    return db_product


def get_products(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Product]:
    """Retrieve list of products with optional category, search, and pagination filters."""
    query = db.query(Product)
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Retrieve product by product_id."""
    return db.query(Product).filter(Product.product_id == product_id).first()


def update_product(
    db: Session,
    product_id: int,
    product_update: ProductUpdate,
    user_id: Optional[int] = None
) -> Optional[Product]:
    """Update an existing product and log transaction."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)

    log_transaction(db, action="UPDATE", product_id=db_product.product_id, user_id=user_id)
    return db_product


def delete_product(db: Session, product_id: int, user_id: Optional[int] = None) -> Optional[Product]:
    """Delete product by product_id and log transaction."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    db.delete(db_product)
    db.commit()

    log_transaction(db, action="DELETE", product_id=product_id, user_id=user_id)
    return db_product