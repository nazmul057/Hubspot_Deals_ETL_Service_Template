# 🗄️ HubSpot Deals ETL Database Schema

This document provides a PostgreSQL database schema for implementing HubSpot deals ETL functionality with multi-tenant support, performance optimization, and comprehensive data tracking.

---

## 📋 Overview

The HubSpot Deals ETL database schema consists of two main tables:

1. **jobs** - Core ETL job management and tracking
2. **hubspot_deals_[type]_[organization_id]** - Storage for extracted HubSpot deal data with ETL metadata and the provided type and organization id.

### **Key Features:**
- ✅ **Multi-tenant data isolation** with `tenant_id` partitioning
- ✅ **ETL metadata tracking** (`_extracted_at`, `_scan_id`, `_tenant_id`)
- ✅ **Performance-optimized indexes** for common query patterns
- ✅ **HubSpot property type mapping** to PostgreSQL types
- ✅ **Comprehensive audit trail** with timestamps and job tracking

---

## 🏗️ Table Schemas

### 1. jobs Table

**Purpose**: Core ETL job management and status tracking for HubSpot deals extraction

| **Column Name**         | **Type**    | **Constraints**           | **Description**                          |
|-------------------------|-------------|---------------------------|------------------------------------------|
| `id`                    | UUID        | PRIMARY KEY               | Unique internal identifier               |
| `organizationid`               | VARCHAR(255)| UNIQUE, NOT NULL, INDEX   | Organization id                 |
| `tenant_id`             | VARCHAR(100)| NOT NULL, INDEX           | Multi-tenant isolation identifier        |
| `status`                | VARCHAR(20) | NOT NULL, INDEX           | pending, running, completed, failed, cancelled |
| `type`             | VARCHAR(50) | NOT NULL DEFAULT 'hubspot_deals' | Type of scan (hubspot_deals) |
| `config`                | JSONB       | NOT NULL                  | HubSpot API configuration and parameters |
| `error_message`         | TEXT        | NULLABLE                  | Error details if scan failed            |
| `startTime`            | TIMESTAMP   | NULLABLE                  | When ETL execution started              |
| `endTime`          | TIMESTAMP   | NULLABLE                  | When ETL finished                       |
| `lastheartbeat`          | TIMESTAMP   | NULLABLE                  | Last Heart Beat                       |
| `recordsExtracted`          | Integer   | NULLABLE                  | Number of Records extracted in the scan job                       |
| `job_metadata`          | json   | NULLABLE                  | Metadata                       |

**Indexes:**
```sql
-- Performance indexes for multi-tenant ETL operations
CREATE INDEX idx_jobs_org          ON jobs (organization_id);
CREATE INDEX idx_jobs_status       ON jobs (status);
CREATE INDEX idx_jobs_type         ON jobs (type);
CREATE INDEX idx_jobs_start_time   ON jobs (start_time);
```

---

### 2. hubspot_deals Table

**Purpose**: Store extracted HubSpot deal data with ETL metadata and multi-tenant support

| **Column Name**         | **Type**    | **Constraints**           | **Description**                          |
|-------------------------|-------------|---------------------------|------------------------------------------|
| `hubspot_deal_id`                    | VARCHAR(100)        | PRIMARY KEY               | Unique result identifier                 |
| `_extracted_at`         | TIMESTAMP   | NOT NULL DEFAULT NOW()    | ETL extraction timestamp                |
| `_scan_id`              | VARCHAR(255)| NOT NULL, INDEX           | ETL scan identifier for tracking        |
| `_tenant_id`            | VARCHAR(100)| NOT NULL, INDEX           | ETL tenant identifier                   |
| `dealname`              | VARCHAR(500)| NULLABLE                  | Deal name                                |
| `amount`                | DECIMAL(15,2)| NULLABLE                 | Deal amount/value                        |
| `dealstage`             | VARCHAR(100)| NULLABLE, INDEX           | Current deal stage                       |
| `pipeline`              | VARCHAR(100)| NULLABLE, INDEX           | Pipeline name                            |
| `closedate`             | TIMESTAMP   | NULLABLE, INDEX           | Expected close date                      |
| `createdate`            | TIMESTAMP   | NULLABLE, INDEX           | Deal creation date (HubSpot)             |
| `hs_lastmodifieddate`   | TIMESTAMP   | NULLABLE, INDEX           | Last modification date (HubSpot)         |
| `hubspot_object_id`      | VARCHAR(50) | NULLABLE                  | HubSpot owner user ID                    |
| `dealtype`              | VARCHAR(100)| NULLABLE                  | Type of deal (newbusiness, existingbusiness) |
| `archived`              | BOOLEAN     | NOT NULL DEFAULT FALSE    | Whether deal is archived                 |
| `_page_number`            | Integer   | NOT NULL DEFAULT NOW()    | page |
| `_source_service`            | TIMESTAMP   | NOT NULL DEFAULT NOW()    | Record last update timestamp            |
| `_dlt_load_id`            | VARCHAR(100)   | NOT NULL DEFAULT NOW()    | Load Id            |
| `_dlt_id`            | VARCHAR(100)   | NOT NULL DEFAULT NOW()    | Dlt Id            |

