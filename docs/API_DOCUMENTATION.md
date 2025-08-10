# CLO Management System - API Documentation

## 🚀 **PRODUCTION-READY REST API**

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000/api/v1`  
**Documentation**: `http://localhost:8000/docs` (OpenAPI/Swagger)  
**Status**: Phase 2 Complete - All Endpoints Live

## 📋 **API OVERVIEW**

The CLO Management System API provides comprehensive endpoints for managing collateralized loan obligation portfolios, with sophisticated financial calculations, risk analytics, and scenario modeling capabilities.

### **Core API Modules**

1. **Authentication** (`/auth`) - User management and JWT authentication
2. **Assets** (`/assets`) - Asset CRUD operations and correlation analysis  
3. **Portfolios** (`/portfolios`) - CLO deal management and analytics
4. **Waterfall** (`/waterfall`) - Payment calculations and cash flow projections
5. **Risk Analytics** (`/risk`) - VaR calculations and risk metrics
6. **Scenarios** (`/scenarios`) - MAG scenario analysis and custom scenarios
7. **Monitoring** (`/monitoring`) - System health and performance metrics

### **Authentication & Authorization**

All endpoints (except public health checks) require JWT authentication:

```bash
# Get authentication token
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=your_password

# Use token in subsequent requests
Authorization: Bearer <jwt_token>
```

#### **User Roles & Permissions**

- **Admin**: Full system access, user management, system configuration
- **Manager**: Deal management, risk analytics, waterfall calculations  
- **Analyst**: Risk analytics, scenario analysis, deal viewing
- **Viewer**: Read-only access to deals and basic analytics

---

## 🔐 **AUTHENTICATION API** (`/api/v1/auth`)

