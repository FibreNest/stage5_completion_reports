# Automated Reports Generator

This solution provides an automated reporting system that generates CSV reports from a PostgreSQL database and sends them via email using SendGrid. The system runs monthly on the 1st at 8:00 AM and handles monthly, quarterly, and cumulative reports.

## Features

- **Monthly Reports**: Generated on the 1st of every month at 8:00 AM
- **Quarterly Reports**: Automatically generated when a quarter ends
- **Cumulative Reports**: Contains all data from a specified start date (01/08/2025)
- **CSV Export**: Reports are exported in CSV format with helper columns excluded
- **Email Delivery**: Reports are sent via SendGrid API to configured recipients
- **Azure Functions**: Serverless execution with automatic scaling

## Architecture

The solution uses Azure Functions with a timer trigger to automate the reporting process:

```
Azure Function (Timer Trigger)
    ↓
PostgreSQL Database Query
    ↓
Data Processing & CSV Generation
    ↓
SendGrid Email with Attachments
```

## Prerequisites

- Azure subscription
- Azure CLI installed and configured
- PostgreSQL database with the required table structure
- SendGrid account and API key
- Python 3.11+ (for local development)

## Database Table Structure

The solution expects a table with the following columns:
- `id` (PK, integer)
- `ucr` (character varying)
- `company` (character varying)
- `region` (character varying)
- `development` (character varying)
- `plot` (character varying)
- `stage_5_achieved_date` (date)
- `uprn` (character varying)
- `postcode` (character varying)
- `report_month` (date) - automatically set to 1st of month
- `report_quarter` (date) - automatically set to 1st of quarter
- `created_at` (timestamp)
- `updated_at` (timestamp)

## Configuration

### Environment Variables

Configure these environment variables in your Azure Function App settings:

```json
{
  "DB_CONNECTION_STRING": "postgresql://username:password@host:port/database",
      "SENDGRID_BEARER_TOKEN": "your_sendgrid_bearer_token_here",
    "SENDGRID_ENDPOINT": "https://api.sendgrid.com/v3/mail/send",
  "SENDER_EMAIL": "reports@yourcompany.com",
  "RECIPIENT_EMAILS": "email1@domain.com,email2@domain.com",
  "CUMULATIVE_START_DATE": "2025-08-01"
}
```

### Local Development

Copy `local.settings.json.example` to `local.settings.json` and update the values:

```bash
cp local.settings.json.example local.settings.json
```

## Deployment

### Option 1: Automated Script (Recommended)

#### For macOS/Linux:
```bash
# Run the deployment script
./deploy.sh "Your-RG-Name" "West Europe"
```

#### For Windows:
```powershell
# Run the deployment script
.\deploy.ps1 -ResourceGroupName "Your-RG-Name" -Location "West Europe"
```

### Option 2: Azure CLI

```bash
# Create resource group
az group create --name "AutomatedReports-RG" --location "West Europe"

# Deploy using Bicep
az deployment group create \
  --resource-group "AutomatedReports-RG" \
  --template-file "azure-deploy.bicep" \
  --parameters "azure-deploy.parameters.json"
```

### Option 3: Azure Portal

1. Navigate to your resource group
2. Click "Deploy a custom template"
3. Upload the `azure-deploy.bicep` file
4. Fill in the required parameters
5. Deploy

## Function Deployment

After deploying the Azure resources, deploy your function code:

```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Deploy function code
func azure functionapp publish <function-app-name>
```

## Report Logic

### Monthly Reports
- Generated on the 1st of every month at 8:00 AM
- Contains data from the previous month
- Uses `report_month` column for filtering

### Quarterly Reports
- Generated only when a quarter ends (March 31, June 30, September 30, December 31)
- Contains data from the previous quarter
- Uses `report_quarter` column for filtering

### Cumulative Reports
- Generated every month
- Contains all data from the configured start date (default: 01/08/2025)
- Uses `stage_5_achieved_date` column for filtering

## Monitoring

The solution includes Application Insights for monitoring:
- Function execution logs
- Database query performance
- Email delivery status
- Error tracking and alerting

## Customization

### Modify Report Schedule

To change the schedule, update the cron expression in `function_app.py`:

```python
@app.schedule(schedule="0 8 1 * *", arg_name="timer", run_on_startup=False, use_monitor=False)
```

Cron format: `{second} {minute} {hour} {day} {month} {day-of-week}`

### Add New Report Types

To add new report types, create new functions and modify the main function:

```python
def generate_custom_report(conn, custom_criteria):
    # Custom report logic
    pass
```

### Modify Email Templates

Update the email body templates in the `send_email_with_attachment` calls:

```python
custom_body = f"""
<h2>Custom Report</h2>
<p>Your custom content here.</p>
"""
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check connection string format
   - Verify network access and firewall rules
   - Ensure database is running

2. **SendGrid Email Failed**
   - Verify API key is correct
   - Check sender email is verified
   - Review SendGrid account limits

3. **Function Not Triggering**
   - Check timer trigger configuration
   - Verify function app is running
   - Check Application Insights for errors

### Logs

View function logs in Azure Portal:
1. Navigate to your Function App
2. Click on the function name
3. Go to "Monitor" tab
4. View execution logs and details

## Security Considerations

- Store sensitive information in Azure Key Vault
- Use managed identities for database connections
- Implement proper network security groups
- Enable Azure Security Center monitoring

## Cost Optimization

- Use Consumption plan for low-traffic scenarios
- Monitor function execution times
- Set up cost alerts and budgets
- Consider Premium plan for high-frequency execution

## Support

For issues and questions:
1. Check Azure Function logs
2. Review Application Insights
3. Check Azure status page
4. Contact Azure support if needed

## License

This solution is provided as-is for educational and commercial use. 