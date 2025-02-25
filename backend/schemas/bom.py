# backend/schemas/bom.py
from pydantic import BaseModel, validator
from typing import Optional, List, Union
from datetime import datetime

class BOMComponentBase(BaseModel):
    component_id: int
    quantity: float
    uom: str
    position: Optional[int] = None
    notes: Optional[str] = None
    is_critical: Optional[bool] = False

class BOMComponentCreate(BOMComponentBase):
    pass

class BOMComponentUpdate(BaseModel):
    component_id: Optional[int] = None
    quantity: Optional[float] = None
    uom: Optional[str] = None
    position: Optional[int] = None
    notes: Optional[str] = None
    is_critical: Optional[bool] = None

class BOMBase(BaseModel):
    name: str
    description: Optional[str] = None
    product_id: int
    version: Optional[str] = "1.0"
    is_active: Optional[bool] = True
    notes: Optional[str] = None

class BOMCreate(BOMBase):
    components: List[BOMComponentCreate]

class BOMUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_id: Optional[int] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    components: Optional[List[Union[BOMComponentCreate, BOMComponentUpdate]]] = None

class BOMComponent(BOMComponentBase):
    id: int
    bom_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class BOM(BOMBase):
    id: int
    components: List[BOMComponent]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