### **POST /auth/register**
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "secure_password",
  "role": "analyst"
}
```

**Response (201):**
```json
{
  "id": "user_12345",
  "email": "user@example.com", 
  "full_name": "John Doe",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-08-10T10:00:00Z"
}
```

### **POST /auth/token**
Authenticate and receive JWT access token.

**Request Body (form-data):**
```
username: user@example.com
password: secure_password
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user_12345",
    "email": "user@example.com",
    "full_name": "John Doe", 
    "role": "analyst"
  }
}
```

### **GET /auth/me**
Get current user profile information.

**Response (200):**
```json
{
  "id": "user_12345",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-08-10T10:00:00Z",
  "last_login": "2024-08-10T15:30:00Z"
}
```

---

## 📈 **ASSETS API** (`/api/v1/assets`)

### **GET /assets/**
List all assets with pagination and filtering.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100, max: 1000)  
- `asset_type` (string): Filter by asset type
- `rating` (string): Filter by credit rating

**Response (200):**
```json
{
  "assets": [
    {
      "id": "ASSET001",
      "cusip": "12345678",
      "asset_name": "Sample Corp Loan",
      "asset_type": "Senior Loan",
      "current_balance": 5000000.00,
      "original_balance": 5000000.00,
      "coupon_rate": 0.055,
      "maturity_date": "2029-12-15",
      "rating": "BB+",
      "sector": "Technology",
      "industry": "Software",
      "created_at": "2024-08-10T10:00:00Z"
    }
  ],
  "total_count": 384,
  "skip": 0,
  "limit": 100,
  "has_more": true
}
```

### **GET /assets/{asset_id}**
Get detailed information for a specific asset.

**Path Parameters:**
- `asset_id` (string): Asset identifier

**Response (200):**
```json
{
  "id": "ASSET001",
  "cusip": "12345678",
  "isin": "US1234567890",
  "asset_name": "Sample Corp Loan",
  "asset_type": "Senior Loan",
  "current_balance": 5000000.00,
  "original_balance": 5000000.00,
  "coupon_rate": 0.055,
  "maturity_date": "2029-12-15",
  "rating": "BB+",
  "sector": "Technology",
  "industry": "Software",
  "days_to_maturity": 1827,
  "yield_to_maturity": 0.058,
  "duration": 3.2,
  "created_at": "2024-08-10T10:00:00Z",
  "updated_at": "2024-08-10T12:00:00Z"
}
```

### **GET /assets/{asset_id}/correlations**
Get correlation data for a specific asset.

**Path Parameters:**
- `asset_id` (string): Asset identifier

**Query Parameters:**  
- `limit` (int): Maximum correlations to return (default: 50, max: 500)
- `threshold` (float): Minimum correlation threshold (-1.0 to 1.0)

**Response (200):**
```json
[
  {
    "asset_id_1": "ASSET001",
    "asset_id_2": "ASSET002", 
    "correlation": 0.75,
    "last_updated": "2024-08-10T10:00:00Z"
  }
]
```

### **GET /assets/correlations/{asset_id_1}/{asset_id_2}**
Get correlation between two specific assets.

**Response (200):**
```json
{
  "asset_id_1": "ASSET001",
  "asset_id_2": "ASSET002",
  "correlation": 0.75
}
```

### **GET /assets/stats/summary**
Get asset portfolio statistics summary.

**Response (200):**
```json
{
  "total_assets": 384,
  "by_type": {
    "Senior Loan": 245,
    "Second Lien": 89,
    "High Yield Bond": 50
  },
  "by_rating": {
    "BB+": 125,
    "BB": 98,
    "BB-": 87,
    "B+": 74
  },
  "correlations_available": 238144
}
```

---

## 💼 **PORTFOLIOS API** (`/api/v1/portfolios`)

### **GET /portfolios/**
List all CLO deals with pagination.

**Query Parameters:**
- `skip` (int): Records to skip (default: 0)
- `limit` (int): Maximum records (default: 100, max: 500)
- `status` (string): Filter by deal status

**Response (200):**
```json
[
  {
    "id": "DEAL001",
    "deal_name": "Sample CLO 2024-1",
    "manager": "Sample Asset Management",
    "trustee": "Sample Trust Company",
    "effective_date": "2024-01-15",
    "stated_maturity": "2031-01-15", 
    "deal_size": 500000000.00,
    "currency": "USD",
    "status": "effective",
    "current_asset_count": 125,
    "current_portfolio_balance": 485000000.00,
    "created_at": "2024-01-10T10:00:00Z"
  }
]
```

### **GET /portfolios/{deal_id}**
Get detailed information for a specific CLO deal.

**Response (200):**
```json
{
  "id": "DEAL001",
  "deal_name": "Sample CLO 2024-1",
  "manager": "Sample Asset Management",
  "trustee": "Sample Trust Company", 
  "effective_date": "2024-01-15",
  "stated_maturity": "2031-01-15",
  "revolving_period_end": "2026-01-15",
  "reinvestment_period_end": "2025-07-15",
  "deal_size": 500000000.00,
  "currency": "USD",
  "status": "effective",
  "current_asset_count": 125,
  "current_portfolio_balance": 485000000.00,
  "days_to_maturity": 2345,
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-08-10T12:00:00Z"
}
```

### **GET /portfolios/{deal_id}/summary** 
Get comprehensive portfolio summary for a CLO deal.

**Response (200):**
```json
{
  "deal_id": "DEAL001", 
  "total_assets": 125,
  "total_balance": 485000000.00,
  "average_rating": "BB",
  "weighted_average_life": 4.2,
  "sector_diversification": {
    "Technology": 0.15,
    "Healthcare": 0.12,
    "Energy": 0.10,
    "Consumer": 0.08
  },
  "rating_diversification": {
    "BB+": 0.25,
    "BB": 0.30,
    "BB-": 0.25,
    "B+": 0.20
  },
  "average_spread": 425.5,
  "duration": 3.8,
  "top_holdings": [
    {
      "asset_id": "ASSET001",
      "asset_name": "Sample Corp Loan",
      "weight": 0.03,
      "balance": 15000000.00
    }
  ],
  "maturity_profile": {
    "0-2 years": 25,
    "2-4 years": 45, 
    "4-6 years": 35,
    "6+ years": 20
  },
  "current_yield": 0.065,
  "yield_to_maturity": 0.058
}
```

### **GET /portfolios/{deal_id}/tranches**
Get tranche structure for a CLO deal.

**Response (200):**
```json
[
  {
    "id": "TRANCHE_A1",
    "deal_id": "DEAL001",
    "tranche_name": "Class A-1 Notes",
    "tranche_type": "Senior",
    "original_balance": 200000000.00,
    "current_balance": 190000000.00, 
    "coupon_rate": 0.045,
    "spread": 150.0,
    "rating": "AAA",
    "payment_priority": 1,
    "is_floating_rate": true
  }
]
```

### **GET /portfolios/{deal_id}/triggers**
Get OC/IC trigger status for a CLO deal.

**Response (200):**
```json
{
  "oc_triggers": [
    {
      "trigger_type": "OC",
      "tranche_name": "Class A-1",
      "threshold": 1.15,
      "current_value": 1.18,
      "is_passing": true,
      "margin": 0.03,
      "last_tested": "2024-08-10T10:00:00Z"
    }
  ],
  "ic_triggers": [
    {
      "trigger_type": "IC", 
      "tranche_name": "Class A-1",
      "threshold": 1.25,
      "current_value": 1.28,
      "is_passing": true,
      "margin": 0.03,
      "last_tested": "2024-08-10T10:00:00Z"
    }
  ],
  "status": "compliant"
}
```

---

## 💧 **WATERFALL API** (`/api/v1/waterfall`)

### **POST /waterfall/calculate**
Calculate waterfall distribution for a payment period.

**Request Body:**
```json
{
  "deal_id": "DEAL001",
  "payment_date": "2024-08-15",
  "available_funds": 8500000.00,
  "principal_collections": 5000000.00,
  "interest_collections": 3500000.00,
  "scenario_name": "base"
}
```

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "payment_date": "2024-08-15",
  "calculation_timestamp": "2024-08-10T15:30:00Z",
  "total_available_funds": 8500000.00,
  "principal_collections": 5000000.00,
  "interest_collections": 3500000.00,
  "payment_steps": [
    {
      "step_number": 1,
      "description": "Management Fees",
      "payment_type": "fees",
      "target_amount": 187500.00,
      "actual_amount": 187500.00,
      "remaining_funds": 8312500.00,
      "priority": 1
    },
    {
      "step_number": 2, 
      "description": "Class A-1 Interest",
      "payment_type": "interest",
      "target_amount": 712500.00,
      "actual_amount": 712500.00,
      "remaining_funds": 7600000.00,
      "tranche_id": "A1",
      "priority": 3
    }
  ],
  "tranche_payments": {
    "A1": {
      "interest": 712500.00,
      "principal": 2500000.00
    },
    "A2": {
      "interest": 618750.00,
      "principal": 2000000.00
    }
  },
  "total_fees_paid": 212500.00,
  "total_interest_paid": 2850000.00,
  "total_principal_paid": 4500000.00,
  "total_distributions": 7562500.00,
  "remaining_funds": 937500.00,
  "trigger_status": {
    "oc_a1_passing": true,
    "ic_a1_passing": true
  }
}
```

