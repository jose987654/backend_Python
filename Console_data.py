import json
import os
from flask import Flask, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from google.oauth2.credentials import Credentials
from google.ads.googleads.client import GoogleAdsClient
from email.mime.text import MIMEText
from get_Campaigns import get_Campaigns, YAML_PATH, CUSTOMER_ID
import concurrent.futures
from Email_clients import recipient_emails,all_recipients
from google.auth.transport.requests import Request
from flask import Flask, jsonify, redirect, request, session, url_for
from google_auth_oauthlib.flow import InstalledAppFlow


# def setup_search_console_api(client_secrets_file):
#     script_directory = os.path.dirname(os.path.abspath(__file__))
#     CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, client_secrets_file))
#     OAUTH_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
#     with open(CLIENT_SECRETS_FILE, 'r') as json_keyfile:
#         keyfile_dict = json.load(json_keyfile)
#     credentials = service_account.Credentials.from_service_account_info(keyfile_dict, scopes=[OAUTH_SCOPE])
#     webmasters_service = build('searchconsole', 'v1', credentials=credentials)
#     return webmasters_service
refresh_secrets_file="./client_secret_917854844662-kib0uct1qgpmqci7od6dusa3rbvjphn7.apps.googleusercontent.com.json"
script_directory = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
OAUTH_SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
SEARCH_CONSOLE_API_NAME = 'searchconsole'
SEARCH_CONSOLE_API_VERSION = 'v1'
TOKEN_DIR = os.path.join(os.path.dirname(__file__), 'token')

TOKEN_PATH = os.path.join(TOKEN_DIR, 'token.json')

def setup_search_console_api():    
    CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, refresh_secrets_file))
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, OAUTH_SCOPES)
    credentials = obtain_or_refresh_credentials(flow)
    webmasters_service = build(SEARCH_CONSOLE_API_NAME, SEARCH_CONSOLE_API_VERSION, credentials=credentials)
    return webmasters_service

def obtain_or_refresh_credentials(flow):
    if os.path.exists(TOKEN_PATH):
        credentials = Credentials.from_authorized_user_file(TOKEN_PATH, OAUTH_SCOPES)
    else:
        credentials = flow.run_local_server(port=0)
        save_credentials(credentials)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        save_credentials(credentials)
    return credentials

def save_credentials(credentials):
    with open(TOKEN_PATH, 'w') as token_file:
        token_file.write(credentials.to_json())   


def fetch_search_console_data(webmasters_service):
    current_date = datetime.now().date()
    start_date = (current_date - timedelta(days=2000)).isoformat()
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
        # print("search data",search_analytics_data)
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

def fetch_search_console_errors(webmasters_service):
    current_date = datetime.now().date()
    start_date = (current_date - timedelta(days=2)).isoformat()
    end_date = current_date.isoformat()

    try:
        # Fetch the list of sites
        site_list = webmasters_service.sites().list().execute()

        # Check if 'siteEntry' is present in the response
        if 'siteEntry' in site_list:
            sites = site_list['siteEntry']

            for site in sites:
                site_url = site['siteUrl']

                # Make a request to fetch site errors
                request = {
                    'siteUrl': site_url,
                    'startDate': start_date,
                    'endDate': end_date,
                    'dimensions': ['date']
                }

                errors_data = webmasters_service.urlcrawlerrorscounts().query(siteUrl=site_url, startDate=start_date, endDate=end_date, dimensions=['date']).execute()

                # Process and print the errors data
                print(f"Site: {site_url}")
                print("Errors Data:", errors_data)
                print("\n")
        else:
            print("No sites found in the response.")
    
    except Exception as e:
        print(f"Error fetching search console errors: {e}")


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


# Usage example:
# Assuming you already have a 'webmasters_service' object
# Refer to the Google API Python client documentation for initializing the service.
# https://developers.google.com/webmaster-tools/search-console-api-original/v3/quickstart
# fetch_search_console_errors(webmasters_service)