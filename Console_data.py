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
from get_Campaigns import get_Campaigns, YAML_PATH, CUSTOMER_ID,load_or_refresh_client
import concurrent.futures
from Email_clients import recipient_emails,all_recipients
from google.auth.transport.requests import Request
from flask import Flask, jsonify, redirect, request, session, url_for
from google_auth_oauthlib.flow import InstalledAppFlow
from reportlab.pdfgen import canvas
from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

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
google_ads_client = load_or_refresh_client()

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

def fetch_search_console_data1(webmasters_service):
    current_date = datetime.now().date()
    start_date = (current_date - timedelta(days=2000)).isoformat()
    end_date = current_date.isoformat()

    request1 = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date']
    }

    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date', 'country', 'device'],  
        # 'searchType': 'web',  # Use 'web' for web search data
        # 'rowLimit': 1000,  # Adjust the row limit as needed
        # 'aggregationType': 'auto',  # Use 'auto' for automatic aggregation
        # 'dimensionFilterGroups': [
        #     {
        #         'filters': [
        #             {'dimension': 'device', 'operator': 'equals', 'expression': 'MOBILE'}  # Add filter for mobile devices
        #         ]
        #     }
        # ]
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

def fetch_search_console_data(webmasters_service):
    current_date = datetime.now().date()
    start_date = (current_date - timedelta(days=2000)).isoformat()
    end_date = current_date.isoformat()

    # Request for search analytics
    request_analytics = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date'],
        # Add other parameters as needed
    }
     
    # Request for popular countries
    request_countries = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['country'],
        # Add other parameters as needed
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

        # Fetch search analytics data
        search_analytics_data = webmasters_service.searchanalytics().query(
            siteUrl=site_url,
            body=request_analytics
        ).execute()

        # Fetch popular countries data
        popular_countries_data = webmasters_service.searchanalytics().query(
            siteUrl=site_url,
            body=request_countries
        ).execute()

        # site_errors = get_site_errors(webmasters_service, site_url)
        # print("search data",search_analytics_data)
        return {
            'site_list': site_list,
            'first_site': first_site,
            # 'site_errors': site_errors,
            'site_info': site_info,
            'sitemap_path': sitemap_path,
            'search_analytics_data': search_analytics_data,
            'popular_countries_data': popular_countries_data
        }
    else:
        return {'error': 'No sites found'}

# def get_site_errors(webmasters_service, site_url):
#     # search_console_service = setup_search_console_api() .urlcrawlerrors().query(siteUrl=site_url, category='serverError')
#     # request = webmasters_service.urlcrawlerrors().query(siteUrl=site_url)
#     request = webmasters_service.urlcrawlerrors().query(siteUrl=site_url, category='serverError')
#     try:
#         response = request.execute()
#         return response
#     except Exception as e:
#         print(f"Error fetching site errors: {e}")
#         return None
def get_site_errors(webmasters_service, site_url):
    try:
        # Use the Search Console API to fetch site errors
        print(f"this works ")
        request = webmasters_service.urlcrawlerrors().query(siteUrl=site_url, category='serverError')
        response = request.execute()

        if 'urlCrawlErrorCountsPerType' in response:
            return response['urlCrawlErrorCountsPerType']
        else:
            print("No error data found.")
            return {}
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

                # errors_data = webmasters_service.urlcrawlerrorscounts().query(siteUrl=site_url, startDate=start_date, endDate=end_date, dimensions=['date']).execute()
                errors_data = webmasters_service.urlcrawlerrors().list(siteUrl=site_url, category='serverError')
                # Process and print the errors data webmasters_service.urlcrawlerrors().query(siteUrl=site_url, category='serverError')
                print(f"Site: {site_url}")
                print("Errors Data:", errors_data)
                print("\n")
        else:
            print("No sites found in the response.")
    
    except Exception as e:
        print(f"Error fetching search console errors: {e}")

