# backend/routers/mrp.py
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from database import get_db
from models.production import MRPRun as MRPRunModel, MRPItem as MRPItemModel, MPS as MPSModel
from models.inventory import InventoryItem
from models.bom import BOM, BOMComponent
from schemas.production import MRPRun, MRPRunCreate, MRPRunResult, MRPRunResultItem

router = APIRouter()

@router.get("/", response_model=List[MRPRun])
def read_mrp_runs(
    skip: int = 0, 
    limit: int = 100, 
    mps_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all MRP runs with optional filters"""
    query = db.query(MRPRunModel)
    
    if mps_id:
        query = query.filter(MRPRunModel.mps_id == mps_id)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{run_id}", response_model=MRPRun)
def read_mrp_run(run_id: int, db: Session = Depends(get_db)):
    """Get a specific MRP run by ID"""
    db_run = db.query(MRPRunModel).options(joinedload(MRPRunModel.mrp_items)).filter(
        MRPRunModel.id == run_id
    ).first()
    
    if db_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MRP run with ID {run_id} not found"
        )
    
    return db_run

@router.get("/{run_id}/results", response_model=MRPRunResult)
def read_mrp_results(run_id: int, db: Session = Depends(get_db)):
    """Get detailed results for an MRP run"""
    db_run = db.query(MRPRunModel).filter(MRPRunModel.id == run_id).first()
    
    if db_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MRP run with ID {run_id} not found"
        )
    
    # Get MRP items and join with inventory items to get names
    mrp_items = db.query(
        MRPItemModel, InventoryItem.item_code, InventoryItem.name
    ).join(
        InventoryItem, MRPItemModel.item_id == InventoryItem.id
    ).filter(
        MRPItemModel.mrp_run_id == run_id
    ).all()
    
    # Build the item hierarchy
    items_data = []
    items_by_parent = {}
    
    # Group items by parent for hierarchy building
    for item_data in mrp_items:
        mrp_item, item_code, item_name = item_data
        
        # Track items by their parent
        parent_id = mrp_item.parent_id
        if parent_id not in items_by_parent:
            items_by_parent[parent_id] = []
        
        items_by_parent[parent_id].append(mrp_item.id)
        
        # Add to results
        items_data.append(
            MRPRunResultItem(
                id=mrp_item.id,
                item_id=mrp_item.item_id,
                item_code=item_code,
                item_name=item_name,
                required_date=mrp_item.required_date,
                gross_requirement=mrp_item.gross_requirement,
                projected_on_hand=mrp_item.projected_on_hand,
                net_requirement=mrp_item.net_requirement,
                planned_order_release=mrp_item.planned_order_release,
                planned_order_receipt=mrp_item.planned_order_receipt,
                order_release_date=mrp_item.order_release_date,
                is_critical=mrp_item.is_critical,
                parent_id=mrp_item.parent_id,
                level=0,  # Will be set based on hierarchy
                has_children=mrp_item.id in items_by_parent
            )
        )
    
    # Set hierarchy levels
    mrp_result = MRPRunResult(
        id=db_run.id,
        name=db_run.name,
        run_date=db_run.run_date,
        mps_id=db_run.mps_id,
        lead_time_factor=db_run.lead_time_factor,
        include_safety_stock=db_run.include_safety_stock,
        items=items_data
    )
    
    return mrp_result

@router.post("/", response_model=MRPRun, status_code=status.HTTP_201_CREATED)
def create_mrp_run(mrp_run: MRPRunCreate, db: Session = Depends(get_db)):
    """Create a new MRP run and generate material requirements"""
    # Check if MPS exists
    mps = db.query(MPSModel).options(joinedload(MPSModel.schedule_items)).filter(
        MPSModel.id == mrp_run.mps_id
    ).first()
    
    if not mps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MPS with ID {mrp_run.mps_id} not found"
        )
    
    # Create MRP run
    db_mrp_run = MRPRunModel(
        name=mrp_run.name,
        description=mrp_run.description,
        mps_id=mrp_run.mps_id,
        run_date=datetime.utcnow(),
        lead_time_factor=mrp_run.lead_time_factor,
        include_safety_stock=mrp_run.include_safety_stock
    )
    
    db.add(db_mrp_run)
    db.flush()  # Get the ID without committing
    
    # Now run the MRP calculation algorithm
    
    # Step 1: Get all finished products from MPS
    mps_items = mps.schedule_items
    
    # Step 2: For each product, explode the BOM and calculate requirements
    for mps_item in mps_items:
        # Find the product's BOM
        bom = db.query(BOM).filter(
            BOM.product_id == mps_item.product_id,
            BOM.is_active == True
        ).first()
        
        if not bom:
            # Skip products without BOMs
            continue
        
        # Get current inventory level for gross requirements calculation
        product = db.query(InventoryItem).filter(InventoryItem.id == mps_item.product_id).first()
        
        # Create MRP item for the finished product (level 0)
        product_mrp_item = MRPItemModel(
            mrp_run_id=db_mrp_run.id,
            mps_item_id=mps_item.id,
            item_id=mps_item.product_id,
            bom_id=bom.id,
            required_date=mps_item.planned_date,
            gross_requirement=mps_item.quantity,
            projected_on_hand=product.quantity_on_hand if product else 0,
            net_requirement=max(0, mps_item.quantity - (product.quantity_on_hand if product else 0)),
            planned_order_release=max(0, mps_item.quantity - (product.quantity_on_hand if product else 0)),
            planned_order_receipt=max(0, mps_item.quantity - (product.quantity_on_hand if product else 0)),
            order_release_date=calculate_release_date(mps_item.planned_date, product, mrp_run.lead_time_factor),
            is_critical=mps_item.quantity > (product.quantity_on_hand if product else 0),
            parent_id=None  # Top level
        )
        
        db.add(product_mrp_item)
        db.flush()  # Get the ID for parent reference
        
        # Recursively explode the BOM and add all components
        process_bom_components(
            db, 
            bom, 
            product_mrp_item, 
            db_mrp_run.id, 
            mps_item.planned_date, 
            product_mrp_item.planned_order_release,
            mrp_run.lead_time_factor,
            mrp_run.include_safety_stock
        )
    
    db.commit()
    db.refresh(db_mrp_run)
    
    return db_mrp_run

@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mrp_run(run_id: int, db: Session = Depends(get_db)):
    """Delete an MRP run"""
    db_run = db.query(MRPRunModel).filter(MRPRunModel.id == run_id).first()
    
    if db_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MRP run with ID {run_id} not found"
        )
    
    db.delete(db_run)
    db.commit()
    
    return None

# Helper functions for MRP calculations
def calculate_release_date(required_date, item, lead_time_factor):
    """Calculate when an order needs to be released based on lead time"""
    # Default lead time is 1 day if not specified
    lead_time_days = 1
    
    # If item has a lead time, use it
    if hasattr(item, 'lead_time') and item.lead_time:
        lead_time_days = item.lead_time
    
    # Apply the lead time factor
    adjusted_lead_time = lead_time_days * lead_time_factor
    
    # Calculate release date
    return required_date - timedelta(days=adjusted_lead_time)

def process_bom_components(db, bom, parent_mrp_item, mrp_run_id, required_date, parent_quantity, lead_time_factor, include_safety_stock):
    """Recursively process BOM components and create MRP items"""
    # Get all components from the BOM
    components = db.query(BOMComponent).filter(BOMComponent.bom_id == bom.id).all()
    
    for component in components:
        # Get the component item
        item = db.query(InventoryItem).filter(InventoryItem.id == component.component_id).first()
        
        if not item:
            continue
        
        # Calculate requirements
        gross_req = parent_quantity * component.quantity
        safety_stock = item.reorder_point if include_safety_stock and item.reorder_point else 0
        projected_on_hand = item.quantity_on_hand
        net_req = max(0, gross_req + safety_stock - projected_on_hand)
        
        # Check if this component has its own BOM
        component_bom = db.query(BOM).filter(
            BOM.product_id == component.component_id,
            BOM.is_active == True
        ).first()
        
        # Create MRP item for this component
        component_mrp_item = MRPItemModel(
            mrp_run_id=mrp_run_id,
            mps_item_id=None,  # Components don't link directly to MPS
            item_id=component.component_id,
            bom_id=component_bom.id if component_bom else None,
            required_date=required_date,  # Same as parent for now, can be adjusted
            gross_requirement=gross_req,
            projected_on_hand=projected_on_hand,
            net_requirement=net_req,
            planned_order_release=net_req,
            planned_order_receipt=net_req,
            order_release_date=calculate_release_date(required_date, item, lead_time_factor),
            is_critical=net_req > 0 and (projected_on_hand < gross_req),
            parent_id=parent_mrp_item.id  # Link to parent
        )
        
        db.add(component_mrp_item)
        db.flush()  # Get the ID for potential child components
        
        # If this component has its own BOM, process it recursively
        if component_bom:
            process_bom_components(
                db, 
                component_bom, 
                component_mrp_item, 
                mrp_run_id, 
                required_date,  # For simplicity, use same date
                component_mrp_item.planned_order_release,
                lead_time_factor,
                include_safety_stock
            )