**Performance Indexes:**
```sql
-- Always filter by tenant/organization first
CREATE INDEX idx_deals_org                ON hubspot_deals (_organization_id);

-- Typical time filters & stage filters
CREATE INDEX idx_deals_createdate         ON hubspot_deals (createdate);
CREATE INDEX idx_deals_closedate          ON hubspot_deals (closedate);
CREATE INDEX idx_deals_stage              ON hubspot_deals (dealstage);

-- Track by scan when investigating batches
CREATE INDEX idx_deals_scan               ON hubspot_deals (_scan_id);

```

---

## 🏗️ **Complete CREATE TABLE Statements**

### **1. jobs Table**
```sql

CREATE TABLE jobs (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id    UUID        NOT NULL,                 -- tenant/owner
    type               TEXT        NOT NULL,                 -- e.g. 'hubspot_deals'
    status             TEXT        NOT NULL CHECK (status IN ('pending','running','completed','failed','cancelled')),
    start_time         TIMESTAMPTZ NULL,
    end_time           TIMESTAMPTZ NULL,
    last_heartbeat     TIMESTAMPTZ NULL,
    records_extracted  INTEGER     DEFAULT 0 CHECK (records_extracted >= 0),
    error_message      TEXT        NULL,
    config             JSONB       NULL,                     -- connection/param snapshot
    job_metadata       JSONB       NULL,                     -- any extra runtime metadata
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

```

### **2. hubspot_deals Table**
```sql
CREATE TABLE hubspot_deals (
    -- HubSpot identifiers
    hubspot_deal_id        BIGINT      NOT NULL UNIQUE,  -- HubSpot deal ID
    hs_object_id           BIGINT      NULL,             -- if provided separately

    -- Core business fields
    dealname               TEXT        NULL,
    amount                 NUMERIC(18,2) NULL CHECK (amount IS NULL OR amount >= 0),
    dealstage              TEXT        NULL,
    pipeline               TEXT        NULL,
    closedate              TIMESTAMPTZ NULL,
    createdate             TIMESTAMPTZ NULL,
    hs_lastmodifieddate    TIMESTAMPTZ NULL,
    archived               BOOLEAN     NOT NULL DEFAULT FALSE,

    -- ETL metadata
    _extracted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _scan_id               UUID        NULL,
    _organization_id       UUID        NOT NULL,          -- your chosen tenant key
    _tenant_id             UUID        NOT NULL,          -- kept for compatibility
    _page_number           INTEGER     NULL,
    _source_service        TEXT        NULL,              -- e.g. 'hubspot_api'
    _dlt_load_id           UUID        NULL,
    _dlt_id                UUID        NOT NULL DEFAULT gen_random_uuid(),

    -- Soft primary key choice: HubSpot ID already unique. If you prefer a surrogate PK:
    -- id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Keep tenant fields in sync (you decided org==tenant)
    CONSTRAINT chk_tenant_eq_org CHECK (_tenant_id = _organization_id)
);

```

---

## 📊 **HubSpot Property Type Mapping**

