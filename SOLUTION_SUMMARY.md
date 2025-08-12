# Solution Summary - Automated Reports Generator

## Overview

This solution provides an automated reporting system that generates CSV reports from a PostgreSQL database and sends them via email using SendGrid. The system is built on Azure Functions with a timer trigger and runs monthly on the 1st at 8:00 AM.


## Key Components

### 1. Timer Trigger Function
- **Schedule**: `0 8 1 * *` (1st of every month at 8:00 AM)
- **Purpose**: Automatically trigger report generation
- **Benefits**: No manual intervention required

### 2. Data Processing Engine
- **Monthly Reports**: Data from previous month using `report_month` column
- **Quarterly Reports**: Data from previous quarter using `report_quarter` column
- **Cumulative Reports**: All data from 01/08/2025 using `stage_5_achieved_date` column

### 3. CSV Generation
- **Format**: Standard CSV with headers
- **Exclusions**: Removes helper columns (`report_month`, `report_quarter`, `created_at`, `updated_at`)
- **Encoding**: UTF-8 for international character support

### 4. Email Delivery System
- **Provider**: SendGrid API
- **Format**: HTML email with CSV attachments
- **Recipients**: Configurable list of email addresses
- **Attachments**: Separate files for each report type

## Report Logic

### Monthly Reports
- **Trigger**: Every month on the 1st at 8:00 AM
- **Data Source**: `report_month` column equals previous month
- **Content**: All records from the previous month
- **Example**: January 1st report contains December data

### Quarterly Reports
- **Trigger**: Only when a quarter ends (March 31, June 30, September 30, December 31)
- **Data Source**: `report_quarter` column within previous quarter range
- **Content**: All records from the previous quarter
- **Example**: April 1st report contains Q1 data (Jan-Mar)

### Cumulative Reports
- **Trigger**: Every month
- **Data Source**: `stage_5_achieved_date` column from 01/08/2025
- **Content**: All records from the start date to current date
- **Purpose**: Provides ongoing total view of all data

## Technical Implementation

### Database Queries
```sql
-- Monthly Report
SELECT id, ucr, company, region, development, plot, 
       stage_5_achieved_date, uprn, postcode
FROM your_table_name
WHERE report_month = %s

-- Quarterly Report
SELECT id, ucr, company, region, development, plot, 
       stage_5_achieved_date, uprn, postcode
FROM your_table_name
WHERE report_quarter >= %s AND report_quarter <= %s

-- Cumulative Report
SELECT id, ucr, company, region, development, plot, 
       stage_5_achieved_date, uprn, postcode
FROM your_table_name
WHERE stage_5_achieved_date >= %s
```

### Date Calculations
- **Quarter Detection**: Automatically determines current quarter and end dates
- **Previous Month**: Calculates first day of previous month
- **Previous Quarter**: Calculates previous quarter start/end dates
- **Quarter End Check**: Determines if current date is quarter end

### Error Handling
- **Database Connection**: Graceful failure with detailed logging
- **Query Execution**: Exception handling for SQL errors
- **CSV Generation**: Validation of data structure
- **Email Delivery**: Retry logic and delivery confirmation

## Configuration

### Environment Variables
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DB_CONNECTION_STRING": "postgresql://xxx:xxx@xxx.com",
    "SENDGRID_BEARER_TOKEN": "xxx",
    "SENDGRID_ENDPOINT": "https://api.sendgrid.com/v3/mail/send",
    "SENDER_EMAIL": "no-reply@fibrenest.com",
    "RECIPIENT_EMAILS": "cristian.nita@fibrenest.com",
    "CUMULATIVE_START_DATE": "2025-08-01"
  }
} 
```

### Customization Options
- **Schedule**: Modify cron expression for different timing
- **Report Types**: Add new report categories
- **Email Templates**: Customize email content and format
- **Data Filters**: Modify query logic for specific requirements

## Monitoring and Observability

### Application Insights
- **Function Execution**: Track success/failure rates
- **Performance Metrics**: Monitor execution times and resource usage
- **Error Tracking**: Detailed error logs and stack traces
- **Custom Metrics**: Business-specific monitoring points

### Logging
- **Structured Logging**: JSON format for easy parsing
- **Log Levels**: Info, Warning, Error for different severity levels
- **Context Information**: Include relevant data in log messages
- **Audit Trail**: Track all report generation activities

## Security Features

### Data Protection
- **Connection Security**: Encrypted database connections
- **API Security**: Secure SendGrid API key storage
- **Access Control**: Azure Function authentication
- **Network Security**: VNet integration support

### Best Practices
- **Secret Management**: Environment variables for sensitive data
- **Input Validation**: Sanitize all database inputs
- **Error Handling**: No sensitive information in error messages
- **Audit Logging**: Track all data access and modifications

## Cost Optimization

### Consumption Plan Benefits
- **Pay-per-execution**: Only pay when function runs
- **Automatic Scaling**: No idle resource costs
- **Built-in Monitoring**: No additional monitoring costs
- **Managed Infrastructure**: No server maintenance costs

### Cost Monitoring
- **Execution Count**: Track monthly function executions
- **Execution Time**: Monitor performance for optimization
- **Resource Usage**: Monitor memory and CPU usage
- **Cost Alerts**: Set up budget notifications