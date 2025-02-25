from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import inventory, bom, inventory_transactions, mps, mrp, production_orders
from database import engine, Base

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenMRP API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(bom.router, prefix="/api/bom", tags=["bom"])
app.include_router(inventory_transactions.router, prefix="/api/inventory-transactions", tags=["inventory-transactions"])
app.include_router(mps.router, prefix="/api/mps", tags=["production-planning"])
app.include_router(mrp.router, prefix="/api/mrp", tags=["production-planning"])
app.include_router(production_orders.router, prefix="/api/production-orders", tags=["production-planning"])

@app.get("/")
def read_root():
    return {"message": "Welcome to OpenMRP API", "version": "0.4.0"}
