import os
from google_auth_oauthlib.flow import InstalledAppFlow
script_directory = os.path.dirname(os.path.abspath(__file__))
client_secrets_file="./client_secret_917854844662-kib0uct1qgpmqci7od6dusa3rbvjphn7.apps.googleusercontent.com.json"
# Set up the OAuth 2.0 client ID and client secret
CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, client_secrets_file))
CLIENT_ID = '917854844662-kib0uct1qgpmqci7od6dusa3rbvjphn7.apps.googleusercontent.com'
CLIENT_SECRET = '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'
SCOPES = ['https://www.googleapis.com/auth/adwords']

# Directory to store the user's token file.
TOKEN_DIR = os.path.join(os.path.dirname(__file__), 'token')
TOKEN_PATH = os.path.join(TOKEN_DIR, 'user_token.json')


def generate_refresh_token():
    # Create the directory if it doesn't exist
    os.makedirs(TOKEN_DIR, exist_ok=True)

    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,  # Replace with your client secrets file path
        scopes=SCOPES
    )

    # Run the flow to authorize the application
    credentials = flow.run_local_server(port=0)

    # Save the credentials to the token file
    with open(TOKEN_PATH, 'w') as token_file:
        token_file.write(credentials.to_json())

    print(f"Refresh Token: {credentials.refresh_token}")
    print(f"Refresh token saved to '{TOKEN_PATH}'")

if __name__ == '__main__':
    generate_refresh_token()