### **HubSpot to PostgreSQL Type Mapping**
| HubSpot Type | PostgreSQL Type | Description | Example |
|--------------|-----------------|-------------|---------|
| `string` | `VARCHAR(n)` | Text strings | `dealname`, `dealstage` |
| `number` | `DECIMAL(15,2)` | Numeric values | `amount`, `hs_deal_stage_probability` |
| `datetime` | `TIMESTAMP` | Date/time values | `closedate`, `createdate` |
| `bool` | `BOOLEAN` | True/false values | `archived` |
| `enumeration` | `VARCHAR(100)` | Enumerated values | `dealtype`, `pipeline` |
| `json` | `JSONB` | Complex objects | `associations`, `raw_properties` |
| `text` | `TEXT` | Long text content | `description` |

### **Default HubSpot Deal Properties Mapping**
```sql
-- Core deal properties (mapped to dedicated columns)
dealname → VARCHAR(500)           -- Deal name
amount → DECIMAL(15,2)            -- Deal amount
dealstage → VARCHAR(100)          -- Deal stage
pipeline → VARCHAR(100)           -- Pipeline name
closedate → TIMESTAMP             -- Close date
createdate → TIMESTAMP            -- Creation date
hs_lastmodifieddate → TIMESTAMP   -- Last modified
hubspot_owner_id → VARCHAR(50)    -- Owner ID
dealtype → VARCHAR(100)           -- Deal type
description → TEXT                -- Description
hs_deal_stage_probability → DECIMAL(5,2) -- Probability
archived → BOOLEAN                -- Archived status

-- Analytics properties
hs_analytics_source → VARCHAR(100)
hs_analytics_source_data_1 → VARCHAR(100)
hs_analytics_source_data_2 → VARCHAR(100)

-- Complex data (stored in JSONB)
raw_properties → JSONB            -- All HubSpot properties
custom_properties → JSONB         -- Custom properties only
associations → JSONB              -- Deal associations
```

---

## 🔗 Relationships

### Primary Relationships
```sql
-- ETL Job to Deals (One-to-Many)
scan_jobs.id ← hubspot_deals.scan_job_id

-- Multi-tenant isolation
scan_jobs.tenant_id ← hubspot_deals.tenant_id
```

### Cascade Behavior
- **DELETE ScanJob**: Cascades to delete all related deals
- **Multi-tenant isolation**: All queries must include `tenant_id` filter

---

## 📊 Common Queries

### ETL Job Management

```sql
-- Get ETL job with status (multi-tenant)
SELECT id, scan_id, status, scan_type, total_deals, processed_deals, success_rate
FROM scan_jobs 
WHERE scan_id = 'hubspot-scan-001' AND tenant_id = 'tenant-123';

-- Get active ETL jobs for tenant
SELECT scan_id, status, started_at, scan_type, total_deals, processed_deals
FROM scan_jobs 
WHERE tenant_id = 'tenant-123' AND status IN ('running', 'pending') 
ORDER BY created_at DESC;

-- Get ETL progress with success rate
SELECT 
    scan_id,
    total_deals,
    processed_deals,
    failed_deals,
    CASE 
        WHEN total_deals > 0 THEN ROUND((processed_deals * 100.0 / total_deals), 2)
        ELSE 0 
    END as progress_percentage,
    success_rate
FROM scan_jobs 
WHERE scan_id = 'hubspot-scan-001' AND tenant_id = 'tenant-123';
```

### HubSpot Deals Management

