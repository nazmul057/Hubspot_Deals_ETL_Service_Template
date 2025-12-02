# Hubspot_Deals Data Extraction Service

A robust Flask-RESTX API service for extracting Hubspot_Deals data using DLT (Data Load Tool) and PostgreSQL. Features comprehensive Swagger documentation, Docker support, and production-ready deployment.

## Features

- **Hubspot_Deals API Integration**: Extracts data via Hubspot_Deals REST API
- **DLT Integration**: Efficient data loading with PostgreSQL destination
- **Flask-RESTX**: RESTful API with automatic Swagger documentation
- **Async Processing**: Non-blocking scan operations with real-time status tracking
- **Multi-Environment Docker**: Separate configurations for dev/staging/prod
- **Comprehensive Monitoring**: Health checks, logging, and pipeline information
- **Data Validation**: Robust input validation using Marshmallow schemas
- **Production Ready**: Gunicorn WSGI server, proper error handling, CORS support

## Project Structure

```
hubspot-deals-etl
|   .dockerignore
|   .env.example
|   .gitignore
|   app.py
|   config.py
|   docker-compose.yml
|   Dockerfile.dev
|   Dockerfile.prod
|   Dockerfile.stage
|   Dockerfile.test
|   encrypter.py
|   loki_logger.py
|   readme.md
|   requirements.txt
|   utils.py
|   wsgi.py
|   
+---.dlt
+---api
|   |   routes.py
|   |   schemas.py
|   |   swagger_schemas.py
|   |   __init__.py
|
|           
+---docs
|       APi-DOCS.md
|       DATABASE-DESIGN-DOCS.md
|       INTEGRATION-DOCS.md
|       
+---logs
|       app.log
|       
+---models
|   |   database.py
|   |   models.py
|   |   __init__.py
|
|           
+---services
    |   api_service.py
    |   database_service.py
    |   data_source.py
    |   extraction_service.py
    |   hubspot_api_service.py
    |   job_service.py
    |   __init__.py

        
```

## Setup & Installation

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Hubspot_Deals API Access Token/Credentials

### Quick Start with Docker

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Glynac-AI/Backend-Tools-and-assessment
   cd hubspot-deals-extraction
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Hubspot_Deals API credentials
   ```

3. **Start services by environment**:

   **Development Environment (with tools):**
   ```bash
   # Start development services with pgAdmin and Redis Commander
   docker-compose --profile dev up -d --build
   
   # Start core development services only
   docker-compose up -d
   ```

   **Staging Environment:**
   ```bash
   # Start staging services
   docker-compose --profile stage up -d
   ```

   **Production Environment:**
   ```bash
   # Start production services
   docker-compose --profile prod up -d
   ```

4. **Verify the setup**:
   ```bash
   # Check service health
   curl http://localhost:5200/api/health
   
   # View Swagger documentation
   open http://localhost:5200/docs
   
   # Access development tools (dev profile only)
   open http://localhost:8080/  # pgAdmin
   open http://localhost:8081/  # Redis Commander
   ```

### Local Development Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   export FLASK_ENV=development
   export FLASK_DEBUG=true
   export DB_HOST=localhost
   export DB_PASSWORD=password123
   export HUBSPOT_DEALS_API_TOKEN="your-token-here"
   ```