def generate_pdf(site_info, search_analytics_data, campaign_data, pdf_filepath):
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(pdf_filepath), exist_ok=True)
    # print("campaigns ",campaign_data)
    # Create a PDF file with the provided information
    with open(pdf_filepath, 'wb') as pdf_file:
        c = canvas.Canvas(pdf_file)
        
        # Title
        c.setFont("Helvetica", 16)
        c.drawString(72, 800, "Search Console Report and Ads Campaigns")
        
        # Site URL
        c.setFont("Helvetica", 12)
        c.drawString(72, 780, f"Site URL: {site_info['siteUrl']}")

         # Campaign Data
        c.drawString(72, 740, "Campaign Data:")
        text_object = c.beginText(72, 720)
        text_object.setFont("Helvetica", 12)
        campaigns = campaign_data.get('campaigns', [])  # Access the 'campaigns' key
        for campaign in campaigns:
            if 'id' in campaign and 'name' in campaign:
                text_object.textLine(f"ID: {campaign['id']}, Name: {campaign['name']}")
            else:
                text_object.textLine("Invalid campaign structure")

        c.drawText(text_object)       
        
        # c.showPage()
        # Search Analytics Data
        c.drawString(72, 680, "Search Analytics Data:")
        text_object = c.beginText(72, 660)
        text_object.setFont("Helvetica", 12)
        # Display all key-value pairs in vertical format
        # for key, value in search_analytics_data.items():
        #     text_object.textLine(f"{key}: {value}")
        # Debug prints
        # print("Rows:", search_analytics_data.get('rows', []))
        # Display each row in vertical format
        rows = search_analytics_data.get('rows', [])  # Access the 'rows' key
        for row in rows:
            # print("Row:", row)
            # if text_object.getY() < 200:
            #     c.showPage()
            #     # Adjust y-coordinate for the new page
            #     text_object = c.beginText(72, 740)
                # text_object.setTextOrigin(72, 740)
            text_object.textLine(f"Date: {row['keys'][0]}, Clicks: {row['clicks']}, Impressions: {row['impressions']}, CTR: {row['ctr']}")

        response_aggregation_type = search_analytics_data.get('responseAggregationType', '')
        text_object.textLine(f"Response Aggregation Type: {response_aggregation_type}")

        c.drawText(text_object)  
        c.save()   
       

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
#    pdf_filepath = '/path/to/temp_report.pdf'
    pdf_filepath = './temp_report.pdf'
    generate_pdf(site_info, search_analytics_data, campaign_data, pdf_filepath)
   
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
    # email_content = f"Search Console Report\n\nSite URL: {site_info['siteUrl']}\n\nSearch Analytics Data: \n\nCampaign Data :{campaign_data}"

    # Replace these variables with your email server and credentials
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'wasswajose9@gmail.com'
    smtp_password = 'yqma mkrv xtxq icrj'
   
    # Create and send the email
    # msg = MIMEText(email_content)
    msg = MIMEMultipart()
    msg['Subject'] = 'Search API Report'
    msg['From'] = smtp_username
    msg['To'] = ', '.join(active_recipient_emails)

    with open(pdf_filepath, 'rb') as file:
        attach = MIMEApplication(file.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_filepath))
        msg.attach(attach)

    email_content = f"Search Console Report\n\nSite URL: {site_info['siteUrl']}\n\nSearch Analytics Data: \n\nCampaign Data: {campaign_data}"
    msg.attach(MIMEText(email_content, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, active_recipient_emails, msg.as_string())
    
    os.remove(pdf_filepath)

def schedule_report_email():
    
    # Set up the Search Console API
    # search_console_service = setup_search_console_api("./local-env-404011-e776db327a1f.json")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks for concurrent execution
        # search_console_future = executor.submit(fetch_search_console_data, search_console_service)
        # campaign_fetch_future = executor.submit(get_Campaigns, GoogleAdsClient.load_from_storage(YAML_PATH), CUSTOMER_ID)
        search_console_service = setup_search_console_api()
        search_console_future = executor.submit(fetch_search_console_data, search_console_service)
        campaign_fetch_future = executor.submit(get_Campaigns, google_ads_client, CUSTOMER_ID)

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