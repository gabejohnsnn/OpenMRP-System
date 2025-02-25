# backend/routers/production_orders.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from datetime import datetime, timedelta
from models.production import ProductionOrder as ProductionOrderModel
from models.production import MaterialAllocation, ProductionOperation
from models.production import MRPItem, ProductionOrderStatus
from models.inventory import InventoryItem
from models.bom import BOM, BOMComponent
from schemas.production import ProductionOrder, ProductionOrderCreate, ProductionOrderUpdate

router = APIRouter()

@router.get("/", response_model=List[ProductionOrder])
def read_production_orders(
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    product_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all production orders with optional filters"""
    query = db.query(ProductionOrderModel)
    
    if status:
        query = query.filter(ProductionOrderModel.status == status)
    
    if product_id:
        query = query.filter(ProductionOrderModel.product_id == product_id)
    
    if from_date:
        query = query.filter(ProductionOrderModel.scheduled_start_date >= from_date)
    
    if to_date:
        query = query.filter(ProductionOrderModel.scheduled_start_date <= to_date)
    
    orders = query.options(
        joinedload(ProductionOrderModel.material_allocations),
        joinedload(ProductionOrderModel.operations)
    ).offset(skip).limit(limit).all()
    
    return orders

@router.post("/", response_model=ProductionOrder, status_code=status.HTTP_201_CREATED)
def create_production_order(order: ProductionOrderCreate, db: Session = Depends(get_db)):
    """Create a new production order"""
    # Check if product exists
    product = db.query(InventoryItem).filter(InventoryItem.id == order.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {order.product_id} not found"
        )
    
    # If BOM is provided, validate it
    if order.bom_id:
        bom = db.query(BOM).filter(BOM.id == order.bom_id).first()
        if not bom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"BOM with ID {order.bom_id} not found"
            )
        
        # Check if BOM is for the specified product
        if bom.product_id != order.product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BOM does not match the specified product"
            )
    
    # If MRP item is provided, validate it
    if order.mrp_item_id:
        mrp_item = db.query(MRPItem).filter(MRPItem.id == order.mrp_item_id).first()
        if not mrp_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MRP item with ID {order.mrp_item_id} not found"
            )
    
    # Create production order
    db_order = ProductionOrderModel(
        order_number=order.order_number,
        product_id=order.product_id,
        bom_id=order.bom_id,
        mrp_item_id=order.mrp_item_id,
        status=order.status,
        planned_quantity=order.planned_quantity,
        completed_quantity=order.completed_quantity,
        scheduled_start_date=order.scheduled_start_date,
        scheduled_end_date=order.scheduled_end_date,
        actual_start_date=order.actual_start_date,
        actual_end_date=order.actual_end_date,
        notes=order.notes,
        priority=order.priority
    )
    
    db.add(db_order)
    db.flush()  # Get the ID without committing
    
    # Add material allocations
    for allocation_data in order.material_allocations:
        # Check if component exists
        component = db.query(InventoryItem).filter(InventoryItem.id == allocation_data.component_id).first()
        if not component:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component with ID {allocation_data.component_id} not found"
            )
        
        db_allocation = MaterialAllocation(
            production_order_id=db_order.id,
            component_id=allocation_data.component_id,
            required_quantity=allocation_data.required_quantity,
            allocated_quantity=allocation_data.allocated_quantity,
            consumed_quantity=allocation_data.consumed_quantity,
            uom=allocation_data.uom
        )
        
        db.add(db_allocation)
    
    # Add operations
    for operation_data in order.operations:
        db_operation = ProductionOperation(
            production_order_id=db_order.id,
            sequence=operation_data.sequence,
            operation_name=operation_data.operation_name,
            work_center=operation_data.work_center,
            planned_start_date=operation_data.planned_start_date,
            planned_end_date=operation_data.planned_end_date,
            actual_start_date=operation_data.actual_start_date,
            actual_end_date=operation_data.actual_end_date,
            setup_time=operation_data.setup_time,
            run_time=operation_data.run_time,
            status=operation_data.status,
            notes=operation_data.notes
        )
        
        db.add(db_operation)
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.get("/{order_id}", response_model=ProductionOrder)
def read_production_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific production order by ID"""
    order = db.query(ProductionOrderModel).options(
        joinedload(ProductionOrderModel.material_allocations),
        joinedload(ProductionOrderModel.operations)
    ).filter(
        ProductionOrderModel.id == order_id
    ).first()
    
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    return order

@router.put("/{order_id}", response_model=ProductionOrder)
def update_production_order(order_id: int, order: ProductionOrderUpdate, db: Session = Depends(get_db)):
    """Update a production order"""
    db_order = db.query(ProductionOrderModel).filter(ProductionOrderModel.id == order_id).first()
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    # Check if we're trying to update a completed or cancelled order
    if db_order.status in [ProductionOrderStatus.COMPLETED, ProductionOrderStatus.CANCELLED]:
        if order.status not in [ProductionOrderStatus.COMPLETED, ProductionOrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify a {db_order.status.value} production order"
            )
    
    # Update fields
    update_data = order.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_order(order_id: int, db: Session = Depends(get_db)):
    """Delete a production order"""
    db_order = db.query(ProductionOrderModel).filter(ProductionOrderModel.id == order_id).first()
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    # Only allow deleting draft orders
    if db_order.status != ProductionOrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft production orders can be deleted"
        )
    
    db.delete(db_order)
    db.commit()
    
    return None

