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

### Installation and Setup

#### Using Docker (Recommended)

1. Clone the repository
   ```bash
   git clone https://github.com/gabejohnsnn/OpenMRP-System.git
   cd OpenMRP-System
   ```

2. Start the application using Docker Compose
   ```bash
   docker-compose up -d
   ```

3. Access the application
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

#### Manual Setup

1. Clone the repository
   ```bash
   git clone https://github.com/gabejohnsnn/OpenMRP-System.git
   cd OpenMRP-System
   ```

2. Set up the backend
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend
   ```bash
   cd frontend
   npm install
   ```

4. Start the PostgreSQL database
   ```bash
   # Using Docker
   docker run --name openmrp-db \
     -e POSTGRES_USER=openMRP \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=openMRP \
     -p 5432:5432 \
     -d postgres:14
   ```

5. Start the backend server
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

6. Start the frontend development server
   ```bash
   cd frontend
   npm start
   ```

7. Access the application
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Project Structure

```
OpenMRP-System/
├── backend/                  # FastAPI backend
│   ├── models/               # Database models
│   ├── routers/              # API routes
│   ├── schemas/              # Pydantic schemas
│   ├── main.py               # Main application entry point
│   └── database.py           # Database connection
├── frontend/                 # React frontend
│   ├── public/               # Static assets
│   └── src/                  # Source code
│       ├── components/       # React components
│       ├── services/         # API service modules
│       └── App.js            # Root component
└── docker-compose.yml        # Docker configuration
```

## Future Enhancements

1. **Capacity Planning**
   - Add work centers with capacity constraints
   - Schedule production based on available capacity
   - Visualize production load with Gantt charts

2. **Quality Management**
   - Add quality control checkpoints
   - Record inspection results
   - Track non-conformances

3. **Dashboard & Reporting**
   - Create KPI dashboards
   - Generate production reports
   - Add data visualization

4. **User Management & Security**
   - Add user authentication and authorization
   - Role-based access control
   - Activity logging

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the MIT License.
