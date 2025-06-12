# Spendlot Receipt Tracker Backend

A comprehensive backend system for a mobile receipt tracking app that extracts and tracks receipts and spending from multiple sources including image uploads, Gmail, bank transactions via Plaid, and SMS.

## Features

### Core Functionality
- **Receipt Image Processing**: Upload and OCR processing using Google Cloud Vision API
- **Multi-Source Data Ingestion**: Gmail, Plaid (bank transactions), SMS via Twilio
- **Automatic Categorization**: Smart categorization of transactions and receipts
- **Duplicate Detection**: Automatic detection and handling of duplicate entries
- **Real-time Analytics**: Spending summaries, category breakdowns, and trends

### Technology Stack
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching & Queues**: Redis for caching and Celery for background tasks
- **Authentication**: JWT-based authentication with refresh tokens
- **External APIs**: Google Cloud Vision, Gmail API, Plaid API, Twilio
- **Containerization**: Docker and Docker Compose

### Security Features
- JWT authentication with refresh tokens
- Data encryption at rest for sensitive information
- API rate limiting
- Input validation and sanitization
- Secure credential management

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (or use Docker)
- Redis (or use Docker)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd spendlot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec api python scripts/init_db.py
   ```

5. **Run database migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

### Manual Setup (without Docker)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL and Redis**
   - Install and configure PostgreSQL
   - Install and start Redis

3. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Start Celery worker**
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

7. **Start Celery beat (scheduler)**
   ```bash
   celery -A app.tasks.celery_app beat --loglevel=info
   ```

## API Documentation

Once the application is running, you can access:
- **Interactive API docs**: http://localhost:8000/api/v1/docs
- **ReDoc documentation**: http://localhost:8000/api/v1/redoc
- **Health check**: http://localhost:8000/health

## Configuration

### Environment Variables

Key environment variables to configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/spendlot

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Cloud Vision
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# Gmail API
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret

# Plaid API
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENVIRONMENT=sandbox

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
```

### External Service Setup

1. **Google Cloud Vision API**
   - Create a Google Cloud project
   - Enable the Vision API
   - Create a service account and download the JSON key
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to the key file path

2. **Gmail API**
   - Enable Gmail API in Google Cloud Console
   - Create OAuth 2.0 credentials
   - Set the client ID and secret in environment variables

3. **Plaid API**
   - Sign up for Plaid developer account
   - Get your client ID and secret keys
   - Configure for sandbox/development/production environment

4. **Twilio**
   - Create a Twilio account
   - Get your Account SID and Auth Token
   - Set up a phone number for SMS webhooks

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout

### Receipts
- `POST /api/v1/receipts/upload` - Upload receipt image
- `GET /api/v1/receipts/` - Get user receipts (paginated)
- `GET /api/v1/receipts/{id}` - Get specific receipt
- `PUT /api/v1/receipts/{id}` - Update receipt
- `DELETE /api/v1/receipts/{id}` - Delete receipt

### Transactions
- `GET /api/v1/transactions/` - Get user transactions (paginated)
- `POST /api/v1/transactions/` - Create manual transaction
- `GET /api/v1/transactions/{id}` - Get specific transaction
- `PUT /api/v1/transactions/{id}` - Update transaction

### Bank Accounts
- `GET /api/v1/bank-accounts/` - Get user bank accounts
- `POST /api/v1/bank-accounts/plaid/link-token` - Create Plaid link token
- `POST /api/v1/bank-accounts/plaid/exchange-token` - Exchange public token

### Analytics
- `GET /api/v1/analytics/spending-summary` - Get spending summary
- `GET /api/v1/analytics/category-stats` - Get category statistics
- `GET /api/v1/analytics/monthly-trends` - Get monthly spending trends

## Background Tasks

The system uses Celery for background processing:

- **OCR Processing**: Automatic receipt text extraction
- **Gmail Polling**: Periodic email receipt scanning
- **Plaid Sync**: Bank transaction synchronization
- **Categorization**: Automatic transaction categorization
- **Duplicate Detection**: Finding and marking duplicates

## Testing

Run the test suite:

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=app tests/
```

## Development

### Code Quality
- **Linting**: flake8
- **Type Checking**: mypy
- **Code Formatting**: black
- **Import Sorting**: isort

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

### Monitoring
- **Celery Monitoring**: Flower UI at http://localhost:5555
- **Health Checks**: Built-in health check endpoints
- **Logging**: Structured logging with configurable levels

## Production Deployment

### Security Checklist
- [ ] Change default passwords and secret keys
- [ ] Enable HTTPS/TLS
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable database connection pooling
- [ ] Configure log aggregation
- [ ] Set up monitoring and alerting

### Scaling Considerations
- Use multiple Celery workers for background processing
- Implement database read replicas for analytics queries
- Use Redis Cluster for high availability
- Consider CDN for file uploads
- Implement proper database indexing

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository.
