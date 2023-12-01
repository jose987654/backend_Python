
# Import required packages
import os
import flask
import requests
from oauth2client.client import OAuth2WebServerFlow
from googleapiclient.discovery import build
import httplib2
from flask import Flask, jsonify
import json
from googleapiclient.errors import HttpError
from apscheduler.schedulers.background import BackgroundScheduler
import json
import datetime

script_directory = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, "./local-env-404011-e776db327a1f.json")) 
OAUTH_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
# Load the JSON key file
# json_keyfile_path = 'path_to_your_service_account_key.json'  
with open(CLIENT_SECRETS_FILE, 'r') as json_keyfile:
    keyfile_dict = json.load(json_keyfile)

# Create credentials using the JSON key
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_info(keyfile_dict, scopes=[OAUTH_SCOPE])

# Build the service using these credentials
webmasters_service = build('searchconsole', 'v1', credentials=credentials)
site_list = webmasters_service.sites().list().execute()

current_date = datetime.date.today()

# Format the start and end dates (e.g., last 7 days)
start_date = (current_date - datetime.timedelta(days=7)).isoformat()
end_date = current_date.isoformat()

# Construct the request payload
request = {
    'startDate': start_date,
    'endDate': end_date,
    'dimensions': ['date']
}
print(site_list)
# Check if there are site entries
if 'siteEntry' in site_list:
    # Get the first site entry
    first_site = site_list['siteEntry'][0]
    
    # Extract site URL and permission level
    site_url = first_site['siteUrl']
    permission_level = first_site['permissionLevel']    

    # Return the site information
    site_info = {'siteUrl': site_url, 'permissionLevel': permission_level}    
     
    #get sitemap data
    sitemap_data = webmasters_service.sitemaps().list(siteUrl=site_url).execute()
    first_sitemap = sitemap_data['sitemap'][0]
    sitemap_path = first_sitemap['path']
    # print(site_info)  
    print(sitemap_path) 

    search_analytics_data = webmasters_service.searchanalytics().query(
    siteUrl=site_url,
    body=request
    ).execute()

    # Print the output
    print("output of search",search_analytics_data)

else:
    print("No sites found")

