import azure.functions as func
import logging
import os
import json
from datetime import datetime, date
from typing import List, Dict, Any
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import base64
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = func.FunctionApp()

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(os.getenv('DB_CONNECTION_STRING'))
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        raise

def get_quarter_dates(current_date: date) -> tuple:
    """Calculate quarter start and end dates for the given date."""
    year = current_date.year
    month = current_date.month
    
    if month in [1, 2, 3]:
        quarter_start = date(year, 1, 1)
        quarter_end = date(year, 3, 31)
        quarter_num = 1
    elif month in [4, 5, 6]:
        quarter_start = date(year, 4, 1)
        quarter_end = date(year, 6, 30)
        quarter_num = 2
    elif month in [7, 8, 9]:
        quarter_start = date(year, 7, 1)
        quarter_end = date(year, 9, 30)
        quarter_num = 3
    else:
        quarter_start = date(year, 10, 1)
        quarter_end = date(year, 12, 31)
        quarter_num = 4
    
    return quarter_start, quarter_end, quarter_num

def is_quarter_end(current_date: date) -> bool:
    """Check if the current date is the end of a quarter."""
    quarter_start, quarter_end, _ = get_quarter_dates(current_date)
    return current_date == quarter_end

def get_previous_month_date(current_date: date) -> date:
    """Get the first day of the previous month."""
    if current_date.month == 1:
        return date(current_date.year - 1, 12, 1)
    else:
        return date(current_date.year, current_date.month - 1, 1)

def get_previous_quarter_dates(current_date: date) -> tuple:
    """Get the start and end dates of the previous quarter."""
    quarter_start, quarter_end, quarter_num = get_quarter_dates(current_date)
    
    if quarter_num == 1:
        prev_quarter_start = date(current_date.year - 1, 10, 1)
        prev_quarter_end = date(current_date.year - 1, 12, 31)
    else:
        if quarter_num == 2:
            prev_quarter_start = date(current_date.year, 1, 1)
            prev_quarter_end = date(current_date.year, 3, 31)
        elif quarter_num == 3:
            prev_quarter_start = date(current_date.year, 4, 1)
            prev_quarter_end = date(current_date.year, 6, 30)
        else:  # quarter_num == 4
            prev_quarter_start = date(current_date.year, 7, 1)
            prev_quarter_end = date(current_date.year, 9, 30)
    
    return prev_quarter_start, prev_quarter_end