### **POST /waterfall/{deal_id}/cash-flow-projection**
Generate cash flow projections for a CLO deal.

**Request Body:**
```json
{
  "start_date": "2024-08-15",
  "end_date": "2026-08-15", 
  "scenario": "base",
  "assumptions": {
    "default_rate": 0.02,
    "recovery_rate": 0.60,
    "prepayment_rate": 0.15
  },
  "include_monthly_detail": true
}
```

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "scenario": "base", 
  "projection_date": "2024-08-10T15:30:00Z",
  "start_date": "2024-08-15",
  "end_date": "2026-08-15",
  "monthly_projections": [
    {
      "payment_date": "2024-09-15",
      "principal_collections": 5000000.00,
      "interest_collections": 3000000.00,
      "fees_and_expenses": 200000.00,
      "senior_payments": 6500000.00,
      "mezzanine_payments": 1000000.00,
      "subordinate_payments": 200000.00,
      "equity_distribution": 100000.00,
      "ending_balance": 475000000.00
    }
  ],
  "total_collections": 192000000.00,
  "total_distributions": 185000000.00,
  "average_monthly_payment": 7708333.33,
  "final_recovery_rate": 0.98,
  "duration": 4.2,
  "weighted_average_life": 3.8
}
```

### **POST /waterfall/{deal_id}/stress-test**
Run stress testing scenarios on waterfall calculations.

**Request Body:**
```json
{
  "scenarios": [
    {
      "scenario_name": "Mild Stress",
      "description": "Moderate economic downturn",
      "default_rate_shock": 0.03,
      "recovery_rate_shock": -0.10,
      "spread_shock": 200.0
    },
    {
      "scenario_name": "Severe Stress", 
      "description": "Severe economic recession",
      "default_rate_shock": 0.06,
      "recovery_rate_shock": -0.25,
      "spread_shock": 500.0
    }
  ],
  "time_horizon": 12,
  "monte_carlo_runs": 1000
}
```

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "test_date": "2024-08-10T15:30:00Z", 
  "scenarios_tested": 2,
  "monte_carlo_runs": 1000,
  "scenario_results": [
    {
      "scenario": {
        "scenario_name": "Severe Stress",
        "description": "Severe economic recession"
      },
      "portfolio_loss": 15000000.00,
      "loss_percentage": 3.1,
      "tranche_impacts": {
        "A1": 0.00,
        "A2": 0.00, 
        "B": 5000000.00,
        "C": 10000000.00
      },
      "stressed_var": 25000000.00,
      "stressed_volatility": 0.25,
      "time_to_recovery": 18
    }
  ],
  "worst_case_loss": 15000000.00,
  "best_case_loss": 5000000.00, 
  "median_loss": 8500000.00,
  "scenario_rankings": ["Severe Stress", "Mild Stress"],
  "critical_scenarios": ["Severe Stress"]
}
```

