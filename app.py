from flask import Flask, jsonify, request
from threading import Thread, current_thread, enumerate
import logging
from logging.handlers import RotatingFileHandler
from Console_data import setup_search_console_api, fetch_search_console_data, schedule_report_email,fetch_search_console_errors
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from apscheduler.triggers import interval, cron
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import subprocess
from google.ads.googleads.client import GoogleAdsClient
from get_Campaigns import get_Campaigns, YAML_PATH, CUSTOMER_ID
from Email_clients import get_emails_json, delete_email,add_email_updated, delete_all_emails,delete_email_updated, update_email, add_emails,write_recipient_emails,read_recipient_emails,update_email_status_add,update_email_status_remove
import datetime
import os

from functools import wraps
from flask_cors import CORS 
from concurrent.futures import ThreadPoolExecutor
from signup import login_and_generate_token,signup_and_write_to_file,verify_jwt_token,refresh_access_token,revoke_tokens,verify_tokens,reset_password

app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


# Set up a logger for the application
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
app_logger.addHandler(handler)

logs_folder = "./app_logs"
script_directory = os.path.dirname(os.path.abspath(__file__))
log_Folder = os.path.abspath(os.path.join(script_directory, logs_folder))
os.makedirs(log_Folder, exist_ok=True)

# Configure logging for file
# file_log_handler = RotatingFileHandler(log_Folder, maxBytes=10000, backupCount=1)
# file_log_handler.setFormatter(formatter)
# app_logger.addHandler(file_log_handler)

scheduler = BackgroundScheduler()
current_interval = {"interval_seconds": 1000 * 60}
executor = ThreadPoolExecutor()
all_recipients, recipient_emails = read_recipient_emails()
# Set up the Google Search Console API client
search_console_service = setup_search_console_api("./local-env-404011-e776db327a1f.json")
# def get_current_interval():
#     return current_interval

def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Access token is missing"}), 401

        try:
            payload = verify_jwt_token(token)
            if not payload:
                return jsonify({"error": "Invalid access token"}), 401            
            return func(*args, **kwargs)

        except Exception as e:
            return jsonify({"error": str(e)}), 401

    return wrapper

def get_current_interval():
    # Submit the function to be executed in the APScheduler thread
    future = executor.submit(_get_current_interval)
    
    # Wait for the result
    result = future.result()

    return result

def _get_current_interval():
    jobs = scheduler.get_jobs()
    apscheduler_jobs = [job for job in jobs if job.name == 'default']

    if apscheduler_jobs:
        job = apscheduler_jobs[0]
        job_kwargs = job.kwargs

        if 'trigger' in job_kwargs:
            trigger = job_kwargs['trigger']

            if trigger is not None:
                if isinstance(trigger, interval.IntervalTrigger):
                    interval_seconds = trigger.interval.seconds
                    return {"interval_seconds": interval_seconds}
                elif isinstance(trigger, cron.CronTrigger):
                    return {"cron_expression": trigger.cron}

    return {"error": "No APScheduler job found or job has no trigger attribute"}

def set_scheduler_interval(new_interval):
    # Submit the function to be executed in the APScheduler thread
    future = executor.submit(_set_scheduler_interval, new_interval)
    
    # Wait for the result
    result = future.result()

    return result

def _set_scheduler_interval(new_interval):
    # Stop the current job
    job = scheduler.get_job('default')
    if job is not None:
        scheduler.remove_job('default')

    # Schedule a new job with the specified interval
    if 'minutes' in new_interval:
        scheduler.add_job(schedule_report_email, trigger='interval', minutes=new_interval['minutes'], id='default')
    elif 'hours' in new_interval:
        scheduler.add_job(schedule_report_email, trigger='interval', hours=new_interval['hours'], id='default')
    elif 'days' in new_interval:
        scheduler.add_job(schedule_report_email, trigger='interval', days=new_interval['days'], id='default')
    elif 'day_of_month' in new_interval:
        day_of_month = new_interval['day_of_month']
        cron_trigger = f'day={day_of_month}'
        scheduler.add_job(schedule_report_email, trigger=cron.CronTrigger.from_crontab(cron_trigger), id='default')
    elif 'seconds' in new_interval:
        scheduler.add_job(schedule_report_email, trigger='interval', seconds=new_interval['seconds'], id='default')
    else:
        return {"error": "Invalid interval parameter"}

    return {"message": f"Scheduler interval set to {new_interval}"}

