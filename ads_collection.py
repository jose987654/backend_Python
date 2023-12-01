import os
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2 import service_account
from google.ads.googleads.client import GoogleAdsClient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

client_secrets_file = "./client_secret_917854844662-kib0uct1qgpmqci7od6dusa3rbvjphn7.apps.googleusercontent.com.json"
refresh_secrets_file="./token/user_token.json"
script_directory = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, client_secrets_file))
REFRESH_TOKEN_FILE = os.path.abspath(os.path.join(script_directory, refresh_secrets_file))

# Add your Google Ads API credentials here
DEVELOPER_TOKEN = 'IsyGE1YYc-Htw_0HFk9Crw'
CLIENT_ID = '917854844662-kib0uct1qgpmqci7od6dusa3rbvjphn7.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REFRESH_TOKEN = '1//0355-GJgXQFWUCgYIARAAGAMSNwF-L9IrdePZkLjfjxuw3GCXhFBZ42tVXLYwAqmW5mI94xI7pN-xA_v89x5Ssa4xZZbrWKnFz0c'

CLIENT_ID = '917854844662-kib0uct1qgpmqci7od6dusa3rbvjphn7.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REFRESH_TOKEN_PATH = REFRESH_TOKEN_FILE
SCOPES = ['https://www.googleapis.com/auth/adwords']

def get_refresh_token():
    credentials = None

    try:
        # Load existing credentials from the refresh token file
        credentials = Credentials.from_authorized_user_file(REFRESH_TOKEN_PATH, scopes=SCOPES)

        # Check if the credentials are expired
        if credentials.expired:
            credentials.refresh(Request())
    except Exception as e:
        print(f"Error loading or refreshing credentials: {e}")

    # If credentials do not exist or are still invalid, initiate the OAuth2 flow
    if not credentials or not credentials.valid:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,  # Replace with your client secrets file path
            scopes=SCOPES
        )

        credentials = flow.run_local_server(port=0)

        # Save the refresh token to a file for future use
        with open(REFRESH_TOKEN_PATH, 'w') as token_file:
            token_file.write(credentials.to_json())

    return credentials

def main():
    credentials = get_refresh_token()

    # Now you can use the credentials to make API calls
    # For example, using Google Ads API
    from google.ads.googleads.client import GoogleAdsClient

    # client = GoogleAdsClient(credentials=credentials)
    client = GoogleAdsClient(
        credentials=credentials,
        developer_token=DEVELOPER_TOKEN,
    )

    # Your API calls go here
    customer_id = '495-308-3895'
    query = (
        f"SELECT campaign.id, campaign.name "
        f"FROM campaign WHERE campaign.status = 'ENABLED' "
        f"AND segments.date DURING LAST_7_DAYS"
    )

     # The correct attribute is 'service' instead of 'service.google_ads'
    response = client.service.google_ads.search(query=query, customer_id=customer_id)
    for row in response:
        print(row)

if __name__ == '__main__':
    main()

