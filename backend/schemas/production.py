# backend/schemas/production.py
from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from models.production import PlanningHorizon, DemandSource, ProductionOrderStatus

# ----- MPS Schemas -----

class MPSItemBase(BaseModel):
    product_id: int
    planned_date: datetime
    quantity: float
    demand_source: DemandSource = DemandSource.FORECAST
    notes: Optional[str] = None
    reference: Optional[str] = None

class MPSItemCreate(MPSItemBase):
    pass

class MPSItemUpdate(BaseModel):
    product_id: Optional[int] = None
    planned_date: Optional[datetime] = None
    quantity: Optional[float] = None
    demand_source: Optional[DemandSource] = None
    notes: Optional[str] = None
    reference: Optional[str] = None

class MPSItem(MPSItemBase):
    id: int
    mps_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class MPSBase(BaseModel):
    name: str
    description: Optional[str] = None
    planning_horizon: PlanningHorizon = PlanningHorizon.WEEKLY
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    is_locked: bool = False

class MPSCreate(MPSBase):
    schedule_items: List[MPSItemCreate]

class MPSUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    planning_horizon: Optional[PlanningHorizon] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None
    schedule_items: Optional[List[Union[MPSItemCreate, MPSItemUpdate]]] = None

class MPS(MPSBase):
    id: int
    created_at: datetime
    updated_at: datetime
    schedule_items: List[MPSItem]
    
    class Config:
        orm_mode = True

# ----- MRP Schemas -----

class MRPItemBase(BaseModel):
    item_id: int
    required_date: datetime
    gross_requirement: float
    projected_on_hand: float
    net_requirement: float
    planned_order_release: float = 0.0
    planned_order_receipt: float = 0.0
    order_release_date: Optional[datetime] = None
    is_critical: bool = False
    parent_id: Optional[int] = None
    mps_item_id: Optional[int] = None
    bom_id: Optional[int] = None

class MRPItem(MRPItemBase):
    id: int
    mrp_run_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class MRPRunBase(BaseModel):
    name: str
    description: Optional[str] = None
    mps_id: int
    lead_time_factor: float = 1.0
    include_safety_stock: bool = True

class MRPRunCreate(MRPRunBase):
    pass

class MRPRun(MRPRunBase):
    id: int
    run_date: datetime
    created_at: datetime
    updated_at: datetime
    mrp_items: List[MRPItem] = []
    
    class Config:
        orm_mode = True

# ----- Production Order Schemas -----

class MaterialAllocationBase(BaseModel):
    component_id: int
    required_quantity: float
    allocated_quantity: float = 0.0
    consumed_quantity: float = 0.0
    uom: str

class MaterialAllocationCreate(MaterialAllocationBase):
    pass

class MaterialAllocation(MaterialAllocationBase):
    id: int
    production_order_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ProductionOperationBase(BaseModel):
    sequence: int
    operation_name: str
    work_center: Optional[str] = None
    planned_start_date: datetime
    planned_end_date: datetime
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    setup_time: float = 0.0
    run_time: float = 0.0
    status: str = "pending"
    notes: Optional[str] = None

class ProductionOperationCreate(ProductionOperationBase):
    pass

class ProductionOperation(ProductionOperationBase):
    id: int
    production_order_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ProductionOrderBase(BaseModel):
    order_number: str
    product_id: int
    bom_id: Optional[int] = None
    mrp_item_id: Optional[int] = None
    status: ProductionOrderStatus = ProductionOrderStatus.DRAFT
    planned_quantity: float
    completed_quantity: float = 0.0
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    notes: Optional[str] = None
    priority: int = 5

class ProductionOrderCreate(ProductionOrderBase):
    material_allocations: List[MaterialAllocationCreate]
    operations: List[ProductionOperationCreate]

class ProductionOrderUpdate(BaseModel):
    status: Optional[ProductionOrderStatus] = None
    planned_quantity: Optional[float] = None
    completed_quantity: Optional[float] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    notes: Optional[str] = None
    priority: Optional[int] = None

class ProductionOrder(ProductionOrderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    material_allocations: List[MaterialAllocation] = []
    operations: List[ProductionOperation] = []
    
    class Config:
        orm_mode = True

# ----- MRP Run Results Schema -----
class MRPRunResultItem(BaseModel):
    id: int
    item_id: int
    item_code: str
    item_name: str
    required_date: datetime
    gross_requirement: float
    projected_on_hand: float
    net_requirement: float
    planned_order_release: float
    planned_order_receipt: float
    order_release_date: Optional[datetime]
    is_critical: bool
    parent_id: Optional[int]
    level: int = 0
    has_children: bool = False
    
    class Config:
        orm_mode = False

class MRPRunResult(BaseModel):
    id: int
    name: str
    run_date: datetime
    mps_id: int
    lead_time_factor: float
    include_safety_stock: bool
    items: List[MRPRunResultItem]