```sql
-- Get paginated deals for tenant
SELECT id, hubspot_deal_id, dealname, amount, dealstage, pipeline, closedate
FROM hubspot_deals 
WHERE tenant_id = 'tenant-123' AND scan_job_id = 'job-uuid'
ORDER BY created_at 
LIMIT 100 OFFSET 0;

-- Count deals by stage for tenant
SELECT dealstage, COUNT(*) as deal_count, SUM(amount) as total_value
FROM hubspot_deals 
WHERE tenant_id = 'tenant-123' AND archived = false
GROUP BY dealstage
ORDER BY deal_count DESC;

-- Search deals by name (multi-tenant)
SELECT hubspot_deal_id, dealname, amount, dealstage, closedate
FROM hubspot_deals 
WHERE tenant_id = 'tenant-123' 
AND dealname ILIKE '%enterprise%'
ORDER BY amount DESC;

-- Get deals by owner and stage
SELECT hubspot_owner_id, dealstage, COUNT(*) as count, AVG(amount) as avg_amount
FROM hubspot_deals 
WHERE tenant_id = 'tenant-123' AND archived = false
GROUP BY hubspot_owner_id, dealstage
ORDER BY hubspot_owner_id, count DESC;

-- Get recent deals (last 30 days)
SELECT hubspot_deal_id, dealname, amount, dealstage, createdate
FROM hubspot_deals 
WHERE tenant_id = 'tenant-123' 
AND createdate >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY createdate DESC;

-- Get deals closing this month
SELECT hubspot_deal_id, dealname, amount, dealstage, closedate
FROM hubspot_deals 
WHERE tenant_id = 'tenant-123' 
AND closedate >= DATE_TRUNC('month', CURRENT_DATE)
AND closedate < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
ORDER BY closedate ASC;
```

### Control Operations

```sql
-- Get ETL job status and basic info (multi-tenant)
SELECT scan_id, status, started_at, completed_at, error_message, api_calls_made
FROM scan_jobs 
WHERE scan_id = 'hubspot-scan-001' AND tenant_id = 'tenant-123';

-- Cancel an ETL job (update status)
UPDATE scan_jobs 
SET status = 'cancelled', 
    completed_at = CURRENT_TIMESTAMP,
    error_message = 'Cancelled by user',
    updated_at = CURRENT_TIMESTAMP
WHERE scan_id = 'hubspot-scan-001' 
AND tenant_id = 'tenant-123'
AND status IN ('pending', 'running');

-- Get ETL job statistics for tenant
SELECT 
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
    AVG(success_rate) as avg_success_rate,
    SUM(total_deals) as total_deals_processed
FROM scan_jobs 
WHERE tenant_id = 'tenant-123';
```

---

## 🏢 **Multi-Tenant Data Isolation**

### **Tenant Isolation Strategy**
```sql
-- All queries MUST include tenant_id filter for data isolation
-- Example: Get deals for specific tenant only
SELECT * FROM hubspot_deals WHERE tenant_id = 'tenant-123';

-- Row Level Security (RLS) - Optional advanced approach
ALTER TABLE scan_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hubspot_deals ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (if using RLS)
CREATE POLICY tenant_isolation_scan_jobs ON scan_jobs
    FOR ALL TO application_role
    USING (tenant_id = current_setting('app.current_tenant'));

CREATE POLICY tenant_isolation_deals ON hubspot_deals
    FOR ALL TO application_role
    USING (tenant_id = current_setting('app.current_tenant'));
```

### **Tenant-Specific Operations**
```sql
-- Create ETL job for specific tenant
INSERT INTO scan_jobs (
    scan_id, tenant_id, status, scan_type, config
) VALUES (
    'hubspot-scan-001', 'tenant-123', 'pending', 'hubspot_deals',
    '{"api_token": "pat-xxx", "base_url": "https://api.hubapi.com"}'
);

-- Insert deal data with tenant isolation
INSERT INTO hubspot_deals (
    scan_job_id, tenant_id, _scan_id, _tenant_id, hubspot_deal_id,
    dealname, amount, dealstage, pipeline
) VALUES (
    'job-uuid', 'tenant-123', 'hubspot-scan-001', 'tenant-123', '12345678901',
    'Enterprise Deal', 50000.00, 'qualifiedtobuy', 'default'
);

-- Get tenant-specific analytics
SELECT 
    tenant_id,
    COUNT(*) as total_deals,
    SUM(amount) as total_value,
    AVG(amount) as avg_deal_size,
    COUNT(CASE WHEN dealstage = 'closedwon' THEN 1 END) as won_deals
FROM hubspot_deals 
WHERE tenant_id = 'tenant-123' AND archived = false
GROUP BY tenant_id;
```

---

## 🛠️ Implementation Examples

### Creating a New Scan Job

```sql
-- Create scan job
INSERT INTO scan_jobs (
    id, scan_id, status, scan_type, config, organization_id, batch_size
) VALUES (
    'uuid-1', 'my-scan-001', 'pending', 'user_extraction', 
    '{"auth": {"token": "..."}, "filters": {...}}', 
    'org-123', 100
);
```

