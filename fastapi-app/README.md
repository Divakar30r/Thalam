# dCent CP Order Management API

FastAPI application with MongoDB and Beanie ODM for managing UserBase, RolesBase, and TerminalBase collections.

## Features

- **UserBase Management**: User profiles with location tracking and contact information
- **RolesBase Management**: Role-based access control with hierarchical permissions
- **TerminalBase Management**: Terminal capacity and capability management
- **Geospatial Support**: MongoDB geospatial indexing for location-based queries
- **Data Validation**: Comprehensive input validation and referential integrity
- **Async Operations**: Full async/await support with Beanie ODM

## Requirements

- Python 3.8+
- MongoDB 4.4+
- FastAPI
- Beanie ODM
- Motor (async MongoDB driver)

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your MongoDB connection string
```

4. Start MongoDB (if running locally):
```bash
mongod
```

## Usage

1. Start the development server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### UserBase
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/` - List users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### RolesBase
- `POST /api/v1/roles/` - Create role
- `GET /api/v1/roles/` - List roles
- `GET /api/v1/roles/{role_id}` - Get role by ID
- `PUT /api/v1/roles/{role_id}` - Update role
- `DELETE /api/v1/roles/{role_id}` - Delete role

### TerminalBase
- `POST /api/v1/terminals/` - Create terminal
- `GET /api/v1/terminals/` - List terminals
- `GET /api/v1/terminals/{terminal_id}` - Get terminal by ID
- `PUT /api/v1/terminals/{terminal_id}` - Update terminal
- `DELETE /api/v1/terminals/{terminal_id}` - Delete terminal

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `CP_OrderManagement` |
| `DEBUG` | Enable debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Data Models

### UserBase
- ShortName: User's display name
- EmailID: Email with domain validation
- Location: GeoJSON Point for geographic location
- Contact: Array of contact numbers
- AADHAR: Optional AADHAR number
- Status: User status (Active/Inactive)

### RolesBase
- Type: Role type (Admin/Manager/Operator/TerminalOwner)
- RoleID: Formatted role identifier
- Location: GeoJSON Point for role location
- UserEmailID: Reference to UserBase email

### TerminalBase
- TerminalID: Unique terminal identifier
- Location: GeoJSON Point for terminal location
- Capacity: Storage capacity specifications
- Capabilities: Terminal feature flags
- RoleIDs: Array of managing role references

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest
```

3. Run linting:
```bash
flake8 app/
black app/
```

## Production Deployment

1. Set environment to production:
```bash
export ENVIRONMENT=production
```

2. Configure production settings in `.env`

3. Deploy with gunicorn:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## License

This project is licensed under the MIT License.