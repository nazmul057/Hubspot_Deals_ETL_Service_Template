# 📋 HubSpot Deals ETL - Integration with HubSpot CRM API

This document explains the HubSpot CRM REST API endpoints required by the HubSpot Deals ETL service to extract deal data from HubSpot CRM instances.

---

## 📋 Overview

The HubSpot Deals ETL service integrates with HubSpot CRM REST API endpoints to extract deal information. Below are the required and optional endpoints:

### ✅ **Required Endpoint (Essential)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals`             | Search and list deals               | v3          | crm.objects.deals.read   | **Required** |

### 🔧 **Optional Endpoints (Advanced Features)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals/{dealId}`    | Get detailed deal information       | v3          | crm.objects.deals.read   | Optional     |
| `/crm/v3/objects/deals/{dealId}/associations` | Get deal associations           | v3          | crm.objects.deals.read   | Optional     |
| `/crm/v3/properties/deals`          | Get deal properties schema          | v3          | crm.schemas.deals.read   | Optional     |
| `/crm/v3/pipelines/deals`           | Get deal pipeline configuration     | v3          | crm.objects.deals.read   | Optional     |

### 🎯 **Recommendation**
**Start with only the required endpoint.** The `/crm/v3/objects/deals` endpoint provides all essential deal data needed for basic deal analytics and extraction.

---

## 🔐 Authentication Requirements

### **Private App Access Token Authentication**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

### **Required Permissions**
- **crm.objects.deals.read**: Read access to deal objects
- **crm.objects.deals.write**: Write access to deal objects (for updates)
- **crm.schemas.deals.read**: Read access to deal properties schema (optional)

---

## 🌐 HubSpot CRM API Endpoints

### 🎯 **PRIMARY ENDPOINT (Required for Basic Deal Extraction)**

### 1. **Search Deals** - `/crm/v3/objects/deals` ✅ **REQUIRED**

