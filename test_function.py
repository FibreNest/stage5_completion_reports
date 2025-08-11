#!/usr/bin/env python3
"""
Test script for the automated reporting function.
This script allows you to test the function logic locally without deploying to Azure.
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the function logic
from function_app import (
    get_quarter_dates,
    is_quarter_end,
    get_previous_month_date,
    get_previous_quarter_dates,
    create_csv_report,
    send_email_with_attachment
)

def test_date_calculations():
    """Test the date calculation functions."""
    print("Testing date calculations...")
    
    # Test current date
    current_date = date.today()
    print(f"Current date: {current_date}")
    
    # Test quarter dates
    quarter_start, quarter_end, quarter_num = get_quarter_dates(current_date)
    print(f"Current quarter: Q{quarter_num} ({quarter_start} to {quarter_end})")
    
    # Test if quarter end
    is_quarter_end_date = is_quarter_end(current_date)
    print(f"Is quarter end: {is_quarter_end_date}")
    
    # Test previous month
    previous_month = get_previous_month_date(current_date)
    print(f"Previous month: {previous_month}")
    
    # Test previous quarter
    if is_quarter_end_date:
        prev_quarter_start, prev_quarter_end = get_previous_quarter_dates(current_date)
        print(f"Previous quarter: {prev_quarter_start} to {prev_quarter_end}")
    
    print()

def test_csv_generation():
    """Test CSV report generation with real data from database."""
    print("Testing CSV generation with real data...")
    
    try:
        # Get real data from database
        from function_app import get_db_connection, fetch_data_from_db
        
        conn = get_db_connection()
        
        # Query all data from the table
        query = "SELECT * FROM public.stage_5_plots"
        real_data = fetch_data_from_db(conn, query)
        
        if not real_data:
            print("⚠️  No data found in table. Using sample data instead.")
            # Fallback to sample data if table is empty
            real_data = [
                {
                    'id': 225,
                    'ucr': '210203840',
                    'company': 'Persimmon Homes',
                    'region': 'Wessex',
                    'development': 'Ph @ Wellington Gate 5, Grove',
                    'plot': '840',
                    'stage_5_achieved_date': '2025-07-01',
                    'uprn': None,
                    'postcode': 'OX12 0SB',
                    'report_month': '2025-07-01',
                    'report_quarter': '2025-07-01',
                    'created_at': '2025-07-16 17:19:46.142245',
                    'updated_at': '2025-07-16 17:19:46.142245'
                }
            ]
        
        print(f"📊 Retrieved {len(real_data)} records from database")
        
        # Generate CSV from real data
        csv_data = create_csv_report(real_data, "test_report.csv")
        print(f"✅ CSV generated successfully. Size: {len(csv_data)} bytes")
        
        # Show first few lines of CSV
        csv_content = csv_data.decode('utf-8')
        lines = csv_content.split('\n')[:5]
        print("CSV preview:")
        for line in lines:
            print(f"  {line}")
        
        conn.close()
            
    except Exception as e:
        print(f"❌ CSV generation failed: {str(e)}")
    
    print()

def test_email_function():
    """Test email functionality with real data from database."""
    print("Testing email functionality with real data...")
    
    # Check if SendGrid credentials are configured
    bearer_token = os.getenv('SENDGRID_BEARER_TOKEN')
    sendgrid_endpoint = os.getenv('SENDGRID_ENDPOINT')
    sender_email = os.getenv('SENDER_EMAIL')
    recipient_emails = os.getenv('RECIPIENT_EMAILS')
    
    if not all([bearer_token, sendgrid_endpoint, sender_email, recipient_emails]):
        print("SendGrid credentials not configured. Skipping email test.")
        print("Please set SENDGRID_BEARER_TOKEN, SENDGRID_ENDPOINT, SENDER_EMAIL, and RECIPIENT_EMAILS in local.settings.json")
        return
    
    try:
        # Get real data from database
        from function_app import get_db_connection, fetch_data_from_db, create_csv_report
        
        conn = get_db_connection()
        
        # Test multiple scenarios to show different report types
        from datetime import date
        
        print("📅 Testing multiple scenarios with real data...")
        
        # Scenario 1: August 1st (current month - should show July data)
        print("\n🔍 Scenario 1: August 1st (current month)")
        aug_1st = date(2025, 8, 1)
        july_month = date(2025, 7, 1)
        cumulative_start = date(2025, 8, 1)
        
        print(f"   Current date: {aug_1st}")
        print(f"   Previous month: {july_month}")
        print(f"   Cumulative start: {cumulative_start}")
        
        # Generate reports for August 1st scenario
        reports_aug = []
        
        # Monthly Report (July data)
        monthly_query_july = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE report_month = %s
        """
        monthly_data_july = fetch_data_from_db(conn, monthly_query_july, (july_month,))
        if monthly_data_july:
            monthly_csv_july = create_csv_report(monthly_data_july, f"monthly_report_{july_month.strftime('%Y_%m')}.csv")
            reports_aug.append({
                'name': f"Monthly Report - {july_month.strftime('%B %Y')}",
                'data': monthly_csv_july,
                'filename': f"monthly_report_{july_month.strftime('%Y_%m')}.csv",
                'count': len(monthly_data_july)
            })
            print(f"   📊 Monthly report (July): {len(monthly_data_july)} records")
        
        # Cumulative Report (from 01/08)
        cumulative_query_aug = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE stage_5_achieved_date >= %s
        """
        cumulative_data_aug = fetch_data_from_db(conn, cumulative_query_aug, (cumulative_start,))
        if cumulative_data_aug:
            cumulative_csv_aug = create_csv_report(cumulative_data_aug, f"cumulative_report_{aug_1st.strftime('%Y_%m')}.csv")
            reports_aug.append({
                'name': f"Cumulative Report - {aug_1st.strftime('%B %Y')}",
                'data': cumulative_csv_aug,
                'filename': f"cumulative_report_{aug_1st.strftime('%Y_%m')}.csv",
                'count': len(cumulative_data_aug)
            })
            print(f"   📊 Cumulative report: {len(cumulative_data_aug)} records")
        
        # Scenario 2: April 1st (quarterly report day)
        print("\n🔍 Scenario 2: April 1st (quarterly report day)")
        apr_1st = date(2025, 4, 1)
        mar_month = date(2025, 3, 1)
        q1_start = date(2025, 1, 1)
        q1_end = date(2025, 3, 31)
        
        print(f"   Current date: {apr_1st}")
        print(f"   Previous month: {mar_month}")
        print(f"   Previous quarter: {q1_start} to {q1_end}")
        
        # Generate reports for April 1st scenario
        reports_apr = []
        
        # Monthly Report (March data)
        monthly_data_mar = fetch_data_from_db(conn, monthly_query_july, (mar_month,))
        if monthly_data_mar:
            monthly_csv_mar = create_csv_report(monthly_data_mar, f"monthly_report_{mar_month.strftime('%Y_%m')}.csv")
            reports_apr.append({
                'name': f"Monthly Report - {mar_month.strftime('%B %Y')}",
                'data': monthly_csv_mar,
                'filename': f"monthly_report_{mar_month.strftime('%Y_%m')}.csv",
                'count': len(monthly_data_mar)
            })
            print(f"   📊 Monthly report (March): {len(monthly_data_mar)} records")
        
        # Quarterly Report (Q1 data)
        quarterly_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE report_quarter >= %s AND report_quarter <= %s
        """
        quarterly_data = fetch_data_from_db(conn, quarterly_query, (q1_start, q1_end))
        if quarterly_data:
            quarterly_csv = create_csv_report(quarterly_data, f"quarterly_report_{q1_start.strftime('%Y')}_Q1.csv")
            reports_apr.append({
                'name': f"Quarterly Report - Q1 {q1_start.strftime('%Y')}",
                'data': quarterly_csv,
                'filename': f"quarterly_report_{q1_start.strftime('%Y')}_Q1.csv",
                'count': len(quarterly_data)
            })
            print(f"   📊 Quarterly report (Q1): {len(quarterly_data)} records")
        
        # Cumulative Report (from 01/08) - same for both scenarios
        if cumulative_data_aug:
            cumulative_csv_apr = create_csv_report(cumulative_data_aug, f"cumulative_report_{apr_1st.strftime('%Y_%m')}.csv")
            reports_apr.append({
                'name': f"Cumulative Report - {apr_1st.strftime('%B %Y')}",
                'data': cumulative_csv_apr,
                'filename': f"cumulative_report_{apr_1st.strftime('%Y_%m')}.csv",
                'count': len(cumulative_data_aug)
            })
            print(f"   📊 Cumulative report: {len(cumulative_data_aug)} records")
        
        # Create comprehensive reports including Q3 Current Quarter data
        from datetime import date
        test_date = date.today()
        
        # Get Q3 Current Quarter data (from July 1st to current date)
        quarter_start_current, quarter_end_current, quarter_num_current = get_quarter_dates(test_date)
        q3_current_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE stage_5_achieved_date >= %s AND stage_5_achieved_date <= %s
        """
        q3_current_data = fetch_data_from_db(conn, q3_current_query, (quarter_start_current, test_date))
        
        # Create comprehensive reports list
        comprehensive_reports = []
        
        # Add Monthly Report (July data)
        if reports_aug:
            comprehensive_reports.extend(reports_aug)
        
        # Add Q3 Current Quarter Report
        if q3_current_data:
            q3_current_csv = create_csv_report(q3_current_data, f"q3_current_quarter_{quarter_start_current.strftime('%Y_%m')}_to_{test_date.strftime('%Y_%m_%d')}.csv")
            comprehensive_reports.append({
                'name': f"Q3 Current Quarter Report - {quarter_start_current.strftime('%B %Y')} to {test_date.strftime('%B %d')}",
                'data': q3_current_csv,
                'filename': f"q3_current_quarter_{quarter_start_current.strftime('%Y_%m')}_to_{test_date.strftime('%Y_%m_%d')}.csv",
                'count': len(q3_current_data)
            })
            print(f"   📊 Q3 Current Quarter report: {len(q3_current_data)} records")
        
        conn.close()
        
        if not comprehensive_reports:
            print("   ⚠️  No reports generated - no data found for test dates")
            return
        
        # Send email with all comprehensive reports
        print(f"\n📧 Sending email with {len(comprehensive_reports)} comprehensive reports...")
        
        # Create email body
        email_body = f"""
        <h2>Stage 5 Completion Reports - {test_date.strftime('%B %d, %Y')}</h2>
        <p>This is a test email with real data from your database.</p>
        <h3>Reports Generated:</h3>
        <ul>
        """
        
        for report in comprehensive_reports:
            if "Cumulative Report" in report['name']:
                email_body += f"<li><strong>Cumulative Report</strong> - <strong>Since 1st of August 2025</strong>: {report['count']} records</li>"
            else:
                email_body += f"<li><strong>{report['name']}</strong>: {report['count']} records</li>"
        
        email_body += """
        </ul>
        <p>Report generated on: """ + test_date.strftime('%Y-%m-%d') + """</p>
        """
        
        # Print the email body for verification
        print(f"\n📧 Email Body Preview:")
        print("=" * 50)
        print(email_body)
        print("=" * 50)
        
        # Send email with ALL reports as attachments
        from function_app import send_email_with_multiple_attachments
        
        # Prepare attachments for the new function
        attachments = []
        for report in comprehensive_reports:
            attachments.append({
                'data': report['data'],
                'filename': report['filename']
            })
        
        success = send_email_with_multiple_attachments(
            subject=f"Stage 5 Completion Reports - {test_date.strftime('%B %d, %Y')}",
            body=email_body,
            attachments=attachments,
            recipient_emails=recipient_emails.split(',')
        )
        
        if success:
            print(f"✅ Test email sent successfully with {len(comprehensive_reports)} attachments!")
            for i, report in enumerate(comprehensive_reports):
                print(f"   📎 Attachment {i+1}: {report['filename']} ({len(report['data'])} bytes)")
                print(f"      📊 Contains: {report['count']} real records")
        else:
            print("❌ Test email failed to send.")
            
    except Exception as e:
        print(f"❌ Email test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()

def test_database_connection():
    """Test database connection (requires valid database credentials)."""
    print("Testing database connection...")
    
    db_connection_string = os.getenv('DB_CONNECTION_STRING')
    if not db_connection_string:
        print("Database connection string not configured. Skipping database test.")
        print("Please set DB_CONNECTION_STRING in local.settings.json")
        return
    
    try:
        from function_app import get_db_connection
        conn = get_db_connection()
        print("Database connection successful!")
        
        # Test a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"Database version: {version[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
    
    print()

def test_all_report_variants():
    """Test all report variants with different dates and real data."""
    print("Testing all report variants with real data...")
    
    try:
        from function_app import (
            get_db_connection, fetch_data_from_db, create_csv_report,
            get_quarter_dates, is_quarter_end, get_previous_month_date,
            get_previous_quarter_dates
        )
        
        conn = get_db_connection()
        
        # Test 1: Current date (August 11, 2025)
        print("\n📅 Test 1: Current Date (August 11, 2025)")
        current_date = date.today()
        print(f"   Current date: {current_date}")
        
        # Test 2: Simulate January 1st (Q1 start, previous month = December)
        print("\n📅 Test 2: Simulated January 1st (Q1 start)")
        jan_1st = date(2025, 1, 1)
        prev_month_jan = get_previous_month_date(jan_1st)
        quarter_start, quarter_end, quarter_num = get_quarter_dates(jan_1st)
        is_q_end = is_quarter_end(jan_1st)
        print(f"   Date: {jan_1st}")
        print(f"   Previous month: {prev_month_jan}")
        print(f"   Quarter: Q{quarter_num} ({quarter_start} to {quarter_end})")
        print(f"   Is quarter end: {is_q_end}")
        
        # Test 3: Simulate March 31st (Q1 end)
        print("\n📅 Test 3: Simulated March 31st (Q1 end)")
        mar_31st = date(2025, 3, 31)
        prev_month_mar = get_previous_month_date(mar_31st)
        quarter_start_mar, quarter_end_mar, quarter_num_mar = get_quarter_dates(mar_31st)
        is_q_end_mar = is_quarter_end(mar_31st)
        print(f"   Date: {mar_31st}")
        print(f"   Previous month: {prev_month_mar}")
        print(f"   Quarter: Q{quarter_num_mar} ({quarter_start_mar} to {quarter_end_mar})")
        print(f"   Is quarter end: {is_q_end_mar}")
        
        # Test 4: Simulate April 1st (Q2 start, should trigger quarterly report)
        print("\n📅 Test 4: Simulated April 1st (Q2 start, quarterly report day)")
        apr_1st = date(2025, 4, 1)
        prev_month_apr = get_previous_month_date(apr_1st)
        quarter_start_apr, quarter_end_apr, quarter_num_apr = get_quarter_dates(apr_1st)
        is_q_end_apr = is_quarter_end(apr_1st)
        prev_q_start, prev_q_end = get_previous_quarter_dates(apr_1st)
        print(f"   Date: {apr_1st}")
        print(f"   Previous month: {prev_month_apr}")
        print(f"   Current quarter: Q{quarter_num_apr} ({quarter_start_apr} to {quarter_end_apr})")
        print(f"   Is quarter end: {is_q_end_apr}")
        print(f"   Previous quarter: {prev_q_start} to {prev_q_end}")
        
        # Test 5: Simulate September 30th (Q3 end, should trigger quarterly report)
        print("\n📅 Test 5: Simulated September 30th (Q3 end, quarterly report day)")
        sep_30th = date(2025, 9, 30)
        prev_month_sep = get_previous_month_date(sep_30th)
        quarter_start_sep, quarter_end_sep, quarter_num_sep = get_quarter_dates(sep_30th)
        is_q_end_sep = is_quarter_end(sep_30th)
        prev_q_start_sep, prev_q_end_sep = get_previous_quarter_dates(sep_30th)
        print(f"   Date: {sep_30th}")
        print(f"   Previous month: {prev_month_sep}")
        print(f"   Current quarter: Q{quarter_num_sep} ({quarter_start_sep} to {quarter_end_sep})")
        print(f"   Is quarter end: {is_q_end_sep}")
        print(f"   Previous quarter: {prev_q_start_sep} to {prev_q_end_sep}")
        
        # Test 6: Generate actual reports with real data
        print("\n📊 Test 5: Generating actual reports with real data")
        
        # Monthly report (previous month data)
        monthly_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE report_month = %s
        """
        monthly_data = fetch_data_from_db(conn, monthly_query, (prev_month_apr,))
        print(f"   Monthly data (previous month): {len(monthly_data)} records")
        
        # Cumulative report (from 01/08)
        cumulative_start_date = datetime.strptime(os.getenv('CUMULATIVE_START_DATE'), '%Y-%m-%d').date()
        cumulative_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE stage_5_achieved_date >= %s
        """
        cumulative_data = fetch_data_from_db(conn, cumulative_query, (cumulative_start_date,))
        print(f"   Cumulative data (from {cumulative_start_date}): {len(cumulative_data)} records")
        
        # Quarterly report (previous quarter data)
        quarterly_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE report_quarter >= %s AND report_quarter <= %s
        """
        quarterly_data = fetch_data_from_db(conn, quarterly_query, (prev_q_start, prev_q_end))
        print(f"   Quarterly data (previous quarter): {len(quarterly_data)} records")
        
        # Generate CSV reports
        if monthly_data:
            monthly_csv = create_csv_report(monthly_data, f"monthly_report_{prev_month_apr.strftime('%Y_%m')}.csv")
            print(f"   ✅ Monthly CSV generated: {len(monthly_csv)} bytes")
        
        if cumulative_data:
            cumulative_csv = create_csv_report(cumulative_data, f"cumulative_report_{apr_1st.strftime('%Y_%m')}.csv")
            print(f"   ✅ Cumulative CSV generated: {len(cumulative_csv)} bytes")
        
        if quarterly_data:
            quarterly_csv = create_csv_report(quarterly_data, f"quarterly_report_{prev_q_start.strftime('%Y')}_Q{get_quarter_dates(prev_q_start)[2]}.csv")
            print(f"   ✅ Quarterly CSV generated: {len(quarterly_csv)} bytes")
        
        # Test Q3 end scenario with real data
        print("\n📊 Test Q3 End Scenario (September 30th) with real data")
        
        # Monthly report for August (previous month from September 30th)
        monthly_data_q3 = fetch_data_from_db(conn, monthly_query, (prev_month_sep,))
        print(f"   Monthly data (August): {len(monthly_data_q3)} records")
        
        # Quarterly report for Q2 (previous quarter from Q3 end)
        quarterly_data_q3 = fetch_data_from_db(conn, quarterly_query, (prev_q_start_sep, prev_q_end_sep))
        print(f"   Quarterly data (Q2): {len(quarterly_data_q3)} records")
        
        # Cumulative report (from 01/08)
        cumulative_data_q3 = fetch_data_from_db(conn, cumulative_query, (cumulative_start_date,))
        print(f"   Cumulative data (from {cumulative_start_date}): {len(cumulative_data_q3)} records")
        
        # Generate CSV reports for Q3 end scenario
        if monthly_data_q3:
            monthly_csv_q3 = create_csv_report(monthly_data_q3, f"monthly_report_{prev_month_sep.strftime('%Y_%m')}.csv")
            print(f"   ✅ Monthly CSV generated: {len(monthly_csv_q3)} bytes")
        
        if quarterly_data_q3:
            quarterly_csv_q3 = create_csv_report(quarterly_data_q3, f"quarterly_report_{prev_q_start_sep.strftime('%Y')}_Q{get_quarter_dates(prev_q_start_sep)[2]}.csv")
            print(f"   ✅ Quarterly CSV generated: {len(quarterly_csv_q3)} bytes")
        
        if cumulative_data_q3:
            cumulative_csv_q3 = create_csv_report(cumulative_data_q3, f"cumulative_report_{sep_30th.strftime('%Y_%m')}.csv")
            print(f"   ✅ Cumulative CSV generated: {len(cumulative_csv_q3)} bytes")
        
        # Test Q3 2025 (current quarter not finished) with real data
        print("\n📊 Test Q3 2025 Current Quarter (August 11th) with real data")
        
        # Current date is August 11th, 2025 (Q3 not finished)
        current_date_q3 = date(2025, 8, 11)
        prev_month_current = get_previous_month_date(current_date_q3)
        quarter_start_current, quarter_end_current, quarter_num_current = get_quarter_dates(current_date_q3)
        is_q_end_current = is_quarter_end(current_date_q3)
        
        print(f"   Current date: {current_date_q3}")
        print(f"   Previous month: {prev_month_current}")
        print(f"   Current quarter: Q{quarter_num_current} ({quarter_start_current} to {quarter_end_current})")
        print(f"   Is quarter end: {is_q_end_current}")
        
        # Monthly report for July (previous month from August 11th)
        monthly_data_current = fetch_data_from_db(conn, monthly_query, (prev_month_current,))
        print(f"   Monthly data (July): {len(monthly_data_current)} records")
        
        # Q3 Current Quarter data (from July 1st to current date)
        q3_current_query = """
            SELECT id, ucr, company, region, development, plot, 
                   stage_5_achieved_date, uprn, postcode
            FROM public.stage_5_plots
            WHERE stage_5_achieved_date >= %s AND stage_5_achieved_date <= %s
        """
        q3_current_data = fetch_data_from_db(conn, q3_current_query, (quarter_start_current, current_date_q3))
        print(f"   Q3 Current Quarter data (July 1st to {current_date_q3}): {len(q3_current_data)} records")
        
        # Cumulative report (from 01/08)
        cumulative_data_current = fetch_data_from_db(conn, cumulative_query, (cumulative_start_date,))
        print(f"   Cumulative data (from {cumulative_start_date}): {len(cumulative_data_current)} records")
        
        # Generate CSV reports for current Q3 scenario
        if monthly_data_current:
            monthly_csv_current = create_csv_report(monthly_data_current, f"monthly_report_{prev_month_current.strftime('%Y_%m')}.csv")
            print(f"   ✅ Monthly CSV generated: {len(monthly_csv_current)} bytes")
        
        if q3_current_data:
            q3_current_csv = create_csv_report(q3_current_data, f"q3_current_quarter_{quarter_start_current.strftime('%Y_%m')}_to_{current_date_q3.strftime('%Y_%m_%d')}.csv")
            print(f"   ✅ Q3 Current Quarter CSV generated: {len(q3_current_csv)} bytes")
        
        if cumulative_data_current:
            cumulative_csv_current = create_csv_report(cumulative_data_current, f"cumulative_report_{current_date_q3.strftime('%Y_%m')}.csv")
            print(f"   ✅ Cumulative CSV generated: {len(cumulative_csv_current)} bytes")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Report variants test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()

def load_local_settings():
    """Load Azure Functions local settings."""
    try:
        import json
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        # Set environment variables from local.settings.json
        for key, value in settings.get('Values', {}).items():
            os.environ[key] = value
            
        print("✅ Local settings loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load local settings: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Automated Reports Function - Test Suite")
    print("=" * 50)
    print()
    
    # Load local settings first
    if not load_local_settings():
        print("⚠️  Continuing with environment variables only...")
    
    # Also try to load .env file if it exists
    load_dotenv()
    
    # Run tests
    test_date_calculations()
    test_csv_generation()
    test_email_function()
    test_database_connection()
    test_all_report_variants()
    
    print("=" * 50)
    print("Test suite completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 