def get_running_jobs():
    # Get a list of running jobs
    return [job.__getstate__() for job in scheduler.get_jobs()]

@app.route('/search_data', methods=['GET'])
@authenticate
def fetch_search_console_data_route():
    search_console_data = fetch_search_console_data(search_console_service)
    return jsonify(search_console_data)

@app.route('/error_data', methods=['GET'])
# @authenticate
def fetch_search_console_error_route():
    search_error_data = fetch_search_console_errors(search_console_service)
    return jsonify(search_error_data)

@app.route('/log_request', methods=['POST'])
def log_request():
    data = request.get_json()
    app.logger.info(f"Request received: {data}")
    return jsonify({'message': 'Request logged successfully'}), 200

@app.route('/get_logs', methods=['GET'])
def get_logs():
    try:
        with open(log_Folder, 'r') as log_file:
            logs = log_file.read()
        return logs
    except FileNotFoundError:
        return "Log file not found", 404

@app.route('/status', methods=['GET'])
@authenticate
def check_token_status():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({"status": 0, "message": "Token is missing in headers"}), 401

    status = verify_tokens(token)

    return jsonify({"status": status, "message": "Token is valid" if status == 1 else "Token is invalid"}), 200

@app.route('/test_auth', methods=['POST'])
@authenticate
def test_authentication():
    return jsonify({"message": "Token authentication successful!"}), 200

@app.route('/ad_data', methods=['GET'])
@authenticate
def new_route():
    ad_data = get_Campaigns(GoogleAdsClient.load_from_storage(YAML_PATH), CUSTOMER_ID)
    return jsonify(ad_data)

@app.route('/get_emails', methods=['GET'])
@authenticate
def get_emails():
    return get_emails_json()

@app.route('/delete_email', methods=['POST'])
@authenticate
def delete_one_email():
    data = request.get_json()
    email_to_delete = data.get('email', None)

    if email_to_delete:
        deleted = delete_email_updated(email_to_delete)
        return jsonify({"deleted": deleted})
    else:
        return jsonify({"error": "Missing 'email' parameter"}), 400
    
@app.route('/delete_all_emails', methods=['POST'])
@authenticate
def delete_all_emails():    
    recipient_emails = [] 
    # Clear the JSON file
    write_recipient_emails([])    
    return jsonify({"message": "All emails deleted"})

@app.route('/update_email', methods=['POST'])
@authenticate
def update_one_email():
    data = request.get_json()
    old_email = data.get('old_email', None)
    new_email = data.get('new_email', None)

    if old_email and new_email:
        updated = update_email(old_email, new_email)
        if updated:
            return jsonify({"updated": True, "message": f"Email '{old_email}' updated to '{new_email}'"})
        else:
            return jsonify({"updated": False, "error": f"Email '{old_email}' not found"}), 400
    else:
        return jsonify({"error": "Missing 'old_email' or 'new_email' parameter"}), 400

@app.route('/add_emails', methods=['POST'])
@authenticate
def add_multiple_emails():
    data = request.get_json()
    new_emails = data.get('new_emails', None)

    if new_emails:
        added = add_email_updated(new_emails)
        if added:
            return jsonify({"added": added})
        else:
            return jsonify({"error": "Invalid email or email list format"}), 400
    else:
        return jsonify({"error": "Missing 'new_emails' parameter"}), 400

@app.route('/add_Email_status', methods=['POST'])
# @authenticate
def update_email_Add():
    data = request.get_json()
    email_to_add = data.get('email', None)

    if email_to_add:
        added = update_email_status_add(email_to_add)
        return jsonify({"added": added})
    else:
        return jsonify({"error": "Missing 'email' parameter"}), 400
    
