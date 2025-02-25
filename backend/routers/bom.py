# backend/routers/bom.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.bom import BOM as BOMModel, BOMComponent as BOMComponentModel
from models.inventory import InventoryItem
from schemas.bom import BOM, BOMCreate, BOMUpdate, BOMComponent

router = APIRouter()

@router.get("/", response_model=List[BOM])
def read_boms(
    skip: int = 0, 
    limit: int = 100, 
    product_id: Optional[int] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all BOMs with optional filters"""
    query = db.query(BOMModel)
    
    if product_id:
        query = query.filter(BOMModel.product_id == product_id)
    
    if active_only:
        query = query.filter(BOMModel.is_active == True)
    
    return query.options(joinedload(BOMModel.components)).offset(skip).limit(limit).all()

@router.post("/", response_model=BOM, status_code=status.HTTP_201_CREATED)
def create_bom(bom: BOMCreate, db: Session = Depends(get_db)):
    """Create a new BOM with components"""
    # Check if product exists
    product = db.query(InventoryItem).filter(InventoryItem.id == bom.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {bom.product_id} not found"
        )
    
    # Check for existing BOM with same product and version
    existing_bom = db.query(BOMModel).filter(
        BOMModel.product_id == bom.product_id,
        BOMModel.version == bom.version
    ).first()
    
    if existing_bom:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"BOM for product {bom.product_id} with version {bom.version} already exists"
        )
    
    # Extract components from request
    components_data = bom.components
    
    # Create BOM without components first
    db_bom = BOMModel(
        name=bom.name,
        description=bom.description,
        product_id=bom.product_id,
        version=bom.version,
        is_active=bom.is_active,
        notes=bom.notes
    )
    
    db.add(db_bom)
    db.flush()  # Get the ID without committing
    
    # Now add components
    for i, component_data in enumerate(components_data):
        # Check if component exists
        component = db.query(InventoryItem).filter(InventoryItem.id == component_data.component_id).first()
        if not component:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component with ID {component_data.component_id} not found"
            )
        
        # Set position if not provided
        position = component_data.position if component_data.position is not None else i + 1
        
        db_component = BOMComponentModel(
            bom_id=db_bom.id,
            component_id=component_data.component_id,
            quantity=component_data.quantity,
            uom=component_data.uom,
            position=position,
            notes=component_data.notes,
            is_critical=component_data.is_critical
        )
        
        db.add(db_component)
    
    db.commit()
    db.refresh(db_bom)
    
    return db_bom

@router.get("/{bom_id}", response_model=BOM)
def read_bom(bom_id: int, db: Session = Depends(get_db)):
    """Get a specific BOM by ID"""
    db_bom = db.query(BOMModel).options(joinedload(BOMModel.components)).filter(BOMModel.id == bom_id).first()
    
    if db_bom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM with ID {bom_id} not found"
        )
    
    return db_bom

@router.put("/{bom_id}", response_model=BOM)
def update_bom(bom_id: int, bom: BOMUpdate, db: Session = Depends(get_db)):
    """Update a BOM and its components"""
    db_bom = db.query(BOMModel).filter(BOMModel.id == bom_id).first()
    
    if db_bom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM with ID {bom_id} not found"
        )
    
    # Update BOM attributes if provided
    update_data = bom.dict(exclude_unset=True, exclude={"components"})
    for key, value in update_data.items():
        setattr(db_bom, key, value)
    
    # Handle components if provided
    if bom.components is not None:
        # Get existing components
        existing_components = {comp.component_id: comp for comp in db_bom.components}
        
        # Process new components
        for i, component_data in enumerate(bom.components):
            component_dict = component_data.dict(exclude_unset=True)
            component_id = component_dict.get("component_id")
            
            # Check if this is an update to an existing component
            if component_id in existing_components:
                comp = existing_components[component_id]
                # Update existing component
                for key, value in component_dict.items():
                    if key != "component_id":  # Skip the ID
                        setattr(comp, key, value)
            else:
                # This is a new component
                position = component_dict.get("position", i + 1)
                
                # Check if component exists in inventory
                component = db.query(InventoryItem).filter(InventoryItem.id == component_id).first()
                if not component:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Component with ID {component_id} not found"
                    )
                
                # Create new component
                db_component = BOMComponentModel(
                    bom_id=bom_id,
                    component_id=component_id,
                    quantity=component_dict.get("quantity", 1.0),
                    uom=component_dict.get("uom", "pcs"),
                    position=position,
                    notes=component_dict.get("notes"),
                    is_critical=component_dict.get("is_critical", False)
                )
                
                db.add(db_component)
    
    db.commit()
    db.refresh(db_bom)
    
    return db_bom

@router.delete("/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bom(bom_id: int, db: Session = Depends(get_db)):
    """Delete a BOM and its components"""
    db_bom = db.query(BOMModel).filter(BOMModel.id == bom_id).first()
    
    if db_bom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM with ID {bom_id} not found"
        )
    
    db.delete(db_bom)
    db.commit()
    
    return None
