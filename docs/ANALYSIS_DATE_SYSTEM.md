# Analysis Date System

## Overview

The CLO Management System implements a configurable analysis date system that allows users to perform portfolio analysis as of any specific date. The system defaults to **March 23, 2016** to provide consistent historical analysis baseline.

## Default Analysis Date: March 23, 2016

### Rationale
- **Historical Context**: March 23, 2016 represents a significant period in CLO market history
- **Data Consistency**: All sample portfolio data reflects realistic CLO deals that existed as of this date
- **Calculation Accuracy**: All financial metrics (days to maturity, portfolio age, etc.) are calculated from this baseline
- **User Experience**: Provides a consistent starting point while allowing flexibility for other analysis dates

## Implementation Details

### Backend Configuration

#### Date Utilities (`backend/app/utils/date_utils.py`)
```python
def get_analysis_date(analysis_date_str: Optional[str] = None) -> date:
    """
    Get analysis date - either from parameter or default to March 23, 2016
    """
    if analysis_date_str:
        return datetime.strptime(analysis_date_str, "%Y-%m-%d").date()
    return date(2016, 3, 23)  # Default analysis date: March 23, 2016
```

#### API Endpoints
All major portfolio analysis endpoints support the `analysis_date` parameter:

```bash
# Portfolio listing with analysis date context
GET /api/v1/portfolios/?analysis_date=2016-03-23

# Portfolio summary as of specific date  
GET /api/v1/portfolios/{id}/summary?analysis_date=2016-06-30

# Portfolio assets as of analysis date
GET /api/v1/portfolios/{id}/assets?analysis_date=2016-03-23

# Trigger status as of analysis date
GET /api/v1/portfolios/{id}/triggers?analysis_date=2016-03-23
```

#### Sample Portfolio Data (March 23, 2016 Context)

| Deal ID | Deal Name | Vintage | Status | Days to Maturity | Current Balance |
|---------|-----------|---------|--------|------------------|-----------------|
| CLO2014-001 | Magnetar Capital CLO 2014-1 | 2014 | Revolving | 1,910 days | $385.5M |
| CLO2013-002 | Blackstone Credit CLO 2013-A | 2013 | Amortizing | 1,623 days | $467.2M |
| CLO2015-003 | Apollo Credit CLO 2015-C | 2015 | Revolving | 2,129 days | $328.8M |

### Frontend Implementation

#### Analysis Date Picker Component
**Location**: `frontend/src/components/common/UI/AnalysisDatePicker.tsx`

**Features**:
- Default date: March 23, 2016
- Quick action buttons for relevant 2016-era dates
- Visual status indicators (Default/Historical/Future)
- Reset functionality returns to March 23, 2016

**Quick Actions**:
- **Default**: March 23, 2016 (primary baseline)
- **Today**: Current date (for real-time analysis)
- **2016 Q1 End**: March 31, 2016
- **2016 Q2 End**: June 30, 2016  
- **2016 Q3 End**: September 30, 2016
- **2015 Year End**: December 31, 2015

#### Portfolio List Integration
**Location**: `frontend/src/components/portfolio/PortfolioList.tsx`

- Collapsible analysis date settings panel
- Visual indicators showing current analysis date
- Automatic detection of default vs custom dates
- Contextual messaging about historical vs real-time analysis

## Usage Examples

### API Usage

```bash
# Use default March 23, 2016 analysis date
curl "http://localhost:8000/api/v1/portfolios/"

# Analyze portfolio as of June 30, 2016 (Q2 end)
curl "http://localhost:8000/api/v1/portfolios/CLO2014-001/summary?analysis_date=2016-06-30"

# Get trigger status as of December 31, 2015
curl "http://localhost:8000/api/v1/portfolios/CLO2015-003/triggers?analysis_date=2015-12-31"
```

### Frontend Usage

1. **Default Analysis**: System loads with March 23, 2016 baseline
2. **Date Selection**: Click calendar icon to open date picker
3. **Quick Actions**: Use preset buttons for common analysis dates
4. **Custom Analysis**: Select any date for "what-if" scenarios
5. **Reset**: Return to March 23, 2016 default with reset button

## Date Validation

### Backend Validation
- **Format**: YYYY-MM-DD required
- **Range**: 2010-01-01 to (today + 1 year)
- **Error Handling**: Descriptive error messages for invalid dates

### Frontend Validation  
- **Status Indicators**: Default/Historical/Future visual cues
- **Bounds Checking**: Prevents selection of unreasonable dates
- **User Feedback**: Clear indication of analysis date impact

## Key Benefits

### Historical Consistency
- All sample data reflects realistic 2016 CLO market conditions
- Portfolio lifecycles (revolving/amortizing) appropriate for analysis date
- Days to maturity calculated accurately from March 23, 2016

### User Experience
- Intuitive date picker with relevant quick actions
- Clear visual distinction between default and custom dates
- Consistent baseline eliminates confusion about "current" vs "historical" data

### Analytical Flexibility
- Users can analyze any date period while maintaining consistent baseline
- Support for time-series analysis by changing analysis dates
- Real-time analysis still available by selecting today's date

### System Architecture
- Centralized date logic in utility functions
- Consistent API parameter handling across endpoints
- Clean separation between analysis date and system timestamps

## Migration from Current Date Default

### What Changed
- **Before**: All analysis defaulted to `date.today()`
- **After**: All analysis defaults to `date(2016, 3, 23)`
- **Sample Data**: Updated from 2024 vintages to 2013-2015 vintages
- **UI Components**: Updated to reflect March 23, 2016 as baseline

### Backward Compatibility
- All existing API endpoints continue to work
- Explicit date parameters still override defaults
- Real-time analysis available by passing current date
- No breaking changes to API contracts

## Future Enhancements

### Potential Additions
- **Analysis Date Profiles**: Save frequently used analysis dates
- **Time Series Views**: Compare metrics across multiple analysis dates
- **Date Range Analysis**: Analyze portfolio evolution over date ranges
- **Historical Data Integration**: Link to actual historical CLO data when available

This system provides a robust foundation for historical CLO analysis while maintaining the flexibility to analyze any time period as needed.