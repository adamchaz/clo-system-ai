# CLO Management System - Complete API Reference

## 🚀 **API Overview**

The CLO Management System provides a comprehensive REST API for programmatic access to all system functionality. The API follows RESTful principles and uses JSON for data exchange.

**Base URL**: `https://your-domain.com/api/v1`  
**Authentication**: Bearer token (JWT)  
**Content Type**: `application/json`  
**Rate Limiting**: Varies by endpoint (see individual endpoints)

## 🔐 **Authentication**

### **Getting an Access Token**

```http
POST /auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user123",
    "username": "your-username",
    "role": "analyst",
    "permissions": ["read", "write"]
  }
}
```

### **Using the Access Token**

Include the access token in the Authorization header for all API requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📊 **Portfolio Management API**

### **List Portfolios**

```http
GET /portfolios
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Results per page (default: 50, max: 1000)
- `search` (optional): Search term
- `manager` (optional): Filter by portfolio manager
- `status` (optional): Filter by status (active, inactive, liquidating)

**Response:**
```json
{
  "portfolios": [
    {
      "id": "portfolio123",
      "name": "CLO 2024-1A",
      "manager": "Investment Manager LLC",
      "inception_date": "2024-01-15",
      "total_assets": 500000000,
      "currency": "USD",
      "status": "active",
      "performance": {
        "total_return": 0.085,
        "irr": 0.092,
        "moic": 1.12
      }
    }
  ],
  "total_count": 25,
  "page": 1,
  "pages": 1
}
```

### **Get Portfolio Details**

```http
GET /portfolios/{portfolio_id}
```

**Response:**
```json
{
  "id": "portfolio123",
  "name": "CLO 2024-1A", 
  "manager": "Investment Manager LLC",
  "inception_date": "2024-01-15",
  "maturity_date": "2034-01-15",
  "total_assets": 500000000,
  "currency": "USD",
  "status": "active",
  "investment_strategy": "Broadly Syndicated Loans",
  "target_leverage": 10.0,
  "performance": {
    "total_return": 0.085,
    "irr": 0.092,
    "moic": 1.12,
    "sharpe_ratio": 1.15,
    "max_drawdown": 0.025
  },
  "risk_metrics": {
    "duration": 2.8,
    "var_95": 0.032,
    "expected_shortfall": 0.048
  }
}
```

## 🏦 **Asset Management API**

### **List Assets**

```http
GET /assets
```

**Query Parameters:**
- `portfolio_id` (optional): Filter by portfolio
- `asset_type` (optional): Filter by type (loan, bond, security)
- `rating` (optional): Filter by credit rating
- `sector` (optional): Filter by industry sector

**Response:**
```json
{
  "assets": [
    {
      "id": "asset123",
      "cusip": "12345678",
      "issuer": "Example Corp",
      "asset_type": "loan",
      "principal_amount": 5000000,
      "outstanding_amount": 4800000,
      "coupon_rate": 0.075,
      "spread": 0.055,
      "maturity_date": "2029-12-15",
      "rating_sp": "BB+",
      "rating_moodys": "Ba1",
      "sector": "Technology",
      "geography": "United States"
    }
  ],
  "total_count": 384,
  "page": 1,
  "pages": 8
}
```

## 📈 **Analytics API**

### **Waterfall Analysis**

```http
POST /waterfall/analyze
Content-Type: application/json

{
  "portfolio_id": "portfolio123",
  "analysis_date": "2024-06-30",
  "methodology": "MAG17",
  "scenarios": [
    {
      "name": "Base Case",
      "default_rate": 0.02,
      "recovery_rate": 0.70,
      "prepayment_rate": 0.15
    }
  ]
}
```

**Response:**
```json
{
  "analysis_id": "analysis456",
  "status": "completed",
  "results": {
    "total_collections": 125000000,
    "expense_payments": 2500000,
    "senior_interest": 85000000,
    "subordinate_interest": 15000000,
    "senior_principal": 20000000,
    "subordinate_principal": 0,
    "equity_distribution": 2500000,
    "equity_irr": 0.095,
    "equity_moic": 1.18
  }
}
```

### **Risk Analysis**

```http
POST /risk/analyze
Content-Type: application/json

{
  "portfolio_id": "portfolio123", 
  "analysis_type": "var_calculation",
  "confidence_level": 0.95,
  "holding_period_days": 10,
  "simulation_count": 10000
}
```

## 📊 **Reporting API**

### **Generate Report**

```http
POST /reports/generate
Content-Type: application/json

{
  "report_type": "portfolio_performance",
  "portfolio_id": "portfolio123",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "format": "pdf",
  "include_charts": true
}
```

### **Download Report**

```http
GET /reports/{report_id}/download
```

## 🔧 **Monitoring API**

### **System Health**

```http
GET /monitoring/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-07-01T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "api": "healthy",
    "database": "healthy", 
    "cache": "healthy",
    "quantlib": "healthy"
  }
}
```

### **Liveness Probe** (Kubernetes)

```http
GET /monitoring/health/live
```

### **Readiness Probe** (Load Balancers)

```http
GET /monitoring/health/ready
```

## 📝 **Error Handling**

### **HTTP Status Codes**

- `200`: Success
- `201`: Created
- `400`: Bad Request  
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Unprocessable Entity
- `429`: Too Many Requests
- `500`: Internal Server Error

### **Error Response Format**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be processed due to validation errors.",
    "details": [
      {
        "field": "coupon_rate",
        "message": "Coupon rate must be between 0 and 1"
      }
    ],
    "request_id": "req_123456789"
  }
}
```

## 🚦 **Rate Limiting**

API endpoints have different rate limits:

- **Authentication**: 5 requests per minute
- **Read Operations**: 1000 requests per minute
- **Write Operations**: 100 requests per minute  
- **Analysis Operations**: 10 requests per minute
- **Report Generation**: 20 requests per minute

## 🔄 **Pagination**

List endpoints support pagination:

**Request:**
```http
GET /portfolios?page=2&limit=25
```

**Response Headers:**
```
X-Total-Count: 150
X-Page: 2
X-Pages: 6
X-Per-Page: 25
```

---

**Complete API reference with 70+ endpoints for comprehensive CLO portfolio management.**