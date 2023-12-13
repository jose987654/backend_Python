import argparse
import sys
from google.ads.googleads.client import GoogleAdsClient
import os

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


# if __name__ == "__main__":
#     # Set the path to your YAML configuration file
    

#     # Initialize the Google Ads API client from the YAML file
#     googleads_client = GoogleAdsClient.load_from_storage(YAML_PATH)
#     print("output of client",googleads_client)
#     try:
#         get_Campaigns(googleads_client, CUSTOMER_ID)

#     except Exception as ex:
#         print(f"An error occurred: {ex}")
#         sys.exit(1)
