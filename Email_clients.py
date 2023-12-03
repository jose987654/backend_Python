import json
import re
import os

# Define the path to the JSON file
script_directory = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.abspath(os.path.join(script_directory, "./Emails.json")) 

def read_recipient_emails():
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r') as file:
            recipients = json.load(file)
            return recipients, [entry['email'] for entry in recipients]
    else:
        return [], []

all_recipients, recipient_emails = read_recipient_emails()

# recipient_emails = ["wasswajose9@gmail.com", "wasswajose9999@gmail.com", "jacobtusiime6@gmail.com"]

def get_emails_json():
    all_recipients, recipient_emails = read_recipient_emails()
    recipient_data = []
    
    for recipient in all_recipients:
        list_status = recipient.get("status", False)
        recipient_data.append({
            "id": recipient.get("id"),
            "email": recipient.get("email"),
            "role": recipient.get("role"),
            "first_name": recipient.get("first_name"),
            "last_name": recipient.get("last_name"),
            "list_status": list_status if list_status else False,
            # Add other fields as needed
        })
    return json.dumps({"emails": recipient_emails,"all_recipients": recipient_data})

def is_valid_email(email):
    # Simple email validation using a regular expression
    pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    return bool(re.match(pattern, email))

def delete_email(email):
    if email in recipient_emails:
        recipient_emails.remove(email)
        return True
    else:
        return False

def delete_all_emails():
    recipient_emails.clear()

def update_email(old_email, new_email):
    if old_email in recipient_emails:
        index = recipient_emails.index(old_email)
        recipient_emails[index] = new_email

        return True
    else:
        return False

def add_emails(emails):
    added = 0
    messages = []

    for email in emails:
        if is_valid_email(email):
            if email not in recipient_emails:
                recipient_emails.append(email)
                added += 1
            else:
                messages.append(f"Email '{email}' already exists.")

    if added > 0:
        return {"added": added, "messages": messages}
    else:
        return {"error": "No valid emails were added."}

def write_recipient_emails(emails):
    try:
        with open(JSON_FILE_PATH, 'w') as file:
            json.dump(emails, file, indent=2)
        return {"status": "success", "message": "Recipient emails successfully written to the file."}
    except Exception as e:
        return {"status": "failure", "message": f"Error writing recipient emails to the file: {str(e)}"}

def add_email_updated(emails):
    all_recipients, recipient_emails = read_recipient_emails()   
    added = 0 
    messages = []
    
    for email in emails:
        if is_valid_email(email) and email not in [entry['email'] for entry in all_recipients]:
            new_entry = {
                'id': len(all_recipients) + 1,  # Generate a unique id
                'email': email,
                'role': 'user'  # You can set a default role or add this as a parameter
            }
            all_recipients.append(new_entry) 
            added += 1
        else:
            messages.append(f"Email '{email}' is not valid or already exists.")   

    if added > 0:
        # write_recipient_emails(recipient_emails)
        write_recipient_emails(all_recipients)
        return {"added": added, "messages": messages}
    else:
        return {"error": "No valid emails were added.","messages": messages}
    
def delete_email_updated(email):
    all_recipients, recipient_emails = read_recipient_emails()

    # Trim whitespaces from the email
    email = email.strip()

    updated_recipients = [entry for entry in all_recipients if entry['email'].strip() != email]

    if len(updated_recipients) < len(all_recipients):
        # Email was found and deleted
        write_recipient_emails(updated_recipients)
        return {"message": f"Email '{email}' deleted successfully."}
    else:
        # Email was not found
        return {"error": f"Email '{email}' not found."}



def update_email(old_email, new_email):
    all_recipients, recipient_emails = read_recipient_emails()

    for entry in all_recipients:
        if entry['email'] == old_email:
            entry['email'] = new_email

    write_recipient_emails(all_recipients)
    return True

def add_recipient(new_user):
    all_recipients, _ = read_recipient_emails()

    # Check if the email is not already in the list
    if new_user['email'] not in [entry['email'] for entry in all_recipients]:
        all_recipients.append({
            'email': new_user['email'],
            'status': new_user.get('status', True),  # Default to True if not provided
        })

        # Save the updated list to the JSON file
        with open(JSON_FILE_PATH, 'w') as file:
            json.dump(all_recipients, file, indent=2)

def update_email_status_add(email):
    all_recipients, recipient_emails = read_recipient_emails()

    for entry in all_recipients:
        if entry['email'] == email:
            entry['status'] = True

    write_recipient_emails(all_recipients)
    return True

def update_email_status_remove(email):
    all_recipients, recipient_emails = read_recipient_emails()

    for entry in all_recipients:
        if entry['email'] == email:
            entry['status'] = False

    write_recipient_emails(all_recipients)
    return True