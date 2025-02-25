# backend/routers/inventory.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.inventory import InventoryItem as InventoryItemModel, Category as CategoryModel
from schemas.inventory import InventoryItem, InventoryItemCreate, InventoryItemUpdate, Category, CategoryCreate

router = APIRouter()

@router.get("/items/", response_model=List[InventoryItem])
def read_inventory_items(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all inventory items with optional search filter"""
    query = db.query(InventoryItemModel)
    if search:
        query = query.filter(
            InventoryItemModel.name.ilike(f"%{search}%") | 
            InventoryItemModel.item_code.ilike(f"%{search}%")
        )
    return query.offset(skip).limit(limit).all()

@router.post("/items/", response_model=InventoryItem)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    """Create a new inventory item"""
    db_item = db.query(InventoryItemModel).filter(InventoryItemModel.item_code == item.item_code).first()
    if db_item:
        raise HTTPException(status_code=400, detail="Item code already exists")
    db_item = InventoryItemModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/items/{item_id}", response_model=InventoryItem)
def read_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific inventory item by ID"""
    db_item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@router.put("/items/{item_id}", response_model=InventoryItem)
def update_inventory_item(item_id: int, item: InventoryItemUpdate, db: Session = Depends(get_db)):
    """Update an inventory item"""
    db_item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/items/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """Delete an inventory item"""
    db_item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"detail": "Item deleted successfully"}

# Category endpoints
@router.get("/categories/", response_model=List[Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all categories"""
    categories = db.query(CategoryModel).offset(skip).limit(limit).all()
    return categories

@router.post("/categories/", response_model=Category)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    db_category = db.query(CategoryModel).filter(CategoryModel.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    db_category = CategoryModel(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