**Purpose**: Get paginated list of all deals - **THIS IS ALL YOU NEED FOR BASIC DEAL EXTRACTION**

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals`

**Query Parameters**:
```
?limit=100&after=paging_cursor&properties=dealname,amount,dealstage&archived=false
```

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage,pipeline,closedate
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure** (Contains ALL essential deal data):
```json
{
  "results": [
    {
      "id": "12345678901",
      "properties": {
        "dealname": "Enterprise Software License",
        "amount": "50000",
        "dealstage": "qualifiedtobuy",
        "pipeline": "default",
        "closedate": "2024-12-31T23:59:59.999Z",
        "createdate": "2024-01-15T10:30:00.000Z",
        "hs_lastmodifieddate": "2024-01-20T14:45:00.000Z",
        "hubspot_owner_id": "12345678",
        "dealtype": "newbusiness"
      },
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-20T14:45:00.000Z",
      "archived": false
    },
    {
      "id": "12345678902",
      "properties": {
        "dealname": "Consulting Services Contract",
        "amount": "25000",
        "dealstage": "appointmentscheduled",
        "pipeline": "default",
        "closedate": "2024-11-30T23:59:59.999Z",
        "createdate": "2024-01-10T09:15:00.000Z",
        "hs_lastmodifieddate": "2024-01-18T16:20:00.000Z",
        "hubspot_owner_id": "87654321",
        "dealtype": "existingbusiness"
      },
      "createdAt": "2024-01-10T09:15:00.000Z",
      "updatedAt": "2024-01-18T16:20:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "12345678902",
      "link": "https://api.hubapi.com/crm/v3/objects/deals?after=12345678902"
    }
  }
}
```

**✅ This endpoint provides ALL the default deal fields:**
- **id**: Unique deal identifier
- **properties**: Deal properties including dealname, amount, dealstage, pipeline
- **createdAt/updatedAt**: Timestamps for creation and last modification
- **archived**: Boolean indicating if deal is archived
- **paging**: Pagination information for retrieving additional results

**Rate Limit**: 100 requests per 10 seconds per app per account

---

## 📋 **Query Parameters Documentation**

### **Required Parameters**
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `limit` | integer | No | Number of results to return (max 100) | `limit=100` |
| `after` | string | No | Paging cursor for pagination | `after=12345678902` |
| `properties` | string | No | Comma-separated list of properties to include | `properties=dealname,amount,dealstage` |
| `archived` | boolean | No | Include archived deals (default: false) | `archived=false` |

### **Additional Parameters**
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `filter` | string | No | Filter deals by criteria | `filter=dealstage=qualifiedtobuy` |
| `sort` | string | No | Sort results by property | `sort=createdate` |
| `sortDirection` | string | No | Sort direction (asc/desc) | `sortDirection=desc` |

---

## 🔧 **OPTIONAL ENDPOINTS (Advanced Features Only)**

> **⚠️ Note**: These endpoints are NOT required for basic deal extraction. Only implement if you need advanced deal analytics like associations, detailed properties, or pipeline configuration.

### 2. **Get Deal Details** - `/crm/v3/objects/deals/{dealId}` 🔧 **OPTIONAL**

**Purpose**: Get detailed information for a specific deal

**When to use**: Only if you need additional deal metadata not available in search

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/{dealId}`

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals/12345678901
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[field_id]": "[sample_id]",
  "[field_url]": "https://[your_instance].[platform_domain]/[api_path]/[endpoint_1]/[sample_id]",
  "[field_name]": "[Sample Object Name]",
  "[field_type]": "[object_type]",
  "[additional_field_1]": {
    "[sub_field_1]": [
      {
        "[property_1]": "[value_1]",
        "[property_2]": "[value_2]",
        "[property_3]": true
      }
    ],
    "[sub_field_2]": [
      {
        "[property_4]": "[value_4]",
        "[property_5]": "[value_5]"
      }
    ]
  },
  "[nested_object]": {
    "[nested_field_1]": "[value_1]",
    "[nested_field_2]": "[value_2]",
    "[nested_field_3]": "[value_3]",
    "[nested_field_4]": "[value_4]",
    "[nested_field_5]": "[value_5]"
  },
  "[boolean_field_1]": true,
  "[boolean_field_2]": false,
  "[boolean_field_3]": false
}
```

---

### 3. **Get [Object] [Related Data]** - `/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [related data] associated with a [object]

**When to use**: Only if you need [related data] analysis and [specific metrics]

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]`

**Query Parameters**:
```
?[param1]=[value]&[param2]=[value]&[filter_param]=[filter_value]
```

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_2]/[sample_id]/[related_endpoint]?[param2]=[value]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[pagination_start]": 0,
  "[pagination_size]": 50,
  "[pagination_total]": 25,
  "[pagination_last]": false,
  "[data_array]": [
    {
      "[related_id]": 1,
      "[related_url]": "https://[your_instance].[platform_domain]/[api_path]/[related_endpoint]/1",
      "[related_status]": "[status_1]",
      "[related_name]": "[Related Item 1]",
      "[date_start]": "[date_format]",
      "[date_end]": "[date_format]",
      "[date_complete]": "[date_format]",
      "[date_created]": "[date_format]",
      "[origin_field]": "[sample_id]",
      "[description_field]": "[Description text]"
    },
    {
      "[related_id]": 2,
      "[related_url]": "https://[your_instance].[platform_domain]/[api_path]/[related_endpoint]/2",
      "[related_status]": "[status_2]", 
      "[related_name]": "[Related Item 2]",
      "[date_start]": "[date_format]",
      "[date_end]": "[date_format]",
      "[date_created]": "[date_format]",
      "[origin_field]": "[sample_id]",
      "[description_field]": "[Description text]"
    }
  ]
}
```

---

### 4. **Get [Object] Configuration** - `/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [object] configuration details ([config_type_1], [config_type_2], [config_type_3])

