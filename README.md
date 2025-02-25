# OpenMRP System

An open-source Manufacturing Resource Planning (MRP) system for small and medium-sized production applications.

## Overview

OpenMRP is a comprehensive, web-based MRP system designed to help manufacturers plan and control their production processes. It provides essential functionality for inventory management, bill of materials (BOM), production planning, and shop floor control.

## Key Features

- **Inventory Management**
  - Track raw materials, WIP, and finished goods
  - Record inventory transactions (receipts, issues, transfers)
  - Set reorder points and monitor stock levels

- **Bill of Materials (BOM)**
  - Create multi-level product structures
  - Manage revisions and versions
  - Track component relationships

- **Production Planning**
  - Master Production Schedule (MPS)
  - Material Requirements Planning (MRP)
  - Generate planned orders based on material requirements

- **Production Orders**
  - Convert planned orders to production orders
  - Track progress through production lifecycle
  - Monitor material consumption

## Technology Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with Material UI
- **Database**: PostgreSQL
- **Containerization**: Docker

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- PostgreSQL database
- Docker (optional)

### Installation

1. Clone the repository
2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Start the development servers:
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm start
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests.