@app.route('/del_Email_status', methods=['POST'])
# @authenticate
def update_email_Remove():
    data = request.get_json()
    email_to_del = data.get('email', None)

    if email_to_del:
        deleted = update_email_status_remove(email_to_del)
        return jsonify({"deleted": deleted})
    else:
        return jsonify({"error": "Missing 'email' parameter"}), 400

@app.route('/get_scheduler_interval', methods=['GET'])
def get_scheduler_interval():
    # global current_interval
    # threads = enumerate()  
    # for thread in threads:
    #     print(f"Thread Name: {thread.name}, Thread ID: {thread.ident}")
    # running_jobs = get_running_jobs()
    # print("running_jobs found.",running_jobs)
    # print("current thread",current_thread().name)
    # if current_thread().name == 'MainThread':
    #     print("Error: get_scheduler_interval is called from the wrong thread.")
    #     return jsonify({"error": "Function should be called from the scheduler thread"}), 500

    # job = scheduler.get_job('default')
    # if job is not None:
    #     print("Existing job found.")
    # else:
    #     print("No job found. Creating a new one.")
    return jsonify(get_current_interval())

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    if not email or not password or not first_name or not last_name:
        return jsonify({"error": "First_name, Last_name, Email and password are required"}), 400
    try:
        signup_and_write_to_file(first_name,last_name,email, password)
        return jsonify({"message": "Added new user"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
   
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        result = login_and_generate_token(email, password)

        if result:
            access_token, refresh_token, role = result
            return jsonify({"access_token": access_token, "refresh_token": refresh_token, "role": role}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
     
@app.route('/refresh', methods=['POST'])
@authenticate
def refresh():
    data = request.get_json()
    refresh_token = data.get('refresh_token')

    if not refresh_token:
        return jsonify({"error": "Refresh token is required"}), 400

    new_access_token = refresh_access_token(refresh_token)

    if new_access_token:
        return jsonify({"access_token": new_access_token}), 200
    else:
        return jsonify({"error": "Failed to refresh access token"}), 401

@app.route('/emails', methods=['GET'])
def get_emails_2():
    return get_emails_json()

@app.route('/logout', methods=['POST'])
def logout():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    if revoke_tokens(user_id):
        return jsonify({"message": "User logged out successfully"}), 200
    else:
        return jsonify({"error": "Failed to log out user"}), 500

@app.route('/reset_password', methods=['POST'])
def handle_reset_password():    
    return reset_password()

@app.route('/set_scheduler_interval', methods=['POST'])
def set_scheduler_interval():
    data = request.get_json()
    new_interval = data.get('new_interval', None)

    if new_interval is not None:
        result = set_scheduler_interval(new_interval)
        return jsonify(result)
    else:
        return jsonify({"error": "Missing 'new_interval' parameter"}), 400

def run_flask_app():
    # Run the Flask app without the reloaderresult = {'message': 'This is a new route with additional functionality!'}

    # app.run(debug=True, use_reloader=False)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    # from waitress import serve
    # serve(app, host='0.0.0.0', port=5000)

def run_scheduler():
    global current_interval
    # Schedule the report email with a cron trigger for every Friday at a specific time (e.g., 10:00 AM)
    # cron_expression = '0 10 * * 5'  # Minute 0, hour 10, every day of the month, every month, only on Friday (day of week 5)
    # scheduler.add_job(schedule_report_email, trigger=cron.CronTrigger.from_crontab(cron_expression))
       
    if 'interval_seconds' in current_interval:
        scheduler.add_job(schedule_report_email, 'interval', seconds=current_interval['interval_seconds'])
    elif 'cron_expression' in current_interval:
        scheduler.add_job(schedule_report_email, trigger=cron.CronTrigger.from_crontab(current_interval['cron_expression']))
    else:
        # Use a default interval if none specified
        scheduler.add_job(schedule_report_email, 'interval', seconds= 11 * 60)

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    # Start the scheduler in a background thread
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.start()

    # Start the Flask app in the main thread
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()

    try:
        # Wait for the Flask app thread to finish
        flask_thread.join()
    except KeyboardInterrupt:
        # Handle Ctrl+C to exit the program gracefully
        pass

    # Shut down the scheduler gracefully when needed
    atexit.register(lambda: scheduler_thread._stop())
    scheduler_thread.join()