**When to use**: Only if you need [workflow type] and [object] setup analysis

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]`

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_3]/[sample_id]/[config_endpoint]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[field_id]": "[sample_id]",
  "[field_name]": "[Sample Object Name]",
  "[field_type]": "[object_type]",
  "[field_url]": "https://[your_instance].[platform_domain]/[api_path]/[endpoint_3]/[sample_id]/[config_endpoint]",
  "[location_field]": {
    "[location_type]": "[location_value]",
    "[location_identifier]": "[identifier]"
  },
  "[filter_field]": {
    "[filter_id]": "[filter_value]",
    "[filter_url]": "https://[your_instance].[platform_domain]/[api_path]/[filter_endpoint]/[filter_value]"
  },
  "[config_object]": {
    "[config_array]": [
      {
        "[config_name]": "[Config Item 1]",
        "[config_values]": [
          {
            "[config_id]": "[id_1]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_1]"
          }
        ]
      },
      {
        "[config_name]": "[Config Item 2]",
        "[config_values]": [
          {
            "[config_id]": "[id_2]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_2]"
          }
        ]
      },
      {
        "[config_name]": "[Config Item 3]",
        "[config_values]": [
          {
            "[config_id]": "[id_3]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_3]"
          }
        ]
      }
    ],
    "[constraint_type]": "[constraint_value]"
  },
  "[estimation_field]": {
    "[estimation_type]": "[estimation_value]",
    "[estimation_details]": {
      "[detail_id]": "[detail_value]",
      "[detail_name]": "[Detail Display Name]"
    }
  }
}
```

---

### 5. **Get [Object] [Additional Data]** - `/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [additional data] for a [object]

**When to use**: Only if you need [additional data] analysis and [specific functionality]

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]`

**Query Parameters**:
```
?[param1]=[value]&[param2]=[value]&[query_param]=[query_value]&[validation_param]=[validation_value]&[fields_param]=[field1],[field2],[field3],[field4]
```

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_4]/[sample_id]/[additional_endpoint]?[param2]=[value]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[pagination_start]": 0,
  "[pagination_size]": 50,
  "[pagination_total]": 120,
  "[data_key]": [
    {
      "[item_id]": "[item_id_value]",
      "[item_key]": "[ITEM-123]",
      "[item_url]": "https://[your_instance].[platform_domain]/[api_path]/[item_endpoint]/[item_id_value]",
      "[item_fields]": {
        "[summary_field]": "[Item summary text]",
        "[status_field]": {
          "[status_id]": "[status_id_value]",
          "[status_name]": "[Status Name]",
          "[status_category]": {
            "[category_id]": 2,
            "[category_key]": "[category_key]",
            "[category_color]": "[color-name]"
          }
        },
        "[assignee_field]": {
          "[assignee_id]": "[assignee_account_id]",
          "[assignee_name]": "[Assignee Name]"
        },
        "[priority_field]": {
          "[priority_id]": "[priority_id_value]",
          "[priority_name]": "[Priority Level]"
        }
      }
    }
  ]
}
```

---

## 📊 Data Extraction Flow

### 🎯 **SIMPLE FLOW (Recommended - Using Only Required Endpoint)**

### **Single Endpoint Approach - `/crm/v3/objects/deals` Only**
```python
def extract_all_deals_simple():
    """Extract all deals using only the /crm/v3/objects/deals endpoint"""
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }
    
    all_deals = []
    after_cursor = None
    
    while True:
        params = {
            "limit": 100,
            "properties": "dealname,amount,dealstage,pipeline,closedate,createdate,hs_lastmodifieddate,hubspot_owner_id,dealtype"
        }
        
        if after_cursor:
            params["after"] = after_cursor
            
        response = requests.get(
            f"{base_url}/crm/v3/objects/deals",
            params=params,
            headers=headers
        )
        
        if response.status_code == 429:  # Rate limited
            retry_after = int(response.headers.get('Retry-After', 10))
            time.sleep(retry_after)
            continue
            
        response.raise_for_status()
        data = response.json()
        
        deals = data.get("results", [])
        if not deals:  # No more deals
            break
            
        all_deals.extend(deals)
        
        # Check if there are more pages
        paging = data.get("paging", {})
        if "next" in paging:
            after_cursor = paging["next"]["after"]
        else:
            break
    
    return all_deals

# This gives you ALL essential deal data:
# - id, properties (dealname, amount, dealstage, pipeline, etc.)
# - createdAt, updatedAt timestamps
# - archived status
# - pagination information
```

