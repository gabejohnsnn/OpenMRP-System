# backend/models/production.py
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean, Enum, DateTime, Text, Table
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timedelta
from models.base import BaseModel

class PlanningHorizon(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class DemandSource(enum.Enum):
    FORECAST = "forecast"
    CUSTOMER_ORDER = "customer_order"
    SAFETY_STOCK = "safety_stock"
    MINIMUM_LEVEL = "minimum_level"

class ProductionOrderStatus(enum.Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MPS(BaseModel):
    """Master Production Schedule model"""
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    planning_horizon = Column(Enum(PlanningHorizon), default=PlanningHorizon.WEEKLY)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    
    # Relationships
    schedule_items = relationship("MPSItem", back_populates="mps", cascade="all, delete-orphan")

class MPSItem(BaseModel):
    """Master Production Schedule Item model"""
    mps_id = Column(Integer, ForeignKey("mps.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("inventoryitem.id"), nullable=False)
    planned_date = Column(DateTime, nullable=False)
    quantity = Column(Float, nullable=False)
    demand_source = Column(Enum(DemandSource), default=DemandSource.FORECAST)
    notes = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)  # For linking to customer orders or forecasts
    
    # Relationships
    mps = relationship("MPS", back_populates="schedule_items")
    product = relationship("models.inventory.InventoryItem")
    mrp_items = relationship("MRPItem", back_populates="mps_item")

class MRPRun(BaseModel):
    """Material Requirements Planning Run model"""
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    run_date = Column(DateTime, default=datetime.utcnow)
    mps_id = Column(Integer, ForeignKey("mps.id"), nullable=False)
    lead_time_factor = Column(Float, default=1.0)  # Factor to adjust standard lead times
    include_safety_stock = Column(Boolean, default=True)
    
    # Relationships
    mps = relationship("MPS")
    mrp_items = relationship("MRPItem", back_populates="mrp_run", cascade="all, delete-orphan")

class MRPItem(BaseModel):
    """Material Requirements Planning Item model"""
    mrp_run_id = Column(Integer, ForeignKey("mrprun.id"), nullable=False)
    mps_item_id = Column(Integer, ForeignKey("mpsitem.id"), nullable=True)
    item_id = Column(Integer, ForeignKey("inventoryitem.id"), nullable=False)
    bom_id = Column(Integer, ForeignKey("bom.id"), nullable=True)
    
    required_date = Column(DateTime, nullable=False)
    gross_requirement = Column(Float, nullable=False)
    projected_on_hand = Column(Float, nullable=False)
    net_requirement = Column(Float, nullable=False)
    planned_order_release = Column(Float, default=0.0)
    planned_order_receipt = Column(Float, default=0.0)
    order_release_date = Column(DateTime, nullable=True)
    is_critical = Column(Boolean, default=False)
    
    # Parent for multi-level BOM
    parent_id = Column(Integer, ForeignKey("mrpitem.id"), nullable=True)
    
    # Relationships
    mrp_run = relationship("MRPRun", back_populates="mrp_items")
    mps_item = relationship("MPSItem", back_populates="mrp_items")
    item = relationship("models.inventory.InventoryItem")
    bom = relationship("models.bom.BOM")
    parent = relationship("MRPItem", remote_side=[id], backref="components")
    
    # Production order relationship (reverse, one MRP item can generate multiple orders)
    production_orders = relationship("ProductionOrder", back_populates="mrp_item")

class ProductionOrder(BaseModel):
    """Production Order model"""
    order_number = Column(String(20), unique=True, nullable=False)
    mrp_item_id = Column(Integer, ForeignKey("mrpitem.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("inventoryitem.id"), nullable=False)
    bom_id = Column(Integer, ForeignKey("bom.id"), nullable=True)
    
    status = Column(Enum(ProductionOrderStatus), default=ProductionOrderStatus.DRAFT)
    planned_quantity = Column(Float, nullable=False)
    completed_quantity = Column(Float, default=0.0)
    
    scheduled_start_date = Column(DateTime, nullable=False)
    scheduled_end_date = Column(DateTime, nullable=False)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)
    priority = Column(Integer, default=5)  # 1-10 scale, 10 being highest
    
    # Relationships
    mrp_item = relationship("MRPItem", back_populates="production_orders")
    product = relationship("models.inventory.InventoryItem")
    bom = relationship("models.bom.BOM")
    
    # Material allocations
    material_allocations = relationship("MaterialAllocation", back_populates="production_order", cascade="all, delete-orphan")
    
    # Operations
    operations = relationship("ProductionOperation", back_populates="production_order", cascade="all, delete-orphan")

class MaterialAllocation(BaseModel):
    """Material Allocation for Production Orders"""
    production_order_id = Column(Integer, ForeignKey("productionorder.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("inventoryitem.id"), nullable=False)
    required_quantity = Column(Float, nullable=False)
    allocated_quantity = Column(Float, default=0.0)
    consumed_quantity = Column(Float, default=0.0)
    uom = Column(String(10), nullable=False)
    
    # Relationships
    production_order = relationship("ProductionOrder", back_populates="material_allocations")
    component = relationship("models.inventory.InventoryItem")

class ProductionOperation(BaseModel):
    """Production Operations for Production Orders"""
    production_order_id = Column(Integer, ForeignKey("productionorder.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    operation_name = Column(String(100), nullable=False)
    work_center = Column(String(100), nullable=True)
    
    planned_start_date = Column(DateTime, nullable=False)
    planned_end_date = Column(DateTime, nullable=False)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    setup_time = Column(Float, default=0.0)  # In minutes
    run_time = Column(Float, default=0.0)    # In minutes
    status = Column(String(20), default="pending")
    notes = Column(Text, nullable=True)
    
    # Relationships
    production_order = relationship("ProductionOrder", back_populates="operations")
