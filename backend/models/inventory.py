# backend/models/inventory.py
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from models.base import BaseModel

class UnitOfMeasure(enum.Enum):
    PIECE = "piece"
    KILOGRAM = "kg"
    LITER = "liter"
    METER = "meter"
    PACK = "pack"

class Category(BaseModel):
    """Model for inventory item categories"""
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    
    # Relationship with InventoryItem
    items = relationship("InventoryItem", back_populates="category")

class InventoryItem(BaseModel):
    """Model for inventory items"""
    item_code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    uom = Column(Enum(UnitOfMeasure), default=UnitOfMeasure.PIECE)
    unit_cost = Column(Float, default=0.0)
    quantity_on_hand = Column(Float, default=0.0)
    reorder_point = Column(Float, default=0.0)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    
    # Relationship with Category
    category = relationship("Category", back_populates="items")