---

### 🔧 **ADVANCED FLOW (Optional - Multiple Endpoints)**

> **⚠️ Only use this if you need [related_data], [configuration], or [additional_data] data**

### **Step 1: Batch [Object] Retrieval**
```python
# Get [objects] in batches of 50
for start_at in range(0, total_objects, 50):
    response = requests.get(
        f"{base_url}/[api_path]/[primary_endpoint]",
        params={
            "[pagination_param]": start_at,
            "[size_param]": 50
        },
        headers=auth_headers
    )
    objects_data = response.json()
    objects = objects_data.get("[data_array]", [])
```

### **Step 2: Enhanced [Object] Details (Optional)**
```python
# Get detailed information for each [object]
for obj in objects:
    response = requests.get(
        f"{base_url}/[api_path]/[endpoint_1]/{obj['[field_id]']}",
        headers=auth_headers
    )
    detailed_object = response.json()
```

### **Step 3: [Object] [Related Data] (Optional)**
```python
# Get [related data] for each [specific type] [object]
for obj in objects:
    if obj['[field_type]'] == '[specific_type]':
        response = requests.get(
            f"{base_url}/[api_path]/[endpoint_2]/{obj['[field_id]']}/[related_endpoint]",
            params={"[param2]": 50},
            headers=auth_headers
        )
        object_related_data = response.json()
```

### **Step 4: [Object] Configuration (Optional)**
```python
# Get configuration for each [object]
for obj in objects:
    response = requests.get(
        f"{base_url}/[api_path]/[endpoint_3]/{obj['[field_id]']}/[config_endpoint]",
        headers=auth_headers
    )
    object_config = response.json()
```

---

## 📊 **Available Deal Properties**

### **Default HubSpot Deal Properties**
| Property Name | Type | Description | Example |
|---------------|------|-------------|---------|
| `dealname` | string | Name of the deal | "Enterprise Software License" |
| `amount` | string | Deal amount/value | "50000" |
| `dealstage` | string | Current stage in pipeline | "qualifiedtobuy" |
| `pipeline` | string | Pipeline the deal belongs to | "default" |
| `closedate` | datetime | Expected close date | "2024-12-31T23:59:59.999Z" |
| `createdate` | datetime | Deal creation date | "2024-01-15T10:30:00.000Z" |
| `hs_lastmodifieddate` | datetime | Last modification date | "2024-01-20T14:45:00.000Z" |
| `hubspot_owner_id` | string | Owner's HubSpot user ID | "12345678" |
| `dealtype` | string | Type of deal | "newbusiness" |
| `description` | string | Deal description | "Multi-year enterprise license" |
| `hs_deal_stage_probability` | string | Probability percentage | "75" |
| `hs_analytics_source` | string | Source of the deal | "website" |
| `hs_analytics_source_data_1` | string | Additional source data | "organic" |
| `hs_analytics_source_data_2` | string | Additional source data | "google" |

### **Custom Properties**
- Custom properties can be created in HubSpot and will have names like `custom_property_name`
- To get all available properties (including custom ones), use: `GET /crm/v3/properties/deals`

---

## ⚡ Performance Considerations

### **Rate Limiting**
- **Default Limit**: 100 requests per 10 seconds per app per account
- **Burst Limit**: 150 requests per 10 seconds (short duration)
- **Best Practice**: Implement exponential backoff on 429 responses

### **Batch Processing**
- **Recommended Batch Size**: 100 deals per request (maximum)
- **Concurrent Requests**: Max 10 parallel requests (deals are complex objects)
- **Request Interval**: 100ms between requests to stay under rate limits