### Adding Results (Customize with your fields)

```sql
-- Insert scan results - REPLACE with YOUR field names and values
INSERT INTO [result_table] (
    id, scan_job_id, [your_field_1], [your_field_2], [your_field_3]
) VALUES 
('uuid-3', 'uuid-1', '[value_1]', '[value_2]', '[value_3]'),
('uuid-4', 'uuid-1', '[value_1]', '[value_2]', '[value_3]');

-- Examples for different data types:

-- For user extraction:
-- INSERT INTO user_results (id, scan_job_id, user_id, username, email, department)
-- VALUES ('uuid-3', 'uuid-1', 'user-001', 'john.doe', 'john@example.com', 'Engineering');

-- For project extraction:
-- INSERT INTO project_results (id, scan_job_id, project_id, project_key, project_name, project_type)
-- VALUES ('uuid-3', 'uuid-1', 'proj-001', 'ENG', 'Engineering Project', 'software');

-- For calendar extraction:
-- INSERT INTO calendar_events (id, scan_job_id, event_id, title, organizer_email, start_time)
-- VALUES ('uuid-3', 'uuid-1', 'evt-001', 'Team Meeting', 'manager@example.com', '2024-01-15 10:00:00');

-- Update scan job progress
UPDATE scan_jobs 
SET processed_items = processed_items + 2,
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'uuid-1';
```

### Status Updates

```sql
-- Start scan
UPDATE scan_jobs 
SET status = 'running', 
    started_at = CURRENT_TIMESTAMP 
WHERE scan_id = 'my-scan-001';

-- Complete scan
UPDATE scan_jobs 
SET status = 'completed', 
    completed_at = CURRENT_TIMESTAMP,
    success_rate = CASE 
        WHEN total_items > 0 THEN ROUND(((total_items - failed_items) * 100.0 / total_items), 2)::TEXT || '%'
        ELSE '100%' 
    END
WHERE scan_id = 'my-scan-001';
```

---

## 🔧 Customization Options

### Result Table Naming
Replace `[result_table]` with your preferred name:
- `scan_results` (generic)
- `user_results` (specific to user scans)
- `extraction_results` (for data extraction)
- `calendar_events` (for calendar data)
- `project_data` (for project information)

### Result Table Customization Examples

**Replace `[result_table]` and customize fields for your specific data:**

