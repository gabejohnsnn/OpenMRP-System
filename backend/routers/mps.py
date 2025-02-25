# backend/routers/mps.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.production import MPS as MPSModel, MPSItem as MPSItemModel
from models.inventory import InventoryItem
from schemas.production import MPS, MPSCreate, MPSUpdate, MPSItem

router = APIRouter()

@router.get("/", response_model=List[MPS])
def read_mps_list(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all Master Production Schedules with optional filters"""
    query = db.query(MPSModel)
    
    if active_only:
        query = query.filter(MPSModel.is_active == True)
    
    return query.options(joinedload(MPSModel.schedule_items)).offset(skip).limit(limit).all()

@router.post("/", response_model=MPS, status_code=status.HTTP_201_CREATED)
def create_mps(mps: MPSCreate, db: Session = Depends(get_db)):
    """Create a new Master Production Schedule with items"""
    # Create MPS without items first
    db_mps = MPSModel(
        name=mps.name,
        description=mps.description,
        planning_horizon=mps.planning_horizon,
        start_date=mps.start_date,
        end_date=mps.end_date,
        is_active=mps.is_active,
        is_locked=mps.is_locked
    )
    
    db.add(db_mps)
    db.flush()  # Get the ID without committing
    
    # Now add schedule items
    for item_data in mps.schedule_items:
        # Check if product exists
        product = db.query(InventoryItem).filter(InventoryItem.id == item_data.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_data.product_id} not found"
            )
        
        db_item = MPSItemModel(
            mps_id=db_mps.id,
            product_id=item_data.product_id,
            planned_date=item_data.planned_date,
            quantity=item_data.quantity,
            demand_source=item_data.demand_source,
            notes=item_data.notes,
            reference=item_data.reference
        )
        
        db.add(db_item)
    
    db.commit()
    db.refresh(db_mps)
    
    return db_mps

@router.get("/{mps_id}", response_model=MPS)
def read_mps(mps_id: int, db: Session = Depends(get_db)):
    """Get a specific Master Production Schedule by ID"""
    db_mps = db.query(MPSModel).options(joinedload(MPSModel.schedule_items)).filter(MPSModel.id == mps_id).first()
    
    if db_mps is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MPS with ID {mps_id} not found"
        )
    
    return db_mps

@router.put("/{mps_id}", response_model=MPS)
def update_mps(mps_id: int, mps: MPSUpdate, db: Session = Depends(get_db)):
    """Update a Master Production Schedule"""
    db_mps = db.query(MPSModel).filter(MPSModel.id == mps_id).first()
    
    if db_mps is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MPS with ID {mps_id} not found"
        )
    
    # Check if MPS is locked
    if db_mps.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a locked MPS"
        )
    
    # Update MPS attributes if provided
    update_data = mps.dict(exclude_unset=True, exclude={"schedule_items"})
    for key, value in update_data.items():
        setattr(db_mps, key, value)
    
    # Handle schedule items if provided
    if mps.schedule_items is not None:
        # First, map existing items by ID for easy lookup
        existing_items = {item.id: item for item in db_mps.schedule_items}
        
        # Track which items to keep
        items_to_keep = set()
        
        # Process new items
        for item_data in mps.schedule_items:
            if hasattr(item_data, 'id') and item_data.id:
                # This is an update to an existing item
                if item_data.id in existing_items:
                    item = existing_items[item_data.id]
                    items_to_keep.add(item_data.id)
                    
                    # Update fields
                    item_update = item_data.dict(exclude_unset=True)
                    for key, value in item_update.items():
                        if key != 'id':  # Don't update the ID
                            setattr(item, key, value)
            else:
                # This is a new item
                # Check if product exists
                product = db.query(InventoryItem).filter(InventoryItem.id == item_data.product_id).first()
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product with ID {item_data.product_id} not found"
                    )
                
                db_item = MPSItemModel(
                    mps_id=mps_id,
                    product_id=item_data.product_id,
                    planned_date=item_data.planned_date,
                    quantity=item_data.quantity,
                    demand_source=item_data.demand_source,
                    notes=item_data.notes,
                    reference=item_data.reference
                )
                
                db.add(db_item)
        
        # Delete items that weren't in the update
        for item_id, item in existing_items.items():
            if item_id not in items_to_keep:
                db.delete(item)
    
    db.commit()
    db.refresh(db_mps)
    
    return db_mps

@router.delete("/{mps_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mps(mps_id: int, db: Session = Depends(get_db)):
    """Delete a Master Production Schedule"""
    db_mps = db.query(MPSModel).filter(MPSModel.id == mps_id).first()
    
    if db_mps is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MPS with ID {mps_id} not found"
        )
    
    # Check if MPS is locked
    if db_mps.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a locked MPS"
        )
    
    db.delete(db_mps)
    db.commit()
    
    return None

@router.post("/{mps_id}/lock", response_model=MPS)
def lock_mps(mps_id: int, db: Session = Depends(get_db)):
    """Lock an MPS to prevent further changes"""
    db_mps = db.query(MPSModel).filter(MPSModel.id == mps_id).first()
    
    if db_mps is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MPS with ID {mps_id} not found"
        )
    
    db_mps.is_locked = True
    db.commit()
    db.refresh(db_mps)
    
    return db_mps

@router.post("/{mps_id}/unlock", response_model=MPS)
def unlock_mps(mps_id: int, db: Session = Depends(get_db)):
    """Unlock an MPS to allow changes"""
    db_mps = db.query(MPSModel).filter(MPSModel.id == mps_id).first()
    
    if db_mps is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MPS with ID {mps_id} not found"
        )
    
    db_mps.is_locked = False
    db.commit()
    db.refresh(db_mps)
    
    return db_mps