### **Error Handling**
```http
# Rate limit exceeded
HTTP/429 Too Many Requests
Retry-After: 10

# Authentication failed  
HTTP/401 Unauthorized

# Insufficient permissions
HTTP/403 Forbidden

# Deal not found
HTTP/404 Not Found

# Invalid request
HTTP/400 Bad Request
```

---

## 🔒 Security Requirements

### **API Token Permissions**

#### ✅ **Required (Minimum Permissions)**
```
Required Scopes:
- [scope_1] (for basic [object] information)
```

#### 🔧 **Optional (Advanced Features)**
```
Additional Scopes (only if using optional endpoints):
- [scope_2] (for [related data] information)
- [scope_3] (for [object] configuration)
```

### **User Permissions**

#### ✅ **Required (Minimum)**
The API token user must have:
- **[Permission_1]** global permission
- **[Permission_2]** permission

#### 🔧 **Optional (Advanced Features)**
Additional permissions (only if using optional endpoints):
- **[Permission_3]** permission (for [object] configuration details)
- **[Permission_4]** (for [additional data] access)

---

## 📈 Monitoring & Debugging

### **Request Headers for Debugging**
```http
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
User-Agent: [ServiceName]/1.0
X-Request-ID: [object]-scan-001-batch-1
```

### **Response Validation**
```python
def validate_object_response(object_data):
    required_fields = ["[field_id]", "[field_name]", "[field_type]", "[nested_object]"]
    for field in required_fields:
        if field not in object_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate [object] type
    if object_data["[field_type]"] not in ["[type_1]", "[type_2]"]:
        raise ValueError(f"Invalid [object] type: {object_data['[field_type]']}")
```

### **API Usage Metrics**
- Track requests per [time period]
- Monitor response times
- Log rate limit headers
- Track authentication failures

---

## 🧪 Testing API Integration

### **Test Authentication**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Search**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=5&properties=dealname,amount,dealstage" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Details**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals/12345678901" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Properties Schema**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 🚨 Common Issues & Solutions

### **Issue**: 401 Unauthorized
**Solution**: Verify [auth method] and [credential] combination
```bash
[verification_command]
```

### **Issue**: 403 Forbidden
**Solution**: Check user has "[Permission_1]" and "[Permission_2]" permissions

### **Issue**: [Rate Limit Code] Rate Limited
**Solution**: Implement retry with exponential backoff
```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

### **Issue**: Empty [Object] List
**Solution**: Check if user has access to [parent objects] with [object type] [objects]

### **Issue**: Need [Related Data]/Configuration But Want to Keep It Simple**
**Solution**: Start with `/[primary_endpoint]` only. Add optional endpoints later if needed for advanced [object type] analytics

---

## 💡 **Implementation Recommendations**

### 🎯 **Phase 1: Start Simple (Recommended)**
1. Implement only `/[api_path]/[primary_endpoint]`
2. Extract basic [object] data ([field_id], [field_name], [field_type], [nested_object] info)
3. This covers 90% of [object type] analytics needs

### 🔧 **Phase 2: Add Advanced Features (If Needed)**
1. Add `/[api_path]/[endpoint_1]/{objectId}` for detailed [object] info
2. Add `/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]` for [related data] analysis  
3. Add `/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]` for [workflow type] analysis
4. Add `/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]` for [additional functionality]

### ⚡ **Performance Tip**
- **Simple approach**: 1 API call per [batch_size] [objects]
- **Advanced approach**: 1 + N API calls (N = number of [objects] for details)
- Start simple to minimize API usage and complexity!

---

## 📞 Support Resources

- **HubSpot CRM API Documentation**: https://developers.hubspot.com/docs/api/crm/deals
- **Rate Limiting Guide**: https://developers.hubspot.com/docs/api/rate-limits
- **Authentication Guide**: https://developers.hubspot.com/docs/api/private-apps
- **Deals Properties Reference**: https://developers.hubspot.com/docs/api/crm/properties
- **HubSpot API Status**: https://status.hubspot.com/
- **HubSpot Developer Community**: https://community.hubspot.com/t5/HubSpot-APIs-Integrations/ct-p/apis