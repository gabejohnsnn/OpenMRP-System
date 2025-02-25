# backend/schemas/inventory.py
from pydantic import BaseModel
from typing import Optional, List
from models.inventory import UnitOfMeasure

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    
    class Config:
        orm_mode = True

class InventoryItemBase(BaseModel):
    item_code: str
    name: str
    description: Optional[str] = None
    uom: UnitOfMeasure = UnitOfMeasure.PIECE
    unit_cost: float = 0.0
    quantity_on_hand: float = 0.0
    reorder_point: float = 0.0
    category_id: Optional[int] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    item_code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    uom: Optional[UnitOfMeasure] = None
    unit_cost: Optional[float] = None
    quantity_on_hand: Optional[float] = None
    reorder_point: Optional[float] = None
    category_id: Optional[int] = None

class InventoryItem(InventoryItemBase):
    id: int
    
    class Config:
        orm_mode = True
