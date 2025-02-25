# backend/models/bom.py
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from models.base import BaseModel
from models.inventory import InventoryItem

class BOM(BaseModel):
    """Bill of Materials header model"""
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    product_id = Column(Integer, ForeignKey("inventoryitem.id"))
    version = Column(String, default="1.0")
    is_active = Column(Boolean, default=True)
    notes = Column(String, nullable=True)
    
    # Relationships
    product = relationship("InventoryItem", foreign_keys=[product_id])
    components = relationship("BOMComponent", back_populates="bom", cascade="all, delete-orphan")
    
    # Enforce unique product + version combination
    __table_args__ = (
        UniqueConstraint('product_id', 'version', name='uq_bom_product_version'),
    )

class BOMComponent(BaseModel):
    """Bill of Materials component model - represents items used in a BOM"""
    bom_id = Column(Integer, ForeignKey("bom.id"))
    component_id = Column(Integer, ForeignKey("inventoryitem.id"))
    quantity = Column(Float, default=1.0)
    uom = Column(String)  # Store UOM at time of creation to handle UOM changes
    position = Column(Integer)  # For ordering components
    notes = Column(String, nullable=True)
    is_critical = Column(Boolean, default=False)  # Flag for critical components
    
    # Relationships
    bom = relationship("BOM", back_populates="components")
    component = relationship("InventoryItem")
    
    # Make sure no duplicates in same BOM
    __table_args__ = (
        UniqueConstraint('bom_id', 'component_id', name='uq_bom_component'),
    )