---

## 📊 **RISK ANALYTICS API** (`/api/v1/risk`)

### **GET /risk/{deal_id}/metrics**
Get comprehensive risk metrics for a CLO deal.

**Query Parameters:**
- `as_of_date` (string): As-of date for calculations (ISO format)

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "as_of_date": "2024-08-10",
  "calculation_timestamp": "2024-08-10T15:30:00Z",
  "portfolio_volatility": 0.18,
  "tracking_error": 0.02,
  "sector_concentration": {
    "Technology": 0.15,
    "Healthcare": 0.12,
    "Energy": 0.10
  },
  "rating_concentration": {
    "BB+": 0.25,
    "BB": 0.30,
    "BB-": 0.25
  },
  "single_asset_max_weight": 0.035,
  "herfindahl_index": 0.08,
  "value_at_risk_95": 12500000.00,
  "value_at_risk_99": 22500000.00, 
  "expected_shortfall": 17500000.00,
  "modified_duration": 3.2,
  "effective_duration": 3.1,
  "convexity": 12.5,
  "average_rating_score": 12.5,
  "weighted_average_rating": "BB",
  "default_probability": 0.025,
  "interest_rate_sensitivity": -0.032,
  "credit_spread_sensitivity": -0.018,
  "overall_risk_level": "medium",
  "risk_factors": [
    "High sector concentration",
    "Credit spread exposure"
  ]
}
```

### **GET /risk/{deal_id}/correlation-matrix**
Get correlation matrix for assets in a CLO deal.

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "asset_count": 125,
  "correlation_matrix": [
    [1.0, 0.75, 0.32],
    [0.75, 1.0, 0.45], 
    [0.32, 0.45, 1.0]
  ],
  "asset_ids": ["ASSET001", "ASSET002", "ASSET003"],
  "eigenvalues": [2.15, 0.65, 0.20],
  "condition_number": 10.75,
  "average_correlation": 0.51,
  "max_correlation": 0.85,
  "min_correlation": 0.15
}
```

### **GET /risk/{deal_id}/concentration**
Analyze portfolio concentration by various dimensions.

