# Solution Summary - Automated Reports Generator

## Overview

This solution provides an automated reporting system that generates CSV reports from a PostgreSQL database and sends them via email using SendGrid. The system is built on Azure Functions with a timer trigger and runs monthly on the 1st at 8:00 AM.

## Why Azure Functions?

**Azure Functions** was chosen over other Azure services for the following reasons:

### Advantages of Azure Functions:
1. **Serverless Architecture**: No infrastructure management required
2. **Cost-Effective**: Pay-per-execution model, ideal for monthly reports
3. **Automatic Scaling**: Handles varying workloads automatically
4. **Built-in Timer Triggers**: Perfect for scheduled monthly execution
5. **Easy Integration**: Seamless integration with other Azure services
6. **Python Support**: Native Python runtime support
7. **Monitoring**: Built-in Application Insights integration

### Comparison with Alternatives:

#### Azure Logic Apps
- **Pros**: Visual designer, extensive connectors
- **Cons**: Higher cost for simple workflows, less control over custom logic
- **Decision**: Not chosen due to cost and complexity for this use case

#### Azure WebJobs
- **Pros**: More control, can run continuously
- **Cons**: Requires App Service, higher cost, manual scaling
- **Decision**: Not chosen due to cost and complexity

#### Azure Container Instances
- **Pros**: Full container control
- **Cons**: Higher cost, manual scheduling, infrastructure management
- **Decision**: Not chosen due to cost and complexity

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Functions                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Timer Trigger (Monthly)                   │   │
│  │           Schedule: 0 8 1 * *                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                               │
│                           ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Report Generator                       │   │
│  │  • Monthly Data Query                              │   │
│  │  • Quarterly Data Query (if quarter ended)         │   │
│  │  • Cumulative Data Query                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                               │
│                           ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              CSV Generator                          │   │
│  │  • Exclude helper columns                          │   │
│  │  • Format data for export                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                               │
│                           ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SendGrid Email                         │   │
│  │  • Monthly Report                                  │   │
│  │  • Quarterly Report (if applicable)                │   │
│  │  • Cumulative Report                               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Database                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Data Table                             │   │
│  │  • report_month: Previous month data               │   │
│  │  • report_quarter: Previous quarter data           │   │
│  │  • stage_5_achieved_date: Cumulative data         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

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
  "DB_CONNECTION_STRING": "PostgreSQL connection string",
  "SENDGRID_API_KEY": "SendGrid API key",
  "SENDER_EMAIL": "Verified sender email",
  "RECIPIENT_EMAILS": "Comma-separated recipient list",
  "CUMULATIVE_START_DATE": "2025-08-01"
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

## Deployment Options

### 1. Automated Deployment (Recommended)
- **PowerShell Script**: `deploy.ps1` for Windows environments
- **Bicep Templates**: Infrastructure as Code approach
- **Azure CLI**: Command-line deployment option
- **CI/CD Pipeline**: GitHub Actions or Azure DevOps

### 2. Manual Deployment
- **Azure Portal**: Web-based deployment
- **Resource Manager**: Template-based deployment
- **Function Core Tools**: Local development and deployment

## Maintenance and Updates

### Regular Tasks
- **Monitor Execution**: Check function logs monthly
- **Update Dependencies**: Keep Python packages current
- **Review Costs**: Monitor Azure spending
- **Backup Configuration**: Export function settings

### Update Process
- **Code Updates**: Deploy new function versions
- **Configuration Changes**: Update environment variables
- **Infrastructure Updates**: Modify Bicep templates
- **Rollback Plan**: Maintain previous versions

## Future Enhancements

### Potential Improvements
- **Multiple Report Formats**: Excel, PDF, JSON support
- **Advanced Filtering**: Date ranges, region filters, company filters
- **Report Templates**: Customizable email and report layouts
- **Data Analytics**: Summary statistics and trends
- **Web Dashboard**: Real-time report viewing interface
- **API Endpoints**: REST API for manual report generation

### Scalability Considerations
- **High Volume**: Premium plan for frequent execution
- **Multiple Databases**: Support for multiple data sources
- **Parallel Processing**: Concurrent report generation
- **Caching**: Redis cache for frequently accessed data

## Conclusion

This Azure Functions-based solution provides a robust, cost-effective, and scalable approach to automated reporting. The serverless architecture eliminates infrastructure management overhead while providing enterprise-grade reliability and monitoring capabilities.

The solution is designed to be:
- **Reliable**: Comprehensive error handling and logging
- **Scalable**: Automatic scaling based on demand
- **Cost-Effective**: Pay-per-execution pricing model
- **Maintainable**: Clear code structure and documentation
- **Secure**: Built-in security features and best practices

By leveraging Azure Functions, the solution provides a production-ready reporting system that can be easily deployed, monitored, and maintained with minimal operational overhead. 