**1. User/People Data:**
```sql
CREATE TABLE user_results (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    user_id VARCHAR UNIQUE,
    username VARCHAR,
    email VARCHAR,
    display_name VARCHAR,
    department VARCHAR,
    job_title VARCHAR,
    manager_email VARCHAR,
    status VARCHAR, -- active, inactive, suspended
    last_login TIMESTAMP,
    permissions JSON,
    profile_data JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**2. Project/Repository Data:**
```sql  
CREATE TABLE project_results (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    project_id VARCHAR UNIQUE,
    project_key VARCHAR,
    project_name VARCHAR,
    description TEXT,
    project_type VARCHAR, -- software, business, etc.
    lead_email VARCHAR,
    team_members JSON,
    project_status VARCHAR,
    created_date TIMESTAMP,
    last_updated TIMESTAMP,
    settings JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**3. Issue/Ticket Data:**
```sql
CREATE TABLE issue_results (
    id VARCHAR PRIMARY KEY,  
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    issue_id VARCHAR UNIQUE,
    issue_key VARCHAR,
    title VARCHAR,
    description TEXT,
    issue_type VARCHAR,
    priority VARCHAR,
    status VARCHAR,
    assignee_email VARCHAR,
    reporter_email VARCHAR,
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    resolved_date TIMESTAMP,
    labels JSON,
    custom_fields JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**4. Calendar/Event Data:**
```sql
CREATE TABLE calendar_events (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    event_id VARCHAR UNIQUE,
    calendar_id VARCHAR,
    title VARCHAR,
    description TEXT,
    organizer_name VARCHAR,
    organizer_email VARCHAR,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    location VARCHAR,
    is_virtual BOOLEAN,
    meeting_url VARCHAR,
    attendees JSON,
    event_type VARCHAR, -- meeting, appointment, etc.
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**5. Generic/Flexible Data (when structure varies):**
```sql
CREATE TABLE scan_results (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    object_id VARCHAR, -- ID from source system
    object_type VARCHAR, -- user, project, issue, etc.
    object_name VARCHAR, -- Display name
    raw_data JSON NOT NULL, -- Complete API response
    processed_data JSON, -- Cleaned/normalized data
    extraction_metadata JSON, -- Processing info, batch, etc.
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Additional Columns (Optional Customizations)

**For ScanJob Table:**
```sql
-- Add service-specific columns
ALTER TABLE scan_jobs ADD COLUMN service_name VARCHAR(50);
ALTER TABLE scan_jobs ADD COLUMN api_version VARCHAR(20);
ALTER TABLE scan_jobs ADD COLUMN rate_limit_remaining INTEGER;
ALTER TABLE scan_jobs ADD COLUMN priority_level VARCHAR(20) DEFAULT 'normal';
ALTER TABLE scan_jobs ADD COLUMN max_retries INTEGER DEFAULT 3;
```

---

## 📈 Performance Considerations

### Indexing Strategy
- **Primary Operations**: Index on `scan_id`, `status`, and `created_at`
- **Filtering**: Index on `organization_id`, `scan_type`, `result_type`
- **Pagination**: Composite indexes on frequently queried column combinations
- **Foreign Keys**: Always index foreign key columns

### Data Retention
```sql
-- Archive completed scans older than 90 days
CREATE TABLE scan_jobs_archive AS SELECT * FROM scan_jobs WHERE FALSE;

-- Move old data
INSERT INTO scan_jobs_archive 
SELECT * FROM scan_jobs 
WHERE status = 'completed' 
AND completed_at < CURRENT_DATE - INTERVAL '90 days';

-- Clean up
DELETE FROM scan_jobs 
WHERE status = 'completed' 
AND completed_at < CURRENT_DATE - INTERVAL '90 days';
```

### Large Result Sets
```sql
-- Partition result table by scan_job_id for very large datasets
CREATE TABLE [result_table] (
    -- columns as defined above
) PARTITION BY HASH (scan_job_id);

-- Create partitions
CREATE TABLE [result_table]_p0 PARTITION OF [result_table] FOR VALUES WITH (modulus 4, remainder 0);
CREATE TABLE [result_table]_p1 PARTITION OF [result_table] FOR VALUES WITH (modulus 4, remainder 1);
-- etc.
```

---

## 🛡️ Data Integrity

### Constraints
```sql
-- Ensure valid status values
ALTER TABLE scan_jobs ADD CONSTRAINT check_valid_status 
CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));

-- Ensure valid priority levels
ALTER TABLE scan_controls ADD CONSTRAINT check_valid_priority 
CHECK (priority_level IN ('low', 'normal', 'high', 'urgent'));

-- Ensure positive values
ALTER TABLE scan_jobs ADD CONSTRAINT check_positive_counts 
CHECK (total_items >= 0 AND processed_items >= 0 AND failed_items >= 0);
```

### Triggers
```sql
-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_scan_jobs_updated_at 
    BEFORE UPDATE ON scan_jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

### Usage Guidelines

### Best Practices
1. **Use appropriate batch sizes** for your data volume to manage memory and performance
2. **Implement proper error handling** and store error details in `error_message`
3. **Regular cleanup** of old scan jobs and results based on retention policies
4. **Monitor scan progress** using the progress tracking fields (`total_items`, `processed_items`)
5. **Use JSON config** to store flexible scan parameters and authentication details

### Common Patterns
- **Progress Tracking**: Update `processed_items` and `failed_items` as scan progresses
- **Error Recovery**: Store detailed error information in `error_message` field
- **Flexible Configuration**: Use JSON `config` field for scan parameters, auth details, filters
- **Status Management**: Use clear status transitions (pending → running → completed/failed/cancelled)
- **Data Organization**: Use meaningful `scan_id` values for easy identification

---

**Database Schema Version**: 1.0  
**Last Updated**: [Current Date]  
**Compatible With**: PostgreSQL, MySQL, SQLite, SQL Server