**Query Parameters:**
- `dimension` (string): Concentration dimension (sector, industry, rating, geography)

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "dimension": "sector",
  "analysis_date": "2024-08-10",
  "concentrations": {
    "Technology": 0.15,
    "Healthcare": 0.12,
    "Energy": 0.10,
    "Consumer": 0.08,
    "Financial Services": 0.07
  },
  "concentration_ratio_top5": 0.52,
  "concentration_ratio_top10": 0.78,
  "concentration_risk_score": 52.0,
  "over_concentrated_segments": ["Technology"],
  "effective_number_of_positions": 12.5,
  "diversification_ratio": 0.85,
  "recommended_limits": {
    "Technology": 0.08
  }
}
```

### **POST /risk/{deal_id}/stress-test**
Run comprehensive stress testing on a portfolio.

**Request Body:**
```json
{
  "scenarios": [
    {
      "scenario_name": "Economic Downturn",
      "description": "GDP decline with increased defaults",
      "default_rate_shock": 0.04,
      "recovery_rate_shock": -0.15,
      "correlation_shock": 0.10
    }
  ],
  "time_horizon": 12,
  "monte_carlo_runs": 5000,
  "include_correlation_breakdown": true
}
```

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "test_date": "2024-08-10T15:30:00Z",
  "scenarios_tested": 1,
  "monte_carlo_runs": 5000,
  "scenario_results": [
    {
      "scenario": {
        "scenario_name": "Economic Downturn",
        "description": "GDP decline with increased defaults"
      },
      "portfolio_loss": 18500000.00,
      "loss_percentage": 3.8,
      "tranche_impacts": {
        "A1": 0.00,
        "A2": 0.00,
        "B": 8500000.00,
        "C": 10000000.00
      },
      "stressed_var": 28000000.00,
      "stressed_volatility": 0.28,
      "time_to_recovery": 24,
      "worst_performing_assets": [
        {
          "asset_id": "ASSET123", 
          "loss_percentage": 15.2
        }
      ],
      "sector_impacts": {
        "Energy": -8.5,
        "Consumer": -6.2,
        "Technology": -4.1
      }
    }
  ],
  "worst_case_loss": 18500000.00,
  "best_case_loss": 18500000.00,
  "median_loss": 18500000.00,
  "scenario_rankings": ["Economic Downturn"],
  "critical_scenarios": ["Economic Downturn"]
}
```

### **GET /risk/{deal_id}/var**
Calculate Value at Risk for a portfolio.

