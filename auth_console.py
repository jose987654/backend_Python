from flask import Flask, jsonify, redirect, request, session, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
import os

refresh_secrets_file="./client_secret_917854844662-kib0uct1qgpmqci7od6dusa3rbvjphn7.apps.googleusercontent.com.json"
script_directory = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
OAUTH_SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
SEARCH_CONSOLE_API_NAME = 'searchconsole'
SEARCH_CONSOLE_API_VERSION = 'v1'
TOKEN_DIR = os.path.join(os.path.dirname(__file__), 'token')
# TOKEN_DIR = os.path.abspath(os.path.dirname(__file__), 'token')
TOKEN_PATH = os.path.join(TOKEN_DIR, 'token.json')


# def setup_search_console_api():
#     script_directory = os.path.dirname(os.path.abspath(__file__))
#     CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, refresh_secrets_file))
    
#     flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, OAUTH_SCOPES)
#     credentials = flow.run_local_server(port=0)
#     webmasters_service = build(SEARCH_CONSOLE_API_NAME, SEARCH_CONSOLE_API_VERSION, credentials=credentials)
#     return webmasters_service


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
    print("site list",site_list)
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

        return jsonify({
            'site_info': site_info,
            'sitemap_path': sitemap_path,
            'search_analytics_data': search_analytics_data
        })
    else:
        return jsonify({'error': 'No sites found'})

# Route to fetch Search Console data
@app.route('/fetch_search_console_data')
def fetch_search_console_data_route():
    webmasters_service = setup_search_console_api()
    return fetch_search_console_data(webmasters_service)

if __name__ == '__main__':
    app.run(debug=True)