3. **Start PostgreSQL** (using Docker):
   ```bash
   docker run -d --name hubspot_deals_postgres \
     -e POSTGRES_DB=hubspot_deals_data_dev \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=password123 \
     -p 5432:5432 postgres:15-alpine
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

## API Documentation

### Swagger UI
Access the interactive API documentation at: **http://localhost:5200/docs**

### Available Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| `GET` | `/api/health` | Health check endpoint | None |
| `GET` | `/api/stats` | Service statistics | None |
| `GET` | `/docs` | Swagger UI documentation | None |
| `POST` | `/api/scan/start` | Start a new data extraction scan | Body: scanId, organizationId, type, auth, filters |
| `GET` | `/api/scan/{scan_id}/status` | Get scan status | Path: scan_id |
| `POST` | `/api/scan/{scan_id}/cancel` | Cancel a running scan | Path: scan_id |
| `GET` | `/api/scan/list` | List all scans with pagination | Query: organizationId, limit, offset |
| `GET` | `/api/scan/statistics` | Get scan statistics | Query: organizationId |
| `DELETE` | `/api/scan/{scan_id}/remove` | Remove scan and data | Path: scan_id |
| `GET` | `/api/results/{scan_id}/tables` | Get available tables | Path: scan_id |
| `GET` | `/api/results/{scan_id}/result` | Get scan results | Path: scan_id; Query: tableName, limit, offset |
| `GET` | `/api/pipeline/info` | Get DLT pipeline info | None |
| `POST` | `/api/maintenance/cleanup` | Clean up old scans | Body: daysOld |
| `POST` | `/api/maintenance/detect-crashed` | Detect crashed jobs | Query: timeoutMinutes |

### Example API Usage

#### Start a Scan
```bash
curl -X POST "http://localhost:5200/api/scan/start" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "scanId": "scan-try-1",
      "organizationId": "12345",
      "type": ["user"],
      "auth": {
        "accessToken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      },
      "filters": {
        "dateRange": {
          "startDate": "2025-01-01",
          "endDate": "2025-12-31"
        }
      }
    }
  }'
```

#### Check Scan Status
```bash
curl http://localhost:5200/api/scan/hubspot-deals-scan-001/status
```

#### List All Scans
```bash
curl "http://localhost:5200/api/scan/list?organizationId=org-12345&limit=10"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Enable debug mode | `false` |
| `DB_HOST` | PostgreSQL host | `postgres_dev` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `hubspot_deals_data_dev` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `password123` |
| `DB_SCHEMA` | Database schema | `hubspot_deals_dev` |
| `HUBSPOT_ACCESS_TOKEN` | Hubspot_Deals API token | `""` |
| `HUBSPOT_API_TIMEOUT` | API timeout seconds | `30` |
| `HUBSPOT_API_RATE_LIMIT` | API rate limit | `100` |
| `API_BASE_URL` | API rate limit | `https://api.hubapi.com` |
| `DLT_PIPELINE_NAME` | DLT pipeline name | `hubspot_deals_pipeline_dev` |
| `MAX_CONCURRENT_SCANS` | Max concurrent scans | `3` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Multi-Environment Configuration

Each environment has its own configuration:

**Development:**
- Database: `hubspot_deals_data_dev`
- Port: `5200`
- Debug mode enabled
- Hot reloading
- Development tools available

**Staging:**
- Database: `hubspot_deals_data_stage`
- Port: `5201`
- Production-like settings
- Staging-specific logging

**Production:**
- Database: `hubspot_deals_data_prod`
- Port: `5202`
- Optimized performance
- Production logging
- Enhanced security

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Database Access
```bash
# Development database
docker-compose exec postgres_dev psql -U postgres -d hubspot_deals_data_dev

# View extracted data
SELECT * FROM hubspot_deals_dev.main_data LIMIT 10;
```

### Development Tools (Dev Profile)
- **pgAdmin**: http://localhost:8080 (admin@hubspot-deals.dev / admin123)
- **Redis Commander**: http://localhost:8081 (admin / admin123)

## Deployment

### Production Deployment
```bash
# Build and start production services
docker-compose --profile prod build
docker-compose --profile prod up -d

# Check production service
curl http://localhost:5202/health
```

### Scaling
```bash
# Scale production service
docker-compose --profile prod up -d --scale hubspot_deals_service_prod=3
```

### Monitoring
```bash
# View logs
docker-compose logs -f hubspot_deals_service_dev

# Monitor resource usage
docker stats
```

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker-compose logs hubspot_deals_service_dev

# Restart service
docker-compose restart hubspot_deals_service_dev
```

**Database connection issues:**
```bash
# Check database status
docker-compose exec postgres_dev pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

**Hubspot_Deals API issues:**
- Verify API token in `.env` file
- Check Hubspot_Deals API rate limits
- Validate API endpoint URLs

### Port Conflicts
If you encounter port conflicts, update the ports in your configuration and rebuild:

```bash
# Check port usage
netstat -tulpn | grep :5200

# Update configuration and restart
docker-compose down
docker-compose up -d
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Generated by DLT Generator - Customized for Hubspot_Deals data extraction