def fetch_data_from_db(conn, query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """Fetch data from database using the given query."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Database query failed: {str(e)}")
        raise

def create_csv_report(data: List[Dict[str, Any]], filename: str) -> bytes:
    """Create a CSV report from the data."""
    try:
        # Convert to DataFrame and exclude helper columns
        df = pd.DataFrame(data)
        columns_to_exclude = ['report_month', 'report_quarter', 'created_at', 'updated_at']
        
        # Only exclude columns if they exist in the DataFrame
        existing_columns = [col for col in columns_to_exclude if col in df.columns]
        if existing_columns:
            df = df.drop(columns=existing_columns)
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode('utf-8')
    except Exception as e:
        logging.error(f"CSV creation failed: {str(e)}")
        raise

def send_email_with_attachment(
    subject: str,
    body: str,
    attachment_data: bytes,
    attachment_filename: str,
    recipient_emails: List[str]
) -> bool:
    """Send email with attachment using SendGrid HTTP API."""
    try:
        # Get configuration
        bearer_token = os.getenv('SENDGRID_BEARER_TOKEN')
        sendgrid_endpoint = os.getenv('SENDGRID_ENDPOINT')
        sender_email = os.getenv('SENDER_EMAIL')
        
        if not all([bearer_token, sendgrid_endpoint, sender_email]):
            raise ValueError("Missing SendGrid configuration: SENDGRID_BEARER_TOKEN, SENDGRID_ENDPOINT, or SENDER_EMAIL")
        
        # Prepare email payload
        email_payload = {
            "personalizations": [
                {
                    "to": [{"email": email.strip()} for email in recipient_emails]
                }
            ],
            "from": {"email": sender_email},
            "subject": subject,
            "content": [
                {
                    "type": "text/html",
                    "value": body
                }
            ],
            "attachments": [
                {
                    "content": base64.b64encode(attachment_data).decode('utf-8'),
                    "type": "text/csv",
                    "filename": attachment_filename,
                    "disposition": "attachment"
                }
            ]
        }
        
        # Send email via HTTP API
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            sendgrid_endpoint,
            json=email_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 202]:
            logging.info(f"Email sent successfully. Status code: {response.status_code}")
            return True
        else:
            logging.error(f"Email sending failed. Status code: {response.status_code}, Response: {response.text}")
            return False
        
    except Exception as e:
        logging.error(f"Email sending failed: {str(e)}")
        return False

def send_email_with_multiple_attachments(
    subject: str,
    body: str,
    attachments: List[Dict[str, Any]],
    recipient_emails: List[str]
) -> bool:
    """Send email with multiple attachments using SendGrid HTTP API."""
    try:
        # Get configuration
        bearer_token = os.getenv('SENDGRID_BEARER_TOKEN')
        sendgrid_endpoint = os.getenv('SENDGRID_ENDPOINT')
        sender_email = os.getenv('SENDER_EMAIL')
        
        if not all([bearer_token, sendgrid_endpoint, sender_email]):
            raise ValueError("Missing SendGrid configuration: SENDGRID_BEARER_TOKEN, SENDGRID_ENDPOINT, or SENDER_EMAIL")
        
        # Prepare attachments
        email_attachments = []
        for attachment in attachments:
            email_attachments.append({
                "content": base64.b64encode(attachment['data']).decode('utf-8'),
                "type": "text/csv",
                "filename": attachment['filename'],
                "disposition": "attachment"
            })
        
        # Prepare email payload
        email_payload = {
            "personalizations": [
                {
                    "to": [{"email": email.strip()} for email in recipient_emails]
                }
            ],
            "from": {"email": sender_email},
            "subject": subject,
            "content": [
                {
                    "type": "text/html",
                    "value": body
                }
            ],
            "attachments": email_attachments
        }
        
        # Send email via HTTP API
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            sendgrid_endpoint,
            json=email_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 202]:
            logging.info(f"Email with {len(attachments)} attachments sent successfully. Status code: {response.status_code}")
            return True
        else:
            logging.error(f"Email sending failed. Status code: {response.status_code}, Response: {response.text}")
            return False
        
    except Exception as e:
        logging.error(f"Email sending failed: {str(e)}")
        return False

def generate_reports_on_demand(current_date: date = None) -> dict:
    """
    Generate reports for a specific date or current date.
    This function can be called by both timer and HTTP triggers.
    """
    if current_date is None:
        current_date = date.today()
    
    logging.info(f'Report generation started for date: {current_date}.')
    
    try:
        previous_month = get_previous_month_date(current_date)
        is_quarter_end_date = is_quarter_end(current_date)
        
        # Get database connection
        conn = get_db_connection()
        
        # Fetch monthly data (previous month)
        monthly_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE report_month = %s
        """
        monthly_data = fetch_data_from_db(conn, monthly_query, (previous_month,))
        
        # Fetch cumulative data (from 01/08)
        cumulative_start_date = datetime.strptime(os.getenv('CUMULATIVE_START_DATE'), '%Y-%m-%d').date()
        cumulative_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE stage_5_achieved_date >= %s
        """
        cumulative_data = fetch_data_from_db(conn, cumulative_query, (cumulative_start_date,))
        
        # Prepare email content
        recipient_emails = os.getenv('RECIPIENT_EMAILS').split(',')
        
        # Prepare all reports for single email
        all_reports = []
        email_body = f"""
        <h2>Stage 5 Completion Reports - {current_date.strftime('%B %d, %Y')}</h2>
        <p>Please find attached the following reports generated on {current_date.strftime('%Y-%m-%d')}:</p>
        <ul>
        """
        
        # Monthly report
        if monthly_data:
            monthly_csv = create_csv_report(monthly_data, f"monthly_report_{previous_month.strftime('%Y_%m')}.csv")
            monthly_filename = f"monthly_report_{previous_month.strftime('%Y_%m')}.csv"
            
            all_reports.append({
                'data': monthly_csv,
                'filename': monthly_filename
            })
            
            email_body += f"<li><strong>Monthly Report - {previous_month.strftime('%B %Y')}</strong>: {len(monthly_data)} records</li>"
        
        # Cumulative report
        if cumulative_data:
            cumulative_csv = create_csv_report(cumulative_data, f"cumulative_report_{current_date.strftime('%Y_%m')}.csv")
            cumulative_filename = f"cumulative_report_{current_date.strftime('%Y_%m')}.csv"
            
            all_reports.append({
                'data': cumulative_csv,
                'filename': cumulative_filename
            })
            
            email_body += f"<li><strong>Cumulative Report</strong> - <strong>Since 1st of August 2025</strong>: {len(cumulative_data)} records</li>"
        
        # Quarterly report (if quarter has ended)
        if is_quarter_end_date:
            previous_quarter_start, previous_quarter_end = get_previous_quarter_dates(current_date)
            
            quarterly_query = """
                SELECT id, ucr, company, region, development, plot, 
                       stage_5_achieved_date, uprn, postcode
                FROM public.stage_5_plots
                WHERE report_quarter >= %s AND report_quarter <= %s
            """
            quarterly_data = fetch_data_from_db(conn, quarterly_query, (previous_quarter_start, previous_quarter_end))
            
            if quarterly_data:
                quarterly_csv = create_csv_report(quarterly_data, f"quarterly_report_{previous_quarter_start.strftime('%Y')}_Q{get_quarter_dates(previous_quarter_start)[2]}.csv")
                quarterly_filename = f"quarterly_report_{previous_quarter_start.strftime('%Y')}_Q{get_quarter_dates(previous_quarter_start)[2]}.csv"
                
                all_reports.append({
                    'data': quarterly_csv,
                    'filename': quarterly_filename
                })
                
                email_body += f"<li><strong>Quarterly Report - Q{get_quarter_dates(previous_quarter_start)[2]} {previous_quarter_start.strftime('%Y')}</strong>: {len(quarterly_data)} records ({previous_quarter_start.strftime('%Y-%m-%d')} to {previous_quarter_end.strftime('%Y-%m-%d')})</li>"
        
        email_body += """
        </ul>
        """
        
        # Send single email with all reports
        if all_reports:
            subject = f"Stage 5 Completion Reports - {current_date.strftime('%B %d, %Y')}"
            
            success = send_email_with_multiple_attachments(
                subject,
                email_body,
                all_reports,
                recipient_emails
            )
            
            if success:
                logging.info(f'Reports generated and sent successfully for {current_date}.')
                result = {
                    'success': True,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'reports_generated': len(all_reports),
                    'monthly_records': len(monthly_data) if monthly_data else 0,
                    'quarterly_records': len(quarterly_data) if 'quarterly_data' in locals() and quarterly_data else 0,
                    'cumulative_records': len(cumulative_data) if cumulative_data else 0,
                    'message': f'Successfully generated {len(all_reports)} reports for {current_date.strftime("%B %d, %Y")}'
                }
            else:
                result = {
                    'success': False,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'error': 'Failed to send email'
                }
        else:
            result = {
                'success': False,
                'date': current_date.strftime('%Y-%m-%d'),
                'error': 'No reports generated - no data found'
            }
        
        conn.close()
        return result
        
    except Exception as e:
        logging.error(f'Report generation failed for {current_date}: {str(e)}')
        return {
            'success': False,
            'date': current_date.strftime('%Y-%m-%d') if current_date else 'Unknown',
            'error': str(e)
        }

@app.schedule(schedule="0 8 1 * *", arg_name="timer", run_on_startup=False, use_monitor=False)
def monthly_report_generator(timer: func.TimerRequest) -> None:
    """
    Generate and send monthly reports.
    Runs on the 1st of every month at 8:00 AM.
    """
    logging.info('Monthly report generator started.')
    
    try:
        result = generate_reports_on_demand()
        if result['success']:
            logging.info('Monthly report generator completed successfully.')
        else:
            logging.error(f'Monthly report generator failed: {result.get("error", "Unknown error")}')
            raise Exception(result.get("error", "Unknown error"))
        
    except Exception as e:
        logging.error(f'Monthly report generator failed: {str(e)}')
        raise 

@app.route(route="generate-reports", auth_level=func.AuthLevel.FUNCTION)
def generate_reports_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint to generate reports on demand.
    Call this endpoint to test the function after deployment.
    """
    logging.info('HTTP trigger for report generation received.')
    
    try:
        # Parse request body for optional date parameter
        req_body = req.get_json()
        target_date = None
        
        if req_body and 'date' in req_body:
            try:
                target_date = datetime.strptime(req_body['date'], '%Y-%m-%d').date()
                logging.info(f'Generating reports for specific date: {target_date}')
            except ValueError:
                return func.HttpResponse(
                    json.dumps({'error': 'Invalid date format. Use YYYY-MM-DD'}),
                    status_code=400,
                    mimetype='application/json'
                )
        
        # Generate reports
        result = generate_reports_on_demand(target_date)
        
        # Return response
        if result['success']:
            return func.HttpResponse(
                json.dumps(result),
                status_code=200,
                mimetype='application/json'
            )
        else:
            return func.HttpResponse(
                json.dumps(result),
                status_code=500,
                mimetype='application/json'
            )
            
    except Exception as e:
        logging.error(f'HTTP trigger failed: {str(e)}')
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        ) 