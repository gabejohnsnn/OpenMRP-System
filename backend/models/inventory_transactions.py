# backend/models/inventory_transactions.py
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from models.base import BaseModel

class TransactionType(enum.Enum):
    PURCHASE_RECEIPT = "purchase_receipt"
    SALE_ISSUE = "sale_issue"
    PRODUCTION_ISSUE = "production_issue"
    PRODUCTION_RECEIPT = "production_receipt"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"

class InventoryTransaction(BaseModel):
    """Model for inventory transactions"""
    reference_number = Column(String, index=True)
    transaction_type = Column(Enum(TransactionType))
    transaction_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    
    # Relationships
    details = relationship("InventoryTransactionDetail", back_populates="transaction", cascade="all, delete-orphan")

class InventoryTransactionDetail(BaseModel):
    """Model for inventory transaction details (line items)"""
    transaction_id = Column(Integer, ForeignKey("inventorytransaction.id"))
    item_id = Column(Integer, ForeignKey("inventoryitem.id"))
    quantity = Column(Float)
    uom = Column(String)
    location_from = Column(String, nullable=True)  # For transfers
    location_to = Column(String, nullable=True)    # For transfers and receipts
    
    # Relationships
    transaction = relationship("InventoryTransaction", back_populates="details")
    item = relationship("models.inventory.InventoryItem")