@router.post("/{order_id}/release", response_model=ProductionOrder)
def release_production_order(order_id: int, db: Session = Depends(get_db)):
    """Release a production order to the shop floor"""
    db_order = db.query(ProductionOrderModel).filter(ProductionOrderModel.id == order_id).first()
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    # Only draft or planned orders can be released
    if db_order.status not in [ProductionOrderStatus.DRAFT, ProductionOrderStatus.PLANNED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot release a {db_order.status.value} production order"
        )
    
    # Update status to RELEASED
    db_order.status = ProductionOrderStatus.RELEASED
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.post("/{order_id}/start", response_model=ProductionOrder)
def start_production_order(order_id: int, db: Session = Depends(get_db)):
    """Start a production order"""
    db_order = db.query(ProductionOrderModel).filter(ProductionOrderModel.id == order_id).first()
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    # Only released orders can be started
    if db_order.status != ProductionOrderStatus.RELEASED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start a {db_order.status.value} production order"
        )
    
    # Update status and start date
    db_order.status = ProductionOrderStatus.IN_PROGRESS
    db_order.actual_start_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.post("/{order_id}/complete", response_model=ProductionOrder)
def complete_production_order(
    order_id: int, 
    completed_quantity: float = Query(..., description="The quantity that was completed"),
    db: Session = Depends(get_db)
):
    """Complete a production order"""
    db_order = db.query(ProductionOrderModel).filter(ProductionOrderModel.id == order_id).first()
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    # Only in-progress orders can be completed
    if db_order.status != ProductionOrderStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete a {db_order.status.value} production order"
        )
    
    # Validate completed quantity
    if completed_quantity <= 0 or completed_quantity > db_order.planned_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Completed quantity must be between 0 and {db_order.planned_quantity}"
        )
    
    # Update status, end date, and completed quantity
    db_order.status = ProductionOrderStatus.COMPLETED
    db_order.actual_end_date = datetime.utcnow()
    db_order.completed_quantity = completed_quantity
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.post("/{order_id}/cancel", response_model=ProductionOrder)
def cancel_production_order(order_id: int, db: Session = Depends(get_db)):
    """Cancel a production order"""
    db_order = db.query(ProductionOrderModel).filter(ProductionOrderModel.id == order_id).first()
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    # Only orders that are not completed can be cancelled
    if db_order.status == ProductionOrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed production order"
        )
    
    # Update status
    db_order.status = ProductionOrderStatus.CANCELLED
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.post("/{order_id}/generate-from-bom", response_model=ProductionOrder)
def generate_from_bom(
    order_id: int, 
    bom_id: int = Query(..., description="BOM ID to use for generating materials and operations"),
    db: Session = Depends(get_db)
):
    """Generate material allocations and operations from a BOM"""
    db_order = db.query(ProductionOrderModel).filter(ProductionOrderModel.id == order_id).first()
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production order with ID {order_id} not found"
        )
    
    # Only draft orders can be updated
    if db_order.status != ProductionOrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update a {db_order.status.value} production order"
        )
    
    # Check if BOM exists
    bom = db.query(BOM).options(joinedload(BOM.components)).filter(BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM with ID {bom_id} not found"
        )
    
    # Check if BOM is for the specified product
    if bom.product_id != db_order.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BOM does not match the production order's product"
        )
    
    # Clear existing material allocations
    db.query(MaterialAllocation).filter(
        MaterialAllocation.production_order_id == order_id
    ).delete()
    
    # Add material allocations based on BOM components
    for component in bom.components:
        # Get the component item for UOM
        item = db.query(InventoryItem).filter(InventoryItem.id == component.component_id).first()
        
        db_allocation = MaterialAllocation(
            production_order_id=order_id,
            component_id=component.component_id,
            required_quantity=component.quantity * db_order.planned_quantity,
            allocated_quantity=0.0,
            consumed_quantity=0.0,
            uom=component.uom  # Use BOM component UOM
        )
        
        db.add(db_allocation)
    
    # Update BOM reference
    db_order.bom_id = bom_id
    
    db.commit()
    db.refresh(db_order)
    
    return db_order
