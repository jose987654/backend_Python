import json
import os
from flask import Flask, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from google.ads.googleads.client import GoogleAdsClient
from email.mime.text import MIMEText
from get_Campaigns import get_Campaigns, YAML_PATH, CUSTOMER_ID
import concurrent.futures
from Email_clients import recipient_emails,all_recipients
# recipient_emails =  ["wasswajose9@gmail.com", "wasswajose9999@gmail.com","jacobtusiime6@gmail.com"]    

def setup_search_console_api(client_secrets_file):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, client_secrets_file))
    OAUTH_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

    with open(CLIENT_SECRETS_FILE, 'r') as json_keyfile:
        keyfile_dict = json.load(json_keyfile)

    credentials = service_account.Credentials.from_service_account_info(keyfile_dict, scopes=[OAUTH_SCOPE])

    webmasters_service = build('searchconsole', 'v1', credentials=credentials)
    return webmasters_service

def fetch_search_console_data(webmasters_service):
    current_date = datetime.now().date()
    start_date = (current_date - timedelta(days=20)).isoformat()
    end_date = current_date.isoformat()

    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date']
    }

    site_list = webmasters_service.sites().list().execute()

    if 'siteEntry' in site_list:
        first_site = site_list['siteEntry'][0]
        site_url = first_site['siteUrl']
        permission_level = first_site['permissionLevel']

        site_info = {'siteUrl': site_url, 'permissionLevel': permission_level}

        sitemap_data = webmasters_service.sitemaps().list(siteUrl=site_url).execute()
        first_sitemap = sitemap_data['sitemap'][0]
        sitemap_path = first_sitemap['path']

        search_analytics_data = webmasters_service.searchanalytics().query(
            siteUrl=site_url,
            body=request
        ).execute()

        # site_errors = get_site_errors(webmasters_service, site_url)

        return {
            'site_list': site_list,
            'first_site': first_site,
            # 'site_errors': site_errors,
            'site_info': site_info,
            'sitemap_path': sitemap_path,
            'search_analytics_data': search_analytics_data
        }
    else:
        return {'error': 'No sites found'}

def get_site_errors(webmasters_service, site_url):
    request = webmasters_service.urlcrawlerrorscounts().query(siteUrl=site_url)
    try:
        response = request.execute()
        return response
    except Exception as e:
        print(f"Error fetching site errors: {e}")
        return None


def send_report_email(site_info, search_analytics_data):
   
    # print("sending email ")
    # print("Email body ",site_info, search_analytics_data)
    email_content = f"Search Console Report\n\nSite URL: {site_info['siteUrl']}\n\nSearch Analytics Data: {search_analytics_data}"

    # Replace these variables with your email server and credentials
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'wasswajose9@gmail.com'
    smtp_password = 'yqma mkrv xtxq icrj'
    recipient_emails =  ["wasswajose9@gmail.com", "wasswajose9999@gmail.com","jacobtusiime6@gmail.com"]    

    # Create and send the email
    msg = MIMEText(email_content)
    msg['Subject'] = 'Search API Report'
    msg['From'] = smtp_username
    msg['To'] = ', '.join(recipient_emails)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipient_emails, msg.as_string())

def send_report_email_2(site_info, search_analytics_data,campaign_data):
   
   for entry in all_recipients:
    if 'status' not in entry:
        entry['status'] = False

    # Now, use the list comprehension to get active recipient emails
    active_recipient_emails = [
        entry['email'] for entry in all_recipients if entry.get('status', False) is True
    ]

    # Check if there are active recipients
    if not active_recipient_emails:
        print("No active recipients to send the email to.")
        return
    # print("sending email ")
    # print("Email body ",site_info, search_analytics_data)
    email_content = f"Search Console Report\n\nSite URL: {site_info['siteUrl']}\n\nSearch Analytics Data: {search_analytics_data}\n\nCampaign Data :{campaign_data}"

    # Replace these variables with your email server and credentials
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'wasswajose9@gmail.com'
    smtp_password = 'yqma mkrv xtxq icrj'
   
    # Create and send the email
    msg = MIMEText(email_content)
    msg['Subject'] = 'Search API Report'
    msg['From'] = smtp_username
    msg['To'] = ', '.join(active_recipient_emails)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, active_recipient_emails, msg.as_string())

def schedule_report_email():
    
    # Set up the Search Console API
    search_console_service = setup_search_console_api("./local-env-404011-e776db327a1f.json")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks for concurrent execution
        search_console_future = executor.submit(fetch_search_console_data, search_console_service)
        campaign_fetch_future = executor.submit(get_Campaigns, GoogleAdsClient.load_from_storage(YAML_PATH), CUSTOMER_ID)

        # Wait for both tasks to complete
        search_console_data = search_console_future.result()
        print("fetch_search_console_data finished")
        campaign_fetch_data = campaign_fetch_future.result()
        print("get_Campaigns finished")

    # Send the email with the obtained data
    send_report_email_2(search_console_data['site_info'], search_console_data['search_analytics_data'], campaign_fetch_data)
    print("sent report out ")
    print("================================================")
    # # Fetch data and send report every minute
    # @scheduler.scheduled_job('interval', minutes=1)
    # def job():
    #     search_console_data = fetch_search_console_data(search_console_service)        
    #     send_report_email(search_console_data['site_info'], search_console_data['search_analytics_data'])
    #     print("sent report out ")
    #     print("================================================")
    # # Start the scheduler
    # scheduler.start()

    # try:
    #     # Keep the main thread alive
    #     while True:
    #         pass
    # except (KeyboardInterrupt, SystemExit):
    #     # Shut down the scheduler gracefully when needed
    #     scheduler.shutdown()


