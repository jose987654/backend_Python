from flask import Flask, jsonify
import data_collection  # Import your data collection functions here

app = Flask(__name__)

# Set up the Google Search Console API client
search_console_service = data_collection.setup_search_console_api("./local-env-404011-e776db327a1f.json")

@app.route('/fetch', methods=['GET'])
def fetch_search_console_data():
    search_console_data = data_collection.fetch_search_console_data(search_console_service)
    return jsonify(search_console_data)

if __name__ == '__main__':
    app.run(debug=True)
