# backend/routers/inventory_transactions.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from database import get_db
from models.inventory_transactions import InventoryTransaction as TransactionModel
from models.inventory_transactions import InventoryTransactionDetail as TransactionDetailModel
from models.inventory import InventoryItem
from schemas.inventory_transactions import InventoryTransaction, InventoryTransactionCreate, InventoryTransactionUpdate

router = APIRouter()

@router.get("/", response_model=List[InventoryTransaction])
def read_transactions(
    skip: int = 0, 
    limit: int = 100, 
    transaction_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all inventory transactions with optional filters"""
    query = db.query(TransactionModel)
    
    if transaction_type:
        query = query.filter(TransactionModel.transaction_type == transaction_type)
    
    if from_date:
        query = query.filter(TransactionModel.transaction_date >= from_date)
    
    if to_date:
        query = query.filter(TransactionModel.transaction_date <= to_date)
    
    transactions = query.options(joinedload(TransactionModel.details)).offset(skip).limit(limit).all()
    return transactions

@router.post("/", response_model=InventoryTransaction, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: InventoryTransactionCreate, db: Session = Depends(get_db)):
    """Create a new inventory transaction with details"""
    # Validate all items exist
    for detail in transaction.details:
        item = db.query(InventoryItem).filter(InventoryItem.id == detail.item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {detail.item_id} not found"
            )
    
    # Create transaction
    db_transaction = TransactionModel(
        reference_number=transaction.reference_number,
        transaction_type=transaction.transaction_type,
        transaction_date=transaction.transaction_date or datetime.utcnow(),
        notes=transaction.notes
    )
    
    db.add(db_transaction)
    db.flush()  # Get ID without committing
    
    # Add details
    for detail in transaction.details:
        db_detail = TransactionDetailModel(
            transaction_id=db_transaction.id,
            item_id=detail.item_id,
            quantity=detail.quantity,
            uom=detail.uom,
            location_from=detail.location_from,
            location_to=detail.location_to
        )
        db.add(db_detail)
    
    # Update inventory quantities - this is a critical section!
    for detail in transaction.details:
        item = db.query(InventoryItem).filter(InventoryItem.id == detail.item_id).first()
        
        # Adjust inventory based on transaction type
        if transaction.transaction_type in [transaction.transaction_type.PURCHASE_RECEIPT, 
                                            transaction.transaction_type.PRODUCTION_RECEIPT]:
            # Increase inventory
            item.quantity_on_hand += detail.quantity
        elif transaction.transaction_type in [transaction.transaction_type.SALE_ISSUE, 
                                              transaction.transaction_type.PRODUCTION_ISSUE]:
            # Decrease inventory
            if item.quantity_on_hand < detail.quantity:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient quantity for item {item.name}. Available: {item.quantity_on_hand}, Requested: {detail.quantity}"
                )
            item.quantity_on_hand -= detail.quantity
        elif transaction.transaction_type == transaction.transaction_type.ADJUSTMENT:
            # Direct adjustment (can be positive or negative)
            item.quantity_on_hand += detail.quantity  # For adjustments, quantity can be negative
    
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction

@router.get("/{transaction_id}", response_model=InventoryTransaction)
def read_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a specific inventory transaction by ID"""
    transaction = db.query(TransactionModel).options(joinedload(TransactionModel.details)).filter(
        TransactionModel.id == transaction_id
    ).first()
    
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    return transaction

@router.put("/{transaction_id}", response_model=InventoryTransaction)
def update_transaction(transaction_id: int, transaction: InventoryTransactionUpdate, db: Session = Depends(get_db)):
    """Update an inventory transaction (metadata only, not details)"""
    db_transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    
    if db_transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Update fields if provided - note we only allow updating metadata, not the actual details
    update_data = transaction.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, reverse: bool = False, db: Session = Depends(get_db)):
    """
    Delete an inventory transaction
    If reverse=True, also reverses the quantity changes
    """
    db_transaction = db.query(TransactionModel).options(joinedload(TransactionModel.details)).filter(
        TransactionModel.id == transaction_id
    ).first()
    
    if db_transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    if reverse:
        # Reverse the inventory impact
        for detail in db_transaction.details:
            item = db.query(InventoryItem).filter(InventoryItem.id == detail.item_id).first()
            
            # Reverse adjustment based on transaction type
            if db_transaction.transaction_type in [db_transaction.transaction_type.PURCHASE_RECEIPT, 
                                                   db_transaction.transaction_type.PRODUCTION_RECEIPT]:
                # Decrease inventory
                if item.quantity_on_hand < detail.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot reverse transaction. Current quantity ({item.quantity_on_hand}) for item {item.name} is less than the transaction quantity ({detail.quantity})"
                    )
                item.quantity_on_hand -= detail.quantity
            elif db_transaction.transaction_type in [db_transaction.transaction_type.SALE_ISSUE, 
                                                     db_transaction.transaction_type.PRODUCTION_ISSUE]:
                # Increase inventory
                item.quantity_on_hand += detail.quantity
            elif db_transaction.transaction_type == db_transaction.transaction_type.ADJUSTMENT:
                # Reverse adjustment
                item.quantity_on_hand -= detail.quantity  # Opposite of the adjustment
    
    db.delete(db_transaction)
    db.commit()
    
    return None
