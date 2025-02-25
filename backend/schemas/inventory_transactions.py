# backend/schemas/inventory_transactions.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.inventory_transactions import TransactionType

class TransactionDetailBase(BaseModel):
    item_id: int
    quantity: float
    uom: str
    location_from: Optional[str] = None
    location_to: Optional[str] = None

class TransactionDetailCreate(TransactionDetailBase):
    pass

class TransactionDetail(TransactionDetailBase):
    id: int
    transaction_id: int
    
    class Config:
        orm_mode = True

class InventoryTransactionBase(BaseModel):
    reference_number: str
    transaction_type: TransactionType
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None

class InventoryTransactionCreate(InventoryTransactionBase):
    details: List[TransactionDetailCreate]

class InventoryTransactionUpdate(BaseModel):
    reference_number: Optional[str] = None
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None
    # Details not updatable after creation for data integrity

class InventoryTransaction(InventoryTransactionBase):
    id: int
    details: List[TransactionDetail]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
