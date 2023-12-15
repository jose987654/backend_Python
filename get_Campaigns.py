import argparse
import sys
from google.ads.googleads.client import GoogleAdsClient
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import yaml

refresh_secrets_file="./google-ads2.yaml"
script_directory = os.path.dirname(os.path.abspath(__file__))
# CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(script_directory, client_secrets_file)) 876-272-5250
REFRESH_TOKEN_FILE = os.path.abspath(os.path.join(script_directory, refresh_secrets_file))
YAML_PATH = REFRESH_TOKEN_FILE
CUSTOMER_ID = '8762725250'
# CUSTOMER_ID = '9700671588'

def get_Campaigns(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
          campaign.id,
          campaign.name
        FROM campaign
        ORDER BY campaign.id"""
    
    # List to store campaign data
    campaigns = []

    # Issues a search request using streaming.
    stream = ga_service.search_stream(customer_id=customer_id, query=query)
    # print("output",stream)
    for batch in stream:
        # for response in batch.results:
        #     print("Individual response:", response)
        for row in batch.results:
            campaign_data = {
                "id": row.campaign.id,
                "name": row.campaign.name
            }
            campaigns.append(campaign_data)
            # print(
            #     f"Campaign with ID {row.campaign.id} and name "
            #     f'"{row.campaign.name}" was found.'
            # )          

    # Check if any campaigns were found
    if campaigns:
        print("output of campaigns",campaigns)
        return {
            'campaigns': campaigns
        }
    else:
        print(f"An error occurred:")
        return {'error': 'No campaigns found'}
        # sys.exit(1)

def load_or_refresh_client():
    try:
        if os.path.exists(YAML_PATH):
            client = GoogleAdsClient.load_from_storage(YAML_PATH)
        else:
            # If credentials don't exist or are expired, generate new ones
            client = generate_client()
    except Exception as e:
        print(f"Error loading or refreshing client: {e}")
        return None

    return client

def generate_client():
    try:
        # Load the client secrets from the YAML file
        with open(YAML_PATH, 'r') as yaml_file:
            client_config = yaml.safe_load(yaml_file)

        # Initialize the Google Ads client using the client configuration
        client = GoogleAdsClient.load_from_storage(
            client_config,
            credentials=generate_credentials()
        )

        return client
    except Exception as e:
        print(f"Error generating client: {e}")
        return None

def generate_credentials():
    try:
        # Load the client secrets from the YAML file
        with open(YAML_PATH, 'r') as yaml_file:
            client_config = yaml.safe_load(yaml_file)

        # Initialize the credentials using the client configuration
        credentials = Credentials.from_authorized_user_info(
            client_config,
            scopes=['https://www.googleapis.com/auth/adwords']
        )

        # Refresh the credentials to obtain a new access token
        credentials.refresh(Request())

        # Save the updated credentials back to the YAML file
        with open(YAML_PATH, 'w') as yaml_file:
            yaml.dump(credentials.to_authorized_user_info(), yaml_file, default_flow_style=False)

        return credentials
    except Exception as e:
        print(f"Error generating credentials: {e}")
        return None

def generate_keyword_ideas(customer_id,  keyword_texts=None, max_results=None):
    client = load_or_refresh_client()
    page_url=None
    language_id = 'en'
    page_size=10
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    language_rn = client.get_service("GoogleAdsService").language_constant_path(language_id)
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.include_adult_keywords = False
    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS

    if keyword_texts:
        request.keyword_seed.keywords.extend(keyword_texts)

    if page_url:
        request.url_seed.url = page_url

    # request.page_size = page_size

    keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(request=request)
    results_list = []
    # Iterate over the results and stop after reaching max_results1
    for i, idea in enumerate(keyword_ideas):
        competition_value = idea.keyword_idea_metrics.competition.name
        result = {
            "text": idea.text,
            "avg_monthly_searches": idea.keyword_idea_metrics.avg_monthly_searches,
            "competition": competition_value
        }
        results_list.append(result)
        # print(
        #     f'Keyword idea text "{idea.text}" has '
        #     f'"{idea.keyword_idea_metrics.avg_monthly_searches}" '
        #     f'average monthly searches and "{competition_value}" '
        #     "competition.\n"
        # )        
        if i + 1 >= max_results:
            break  # Break out of the loop after reaching max_results1
    if results_list:
        # print("output of results_list",results_list)
        return {
            'Results': results_list
        }
    else:
        print(f"An error occurred:")
        return {'error': 'No keywords found'}
        # sys.exit(1)
    
# if __name__ == "__main__":
#     try:
#         generate_keyword_ideas(CUSTOMER_ID, keyword_texts=['torrents', 'seedr'],max_results=4)
#     except Exception as ex:
#         print(f"An error occurred: {ex}")
#         sys.exit(1)

# if __name__ == "__main__":
    # Set the path to your YAML configuration file
    

#     # Initialize the Google Ads API client from the YAML file
#     googleads_client = GoogleAdsClient.load_from_storage(YAML_PATH)
#     print("output of client",googleads_client)
#     try:
#         get_Campaigns(googleads_client, CUSTOMER_ID)

#     except Exception as ex:
#         print(f"An error occurred: {ex}")
#         sys.exit(1)
