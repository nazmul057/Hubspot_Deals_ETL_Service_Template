# HubSpot Deals ETL - API Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URLs](#base-urls)
4. [Common Response Formats](#common-response-formats)
5. [API Endpoints](#api-endpoints)
6. [Health & Stats Endpoints](#health--stats-endpoints)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Rate Limiting](#rate-limiting)
10. [Changelog](#changelog)

## 🔍 Overview

The HubSpot Deals ETL service provides REST API endpoints for extracting, managing, and analyzing HubSpot CRM deal data. The service supports multi-tenant operations with comprehensive ETL job tracking and deal data management.

### API Version
- **Version**: 1.0.0
- **Base Path**: `/api`
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI)

### Key Features
- **HubSpot Deals Extraction**: Extract deal data from HubSpot CRM API v3
- **Multi-tenant Support**: Isolated data access per tenant
- **ETL Job Management**: Track extraction progress and status
- **Flexible Data Export**: Download results in JSON, CSV, and Excel formats
- **Real-time Monitoring**: Monitor extraction progress and performance metrics

## 🔐 Authentication

The HubSpot Deals ETL service uses API key-based authentication with tenant isolation. Each request must include a valid API key and tenant identifier.

### Required Credentials
- **API Key**: Service authentication token
- **Tenant ID**: Multi-tenant isolation identifier
- **HubSpot Private App Token**: Required for HubSpot API access (stored in scan configuration)

### Required Permissions
- `deals:read` - Read access to deal extraction endpoints
- `deals:write` - Write access to start/manage extractions
- `admin:manage` - Administrative access to all operations

### Authentication Headers
```
Authorization: Bearer <api_key>
X-Tenant-ID: <tenant_id>
Content-Type: application/json
```

## 🌐 Base URLs

### Development
```
http://localhost:5200
```

### Staging
```
http://localhost:5201
```

### Production
```
http://localhost:5202
```

### Swagger Documentation
```
http://localhost:5200/docs
```

## 📊 Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response (Validation)
```json
{
  "status": "error",
  "message": "Input validation failed",
  "errors": {
    "[field_name]": "Field is required"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response (Application Logic)
```json
{
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "The requested resource was not found",
  "details": {},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Pagination Response
```json
{
  "pagination": {
    "current_page": 1,
    "page_size": 50,
    "total_items": 150,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  }
}
```

## 🔍 Deal Extraction Endpoints

### 1. Start Deal Extraction

**POST** `/api/scan/start`

Initiates a new HubSpot deals extraction process for the specified tenant.

#### Request Body
```json
{
    "config": {
      "scanId": "scan-try-1",
      "organizationId": "12345",
      "type": ["user"],
      "auth": {
        "accessToken": "access-token-xxxxxxxxxxxxxxx-ooooooo"
      },
      "filters": {
        "dateRange": {
          "startDate": "2025-01-01",
          "endDate": "2025-12-31"
        }
      }
    }
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config.scanId` | string | Yes | Unique identifier for the scan (alphanumeric, hyphens, underscores only, max 255 chars) |
| `config.type` | array | Yes | Service types to scan (must include "user") |
| `config.auth.accessToken` | string | Yes | HubSpot Private App access token |
| `config.filters.properties` | array | No | HubSpot deal properties to extract (default: all standard properties) |
| `config.filters.archived` | boolean | No | Include archived deals (default: false) |
| `config.filters.dateRange.startDate` | string | No | Start date for filtering deals (YYYY-MM-DD format) |
| `config.filters.dateRange.endDate` | string | No | End date for filtering deals (YYYY-MM-DD format) |

#### Response
```json
{
    "success": true,
    "message": "Scan initialization accepted and is now processing in the background."
}
```

#### Status Codes
- **202**: Extraction started successfully
- **400**: Invalid request data or HubSpot token
- **409**: Extraction already in progress for this scan ID
- **401**: Invalid API key or tenant ID
- **500**: Internal server error

---

### 2. Get Extraction Status

**GET** `/api/scan/status/{scan_id}`

Retrieves the current status of a HubSpot deals extraction process.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (Existing Extraction)
```json
{
  "status": "success",
  "data": {
    "id": "uuid-internal-job-id",
    "scanId": "hubspot-deals-scan-001",
    "tenantId": "tenant-123",
    "status": "running",
    "scanType": "hubspot_deals",
    "startedAt": "2024-01-15T10:30:00Z",
    "completedAt": null,
    "errorMessage": null,
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:35:00Z",
    "progress": {
      "totalDeals": 1500,
      "processedDeals": 750,
      "failedDeals": 5,
      "successRate": 99.33,
      "apiCallsMade": 8,
      "rateLimitRemaining": 92
    }
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

#### Response (Non-existent Extraction)
```json
{
  "status": "success",
  "data": {
    "id": null,
    "scanId": null,
    "tenantId": null,
    "status": "not_found",
    "startedAt": null,
    "completedAt": null,
    "errorMessage": null,
    "createdAt": null,
    "updatedAt": null,
    "progress": null
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

#### Status Values
- **pending**: Extraction queued but not started
- **running**: Extraction in progress
- **completed**: Extraction finished successfully
- **failed**: Extraction failed with error
- **cancelled**: Extraction cancelled by user
- **not_found**: Extraction does not exist

#### Status Codes
- **200**: Always returns 200 (check `data.status` field for actual state)
- **400**: Invalid scan ID format
- **401**: Invalid API key or tenant ID

---

### 3. Cancel Extraction

**POST** `/scan/cancel/{scan_id}`

Cancels an ongoing extraction process.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response
```json
{
  "message": "Extraction cancelled successfully",
  "scanId": "unique-scan-identifier",
  "status": "cancelled"
}
```

#### Status Codes
- **200**: Extraction cancelled successfully
- **400**: Invalid scan ID format or extraction cannot be cancelled
- **404**: Extraction not found
- **500**: Internal server error

---

### 4. Remove Extraction

**DELETE** `/scan/remove/{scan_id}`

Removes an extraction and all associated data from the system.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response
```json
{
  "message": "Extraction and 1,234 events removed successfully",
  "scanId": "unique-scan-identifier",
  "status": "removed"
}
```

#### Status Codes
- **200**: Extraction removed successfully
- **400**: Invalid scan ID format or extraction cannot be removed
- **404**: Extraction not found
- **500**: Internal server error

---

### 5. Get Extraction Results

**GET** `/api/v1/deals/scan/result/{scan_id}`

Retrieves paginated HubSpot deals extraction results with full deal details.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (minimum: 1) |
| `page_size` | integer | No | 100 | Deals per page (1-1000) |
| `dealstage` | string | No | null | Filter by deal stage |
| `pipeline` | string | No | null | Filter by pipeline |
| `archived` | boolean | No | false | Include archived deals |

#### Response
```json
{
  "status": "success",
  "data": {
    "scanId": "hubspot-deals-scan-001",
    "status": "completed",
    "tenantId": "tenant-123",
    "deals": [
      {
        "id": "uuid-deal-id",
        "hubspotDealId": "12345678901",
        "dealname": "Enterprise Software License",
        "amount": 50000.00,
        "dealstage": "qualifiedtobuy",
        "pipeline": "default",
        "closedate": "2024-12-31T23:59:59.999Z",
        "createdate": "2024-01-15T10:30:00.000Z",
        "hsLastmodifieddate": "2024-01-20T14:45:00.000Z",
        "hubspotOwnerId": "12345678",
        "dealtype": "newbusiness",
        "description": "Multi-year enterprise license agreement",
        "hsDealStageProbability": 75.00,
        "archived": false,
        "rawProperties": {
          "hs_analytics_source": "website",
          "hs_analytics_source_data_1": "organic"
        },
        "associations": {
          "contacts": [{"id": "contact-123"}],
          "companies": [{"id": "company-456"}]
        },
        "extractedAt": "2024-01-15T10:30:00Z",
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 100,
      "total_deals": 1500,
      "total_pages": 15,
      "has_next": true,
      "has_previous": false,
      "next_page": 2,
      "previous_page": null
    },
    "summary": {
      "total_deals": 1500,
      "total_value": 7500000.00,
      "deals_by_stage": {
        "qualifiedtobuy": 450,
        "appointmentscheduled": 300,
        "closedwon": 200
      },
      "deals_by_pipeline": {
        "default": 1200,
        "enterprise": 300
      }
    }
  },
  "timestamp": "2024-01-15T10:45:00Z"
}
```

#### Status Codes
- **200**: Results retrieved successfully
- **400**: Invalid scan ID format or pagination parameters
- **401**: Invalid API key or tenant ID
- **404**: Extraction not found
- **500**: Internal server error

---

### 6. Download Extraction Results

**GET** `/api/v1/deals/scan/download/{scan_id}/{format}`

Downloads HubSpot deals extraction results in the specified format.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |
| `format` | string | Yes | Download format (json, csv, excel) |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `dealstage` | string | No | null | Filter by deal stage |
| `pipeline` | string | No | null | Filter by pipeline |
| `archived` | boolean | No | false | Include archived deals |

#### Supported Formats
- **json**: JSON format with pretty printing
- **csv**: Comma-separated values with headers
- **excel**: Microsoft Excel (.xlsx) format

#### Response
File download with appropriate content-type and Content-Disposition headers:
- **JSON**: `Content-Type: application/json`
- **CSV**: `Content-Type: text/csv`
- **Excel**: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

#### Status Codes
- **200**: File download initiated
- **400**: Invalid scan ID format or unsupported format
- **401**: Invalid API key or tenant ID
- **404**: Extraction not found
- **500**: Internal server error

#### Example URLs
```
GET /api/scan/download/hubspot-deals-scan-001/json
GET /api/scan/download/hubspot-deals-scan-001/csv?dealstage=qualifiedtobuy
GET /api/scan/download/hubspot-deals-scan-001/excel?pipeline=enterprise
```

---

## 🏥 Health & Stats Endpoints

### 1. Health Check

**GET** `/api/v1/health`

Returns the overall health status of the HubSpot Deals ETL service.

#### Response (Healthy)
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "HubSpot Deals ETL",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "hubspot_api": "healthy",
    "redis_cache": "healthy",
    "disk_space": "healthy"
  }
}
```

#### Response (Unhealthy)
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "HubSpot Deals ETL",
  "version": "1.0.0",
  "checks": {
    "database": "unhealthy: connection timeout",
    "hubspot_api": "degraded: high latency",
    "redis_cache": "healthy",
    "disk_space": "healthy"
  }
}
```

#### Status Codes
- **200**: Service is healthy
- **503**: Service is unhealthy

---

### 2. Service Statistics

**GET** `/api/v1/stats`

Returns comprehensive service statistics and performance metrics.

#### Response
```json
{
  "status": "success",
  "data": {
    "service_metrics": {
      "total_requests": 15000,
      "active_connections": 23,
      "success_rate": 99.5,
      "average_response_time": 125.5,
      "errors_last_hour": 5,
      "uptime": "7 days, 3:24:15",
      "memory_usage": "512MB",
      "cpu_usage": "15%",
      "last_restart": "2024-01-08T10:30:00Z"
    },
    "etl_metrics": {
      "total_extractions": 45,
      "active_extractions": 3,
      "completed_extractions": 40,
      "failed_extractions": 2,
      "total_deals_processed": 75000,
      "average_deals_per_extraction": 1667,
      "hubspot_api_calls_made": 1200,
      "hubspot_rate_limit_remaining": 88
    },
    "tenant_metrics": {
      "total_tenants": 12,
      "active_tenants": 8,
      "deals_per_tenant": {
        "tenant-123": 5000,
        "tenant-456": 3000,
        "tenant-789": 2000
      }
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Status Codes
- **200**: Statistics retrieved successfully
- **401**: Invalid API key
- **500**: Internal server error

---

## ⚠️ Error Handling

### Error Response Formats

#### Validation Errors (400)
Returned for input validation failures:
```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "errors": {
    "[field_name]": "[error_message]"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Authentication Errors (401)
```json
{
  "status": "error",
  "error_code": "UNAUTHORIZED",
  "message": "Authentication required",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Authorization Errors (403)
```json
{
  "status": "error",
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Not Found Errors (404)
```json
{
  "status": "error",
  "error_code": "NOT_FOUND",
  "message": "Resource not found",
  "resource_id": "[id]",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Conflict Errors (409)
```json
{
  "status": "error",
  "error_code": "CONFLICT",
  "message": "Resource already exists",
  "conflicting_field": "[field_name]",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Rate Limit Errors (429)
```json
{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests",
  "retry_after": 60,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Server Errors (500)
```json
{
  "status": "error",
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "incident_id": "inc_123456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Server error |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

---

## 📚 Examples

### Complete HubSpot Deals Extraction Workflow

#### 1. Start Deal Extraction
```bash
curl -X POST "http://localhost:5200/api/scan/start" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "scanId": "scan-try-1",
      "organizationId": "12345",
      "type": ["user"],
      "auth": {
        "accessToken": "-----------xxxxxxx"
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

#### 2. Monitor Progress
```bash
curl -H "Authorization: Bearer your-api-key" \
     -H "X-Tenant-ID: tenant-123" \
     "http://localhost:5200/api/scan/status/hubspot-deals-weekly-001"
```

#### 3. Get Results
```bash
curl -H "Authorization: Bearer your-api-key" \
     -H "X-Tenant-ID: tenant-123" \
     "http://localhost:5200/api/scan/result/hubspot-deals-weekly-001?page=1&page_size=50"
```

#### 4. Download Results
```bash
# Download as CSV
curl -H "Authorization: Bearer your-api-key" \
     -H "X-Tenant-ID: tenant-123" \
     "http://localhost:5200/api/scan/download/hubspot-deals-weekly-001/csv" \
     -o "hubspot_deals_results.csv"

# Download as Excel
curl -H "Authorization: Bearer your-api-key" \
     -H "X-Tenant-ID: tenant-123" \
     "http://localhost:5200/api/scan/download/hubspot-deals-weekly-001/excel" \
     -o "hubspot_deals_results.xlsx"

# Download as JSON
curl -H "Authorization: Bearer your-api-key" \
     -H "X-Tenant-ID: tenant-123" \
     "http://localhost:5200/api/scan/download/hubspot-deals-weekly-001/json" \
     -o "hubspot_deals_results.json"
```

#### 5. Cancel Extraction (if needed)
```bash
curl -X POST -H "Authorization: Bearer your-api-key" \
     -H "X-Tenant-ID: tenant-123" \
     "http://localhost:5200/api/scan/cancel/hubspot-deals-weekly-001"
```

#### 6. Remove Extraction (cleanup)
```bash
curl -X DELETE -H "Authorization: Bearer your-api-key" \
     -H "X-Tenant-ID: tenant-123" \
     "http://localhost:5200/api/scan/remove/hubspot-deals-weekly-001"
```

### PowerShell Examples

#### Start Deal Extraction
```powershell
$headers = @{
    "Authorization" = "Bearer your-api-key"
    "X-Tenant-ID" = "tenant-123"
    "Content-Type" = "application/json"
}

$body = @{
  config = @{
    scanId = "powershell-deals-001"
    type = @("deals")
    auth = @{
      "hubspot_token" = "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
      "base_url" = "https://api.hubapi.com"
    }
    filters = @{
      properties = @("dealname", "amount", "dealstage", "pipeline", "closedate")
      archived = $false
      limit = 100
    }
    dateRange = @{
      startDate = "2024-01-01"
      endDate = "2024-01-31"
    }
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:5200/api/v1/deals/scan/start" -Method Post -Body $body -Headers $headers
```

#### Get Status
```powershell
$headers = @{
    "Authorization" = "Bearer your-api-key"
    "X-Tenant-ID" = "tenant-123"
}

Invoke-RestMethod -Uri "http://localhost:5200/api/v1/deals/scan/status/powershell-deals-001" -Headers $headers
```

#### Download Results
```powershell
$headers = @{
    "Authorization" = "Bearer your-api-key"
    "X-Tenant-ID" = "tenant-123"
}

# Download Excel file
Invoke-WebRequest -Uri "http://localhost:5200/api/v1/deals/scan/download/powershell-deals-001/excel" -Headers $headers -OutFile "hubspot_deals_results.xlsx"

# Download CSV file
Invoke-WebRequest -Uri "http://localhost:5200/api/v1/deals/scan/download/powershell-deals-001/csv" -Headers $headers -OutFile "hubspot_deals_results.csv"
```

### Python Examples

#### Start Deal Extraction
```python
import requests

url = "http://localhost:5200/api/v1/deals/scan/start"
headers = {
    "Authorization": "Bearer your-api-key",
    "X-Tenant-ID": "tenant-123",
    "Content-Type": "application/json"
}

payload = {
    "config": {
        "scanId": "python-deals-001",
        "type": ["deals"],
        "auth": {
            "hubspot_token": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "base_url": "https://api.hubapi.com"
        },
        "filters": {
            "properties": ["dealname", "amount", "dealstage", "pipeline", "closedate"],
            "archived": False,
            "limit": 100
        },
        "dateRange": {
            "startDate": "2024-01-01",
            "endDate": "2024-01-31"
        }
    }
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

#### Monitor Progress
```python
import requests
import time

scan_id = "python-deals-001"
url = f"http://localhost:5200/api/v1/deals/scan/status/{scan_id}"
headers = {
    "Authorization": "Bearer your-api-key",
    "X-Tenant-ID": "tenant-123"
}

while True:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        status = data['data']['status']
        
        print(f"Status: {status}")
        if 'progress' in data['data'] and data['data']['progress']:
            progress = data['data']['progress']
            print(f"Progress: {progress['processedDeals']}/{progress['totalDeals']} deals")
        
        if status in ['completed', 'failed', 'cancelled', 'not_found']:
            break
    
    time.sleep(10)  # Check every 10 seconds
```

#### Get Paginated Results
```python
import requests

scan_id = "python-deals-001"
page = 1
all_deals = []
headers = {
    "Authorization": "Bearer your-api-key",
    "X-Tenant-ID": "tenant-123"
}

while True:
    url = f"http://localhost:5200/api/v1/deals/scan/result/{scan_id}?page={page}&page_size=100"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        all_deals.extend(data['data']['deals'])
        
        if not data['data']['pagination']['has_next']:
            break
        
        page += 1
    else:
        print(f"Error: {response.status_code}")
        break

print(f"Total deals retrieved: {len(all_deals)}")
```

#### Download Results
```python
import requests

scan_id = "python-deals-001"
headers = {
    "Authorization": "Bearer your-api-key",
    "X-Tenant-ID": "tenant-123"
}

# Download different formats
formats = ['json', 'csv', 'excel']
for fmt in formats:
    url = f"http://localhost:5200/api/v1/deals/scan/download/{scan_id}/{fmt}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        filename = f"hubspot_deals_results.{fmt if fmt != 'excel' else 'xlsx'}"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {fmt}: {response.status_code}")
```

#### Error Handling
```python
import requests