**Query Parameters:**
- `confidence_level` (float): Confidence level (0.5-0.99, default: 0.95)
- `time_horizon_days` (int): Time horizon in days (1-365, default: 30)  
- `method` (string): Calculation method (parametric, historical, monte_carlo)

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "confidence_level": 0.95,
  "time_horizon_days": 30,
  "method": "monte_carlo",
  "var_amount": 12500000.00,
  "var_percentage": 2.5,
  "expected_shortfall": 17500000.00,
  "portfolio_value": 500000000.00,
  "calculation_details": {
    "simulations": 10000,
    "distribution": "normal"
  },
  "assumptions": [
    "Normal distribution",
    "Constant volatility"
  ]
}
```

---

## 🎯 **SCENARIOS API** (`/api/v1/scenarios`)

### **GET /scenarios/**
List available scenarios (MAG and custom).

**Query Parameters:**
- `scenario_type` (string): Filter by type (MAG, custom, regulatory)
- `active_only` (boolean): Return only active scenarios (default: true)

**Response (200):**
```json
[
  {
    "id": "Mag 6",
    "name": "Mag 6",
    "scenario_type": "MAG", 
    "description": "MAG 6 scenario parameters",
    "is_active": true,
    "created_date": null,
    "parameter_count": 1985,
    "last_used": "2024-08-09T14:20:00Z",
    "usage_count": 15
  },
  {
    "id": "SCEN_Custom_20240810153045",
    "name": "Stress Test Q3 2024",
    "scenario_type": "custom",
    "description": "Q3 2024 stress testing scenario",
    "is_active": true,
    "created_date": "2024-08-10T15:30:45Z",
    "parameter_count": 25,
    "usage_count": 3
  }
]
```

### **GET /scenarios/{scenario_id}**
Get detailed information for a specific scenario.

**Response (200):**
```json
{
  "id": "Mag 6",
  "name": "Mag 6",
  "scenario_type": "MAG",
  "description": "MAG 6 scenario parameters for CLO analysis",
  "is_active": true,
  "parameter_count": 1985,
  "created_date": null,
  "last_used": "2024-08-09T14:20:00Z",
  "usage_count": 15
}
```

### **GET /scenarios/{scenario_id}/parameters**
Get parameters for a specific scenario.

**Query Parameters:**
- `category` (string): Filter by parameter category

**Response (200):**
```json
{
  "scenario_id": "Mag 6",
  "parameter_count": 1985,
  "parameters": [
    {
      "parameter_name": "GDP_Growth_Rate",
      "category": "Economic",
      "value": 0.025,
      "unit": "percentage",
      "description": "Annual GDP growth rate",
      "source": "Federal Reserve"
    },
    {
      "parameter_name": "Corporate_Default_Rate",
      "category": "Credit",
      "value": 0.035,
      "unit": "percentage", 
      "description": "Annual corporate default rate"
    }
  ],
  "parameters_by_category": {
    "Economic": [
      {
        "parameter_name": "GDP_Growth_Rate",
        "value": 0.025,
        "unit": "percentage"
      }
    ],
    "Credit": [
      {
        "parameter_name": "Corporate_Default_Rate", 
        "value": 0.035,
        "unit": "percentage"
      }
    ]
  }
}
```

### **POST /scenarios/**
Create a new custom scenario.

**Request Body:**
```json
{
  "name": "Custom Stress Q4 2024",
  "description": "Custom stress testing scenario for Q4 2024",
  "scenario_type": "custom",
  "parameters": {
    "Economic": {
      "gdp_growth": -0.015,
      "inflation_rate": 0.045
    },
    "Credit": {
      "default_rate": 0.055,
      "recovery_rate": 0.45
    },
    "Market": {
      "credit_spreads": 650.0,
      "volatility": 0.25
    }
  }
}
```

**Response (201):**
```json
{
  "id": "SCEN_Custom_20240810154512",
  "name": "Custom Stress Q4 2024",
  "description": "Custom stress testing scenario for Q4 2024",
  "scenario_type": "custom",
  "created_date": "2024-08-10T15:45:12Z",
  "is_active": true,
  "parameter_count": 6
}
```

### **POST /scenarios/{scenario_id}/analyze**
Run comprehensive scenario analysis.

**Request Body:**
```json
{
  "deal_ids": ["DEAL001", "DEAL002"],
  "analysis_type": "comprehensive",
  "time_horizon": 24,
  "include_stress_testing": true,
  "include_correlation_analysis": true,
  "include_waterfall_impact": true,
  "custom_parameters": {
    "override_default_rate": 0.04
  }
}
```

**Response (200):**
```json
{
  "scenario_id": "Mag 6",
  "analysis_date": "2024-08-10T15:30:00Z",
  "deals_analyzed": ["DEAL001", "DEAL002"],
  "analysis_type": "comprehensive",
  "portfolio_impacts": [
    {
      "deal_id": "DEAL001",
      "base_portfolio_value": 500000000.00,
      "scenario_portfolio_value": 475000000.00,
      "value_change": -25000000.00,
      "value_change_percentage": -5.0,
      "sector_impacts": {
        "Technology": -2.5,
        "Healthcare": -1.2
      },
      "rating_impacts": {
        "BBB": -1.8,
        "BB": -3.2
      }
    }
  ],
  "total_portfolio_impact": -35000000.00,
  "weighted_average_impact": -4.2,
  "risk_metrics": {
    "portfolio_volatility": 22.5,
    "value_at_risk": 45000000.00,
    "expected_shortfall": 62000000.00,
    "maximum_drawdown": 55000000.00
  },
  "cash_flow_impacts": [
    {
      "deal_id": "DEAL001",
      "base_cash_flows": 8000000.00,
      "scenario_cash_flows": 7200000.00,
      "impact_percentage": -10.0
    }
  ],
  "waterfall_impacts": [
    {
      "deal_id": "DEAL001", 
      "senior_impact": 0.0,
      "mezzanine_impact": -5.2,
      "subordinate_impact": -15.8,
      "equity_impact": -35.0
    }
  ],
  "key_findings": [
    "Scenario shows significant negative portfolio impact",
    "High volatility observed under scenario conditions"
  ],
  "risk_warnings": [
    "Potential for significant portfolio losses under this scenario"
  ],
  "recommendations": [
    "Consider hedging strategies to mitigate scenario risk",
    "Review portfolio diversification"
  ]
}
```

### **POST /scenarios/compare**
Compare multiple scenarios for a deal.

**Query Parameters:**
- `scenario_ids` (array): List of scenario IDs to compare (2-5 scenarios)
- `deal_id` (string): Deal to analyze
- `metrics` (array): Metrics to compare (portfolio_value, risk_metrics, cash_flows)

**Response (200):**
```json
{
  "deal_id": "DEAL001",
  "scenarios_compared": ["Mag 6", "Mag 7", "Custom_Stress"],
  "metrics": ["portfolio_value", "risk_metrics"],
  "metric_comparisons": {
    "portfolio_value": {
      "Mag 6": -25000000.00,
      "Mag 7": -18000000.00, 
      "Custom_Stress": -35000000.00
    },
    "risk_metrics": {
      "Mag 6": 22.5,
      "Mag 7": 19.8,
      "Custom_Stress": 28.2
    }
  },
  "scenario_rankings": {
    "portfolio_value": ["Mag 7", "Mag 6", "Custom_Stress"],
    "risk_metrics": ["Mag 7", "Mag 6", "Custom_Stress"]
  },
  "summary": {
    "best_scenario": "Mag 7",
    "worst_scenario": "Custom_Stress",
    "recommendation": "Mag 7 scenario shows most favorable outcomes"
  }
}
```

---

## 🖥️ **MONITORING API** (`/api/v1/monitoring`)

### **GET /monitoring/health**
Get comprehensive system health status.

**Response (200):**
```json
{
  "overall_status": "healthy",
  "uptime_seconds": 86400,
  "uptime_human": "1d 0h 0m",
  "last_restart": "2024-08-09T10:00:00Z",
  "services": [
    {
      "service_name": "PostgreSQL",
      "status": "healthy",
      "response_time_ms": 15.2,
      "last_checked": "2024-08-10T15:30:00Z",
      "error_message": null
    },
    {
      "service_name": "Redis",
      "status": "healthy", 
      "response_time_ms": 2.1,
      "last_checked": "2024-08-10T15:30:00Z",
      "error_message": null
    }
  ],
  "cpu_usage_percent": 35.2,
  "memory_usage_percent": 68.5,
  "disk_usage_percent": 42.1,
  "postgresql_status": "healthy",
  "redis_status": "healthy",
  "migration_databases_status": {
    "assets": true,
    "correlations": true,
    "scenarios": true,
    "config": true,
    "reference": true
  },
  "healthy_services": 7,
  "total_services": 7,
  "active_alerts": 0
}
```

### **GET /monitoring/metrics/performance**
Get system performance metrics.

**Query Parameters:**
- `time_range` (string): Time range (5m, 15m, 1h, 6h, 24h, 7d)

**Response (200):**
```json
{
  "time_range": "1h",
  "metrics": [
    {
      "timestamp": "2024-08-10T15:30:00Z",
      "cpu_percent": 35.2,
      "memory_percent": 68.5,
      "disk_io_read": 5420,
      "disk_io_write": 2150,
      "network_io_sent": 25600,
      "network_io_received": 45200,
      "active_connections": 12,
      "request_rate": 15.3,
      "response_time_avg": 125.7
    }
  ],
  "avg_cpu_percent": 33.8,
  "max_cpu_percent": 42.5,
  "avg_memory_percent": 66.2,
  "max_memory_percent": 71.5,
  "avg_response_time": 132.4,
  "total_requests": 1847,
  "cpu_trend": "stable",
  "memory_trend": "increasing",
  "response_time_trend": "stable"
}
```

### **GET /monitoring/alerts**
Get system alerts and notifications.

**Query Parameters:**
- `severity` (string): Filter by severity (low, medium, high, critical)
- `active_only` (boolean): Return only active alerts (default: true)
- `limit` (int): Maximum alerts to return (default: 100, max: 1000)

**Response (200):**
```json
[
  {
    "id": "alert_12345",
    "title": "High Memory Usage",
    "message": "Memory usage has exceeded 80% for 10 minutes",
    "severity": "medium",
    "component": "system",
    "alert_type": "system",
    "is_active": true,
    "is_acknowledged": false,
    "created_at": "2024-08-10T15:20:00Z",
    "occurrence_count": 1,
    "last_occurrence": "2024-08-10T15:20:00Z",
    "created_by": "system"
  }
]
```

### **GET /monitoring/logs/application**
Get application logs.

**Query Parameters:**
- `level` (string): Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `start_time` (datetime): Start time for log retrieval
- `end_time` (datetime): End time for log retrieval
- `limit` (int): Maximum logs to return (default: 100, max: 1000)

**Response (200):**
```json
{
  "logs": [
    {
      "timestamp": "2024-08-10T15:30:00Z",
      "level": "INFO",
      "logger_name": "clo.waterfall",
      "message": "Waterfall calculation completed for DEAL001",
      "module": "waterfall_service.py",
      "function": "calculate_waterfall",
      "line_number": 125,
      "thread_id": "thread-1",
      "process_id": 12345,
      "user_id": "user_123",
      "request_id": "req_456"
    }
  ],
  "total_count": 1,
  "filters": {
    "level": null,
    "start_time": null,
    "end_time": null
  }
}
```

---

## 🔧 **ERROR HANDLING**

All API endpoints follow consistent error response patterns:

### **Standard Error Response**
```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2024-08-10T15:30:00Z",
  "path": "/api/v1/assets/invalid_id",
  "request_id": "req_12345"
}
```

### **Common HTTP Status Codes**
- **200**: Success
- **201**: Created  
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **422**: Unprocessable Entity (validation errors)
- **500**: Internal Server Error

### **Validation Error Response**
```json
{
  "detail": [
    {
      "loc": ["body", "deal_id"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "available_funds"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

## 📈 **RATE LIMITING & PERFORMANCE**

### **Rate Limits**
- **Standard endpoints**: 100 requests/minute per user
- **Calculation endpoints**: 20 requests/minute per user  
- **Authentication endpoints**: 10 requests/minute per IP

### **Response Times (Production)**
- **Simple queries**: < 100ms
- **Waterfall calculations**: < 2 seconds
- **Risk analytics**: < 5 seconds
- **Scenario analysis**: < 10 seconds

### **Caching**
- **Asset data**: 1 hour TTL
- **Correlation matrix**: 2 hours TTL
- **Scenario parameters**: 4 hours TTL
- **User sessions**: 24 hours TTL

---

## 🚀 **GETTING STARTED**

### **1. Authentication Flow**
```python
import requests

# Get authentication token
auth_response = requests.post("http://localhost:8000/api/v1/auth/token", 
                             data={
                                 "username": "user@example.com",
                                 "password": "password"
                             })
token = auth_response.json()["access_token"]

# Use token in subsequent requests
headers = {"Authorization": f"Bearer {token}"}

# Get asset list
assets_response = requests.get("http://localhost:8000/api/v1/assets/", 
                              headers=headers)
assets = assets_response.json()
```

### **2. Calculate Waterfall**
```python
# Calculate waterfall for a deal
waterfall_request = {
    "deal_id": "DEAL001",
    "payment_date": "2024-08-15",
    "available_funds": 8500000.00,
    "principal_collections": 5000000.00,
    "interest_collections": 3500000.00
}

waterfall_response = requests.post(
    "http://localhost:8000/api/v1/waterfall/calculate",
    json=waterfall_request,
    headers=headers
)
results = waterfall_response.json()
```

### **3. Risk Analysis**
```python
# Get risk metrics for a portfolio
risk_response = requests.get(
    "http://localhost:8000/api/v1/risk/DEAL001/metrics?as_of_date=2024-08-10",
    headers=headers
)
risk_metrics = risk_response.json()

# Run stress testing
stress_test_request = {
    "scenarios": [{
        "scenario_name": "Economic Downturn",
        "default_rate_shock": 0.04,
        "recovery_rate_shock": -0.15
    }],
    "monte_carlo_runs": 5000
}

stress_response = requests.post(
    "http://localhost:8000/api/v1/risk/DEAL001/stress-test",
    json=stress_test_request,
    headers=headers  
)
stress_results = stress_response.json()
```

---

## 📚 **ADDITIONAL RESOURCES**

- **Interactive API Documentation**: `http://localhost:8000/docs`
- **OpenAPI Specification**: `http://localhost:8000/openapi.json`
- **System Health Dashboard**: `http://localhost:8000/api/v1/monitoring/health`
- **GitHub Repository**: [CLO Management System](https://github.com/your-org/clo-management-system)
- **Technical Documentation**: `/docs` folder in repository

---

## 🆘 **SUPPORT & TROUBLESHOOTING**

### **Common Issues**

1. **Authentication Errors**
   - Ensure JWT token is included in Authorization header
   - Check token expiration (30 minutes default)
   - Verify user permissions for endpoint

2. **Validation Errors**  
   - Review request body against schema documentation
   - Check required fields and data types
   - Ensure numeric values are within valid ranges

3. **Performance Issues**
   - Use pagination for large result sets
   - Consider caching frequently accessed data
   - Monitor rate limits and adjust request frequency

### **Getting Help**
- Create GitHub issues for bug reports
- Use discussion forums for questions
- Contact support team for critical issues

---

**Last Updated**: August 10, 2024  
**API Version**: 1.0.0  
**Status**: Production Ready