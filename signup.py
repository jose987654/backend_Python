import json
import bcrypt
import os
import jwt
from datetime import datetime, timedelta
import secrets
from flask import Flask, jsonify, request
from Email_clients import is_valid_email,read_recipient_emails,write_recipient_emails
script_directory = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.abspath(os.path.join(script_directory, "./Emails.json")) 
secret_key = secrets.token_hex(32)
SECRET_KEY = secret_key
all_recipients, recipient_emails = read_recipient_emails()
salt = bcrypt.gensalt()

def hash_password(password):
    # Generate a salt and hash the password
    # salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def signup_and_write_to_file(first_name,last_name,email, password):
    all_recipients, recipient_emails = read_recipient_emails()
    if is_valid_email(email):
        existing_emails = [entry['email'] for entry in all_recipients]
        if email not in existing_emails:
            hashed_password = hash_password(password)
            new_user = {
                "id": len(all_recipients) + 1,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "role": "user",
                "password": hashed_password.decode('utf-8'),
    "active": True,"status":True
            }
            all_recipients.append(new_user)
            write_recipient_emails(all_recipients)
            return {"message": "Added new user"}
        else:
            raise ValueError("Email already exists")
    else:
        raise ValueError("Invalid email format")

   
def generate_jwt_token(user_id, email, role, expiration_minutes=300):
    # Generate a JWT token with user information and expiration time
    expiration_time = datetime.utcnow() + timedelta(minutes=expiration_minutes)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expiration_time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired.")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token.")
        return None

def verify_tokens(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Get the expiration time from the payload
        expiration_time = payload.get("exp")

        # Check if the expiration time is present and greater than the current time
        if expiration_time and expiration_time > datetime.utcnow().timestamp():
            return 1  # Token is valid
        else:
            return 0  # Token is expired or invalid
    except jwt.ExpiredSignatureError:
        return 0  # Token has expired
    except jwt.InvalidTokenError:
        return 0  # Invalid token

def generate_refresh_token(user_id, email, expiration_days=7):
    expiration_time = datetime.utcnow() + timedelta(days=expiration_days)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration_time
    }
    refresh_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return refresh_token    

def refresh_access_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
        # Check if the refresh token is expired or invalid, handle it accordingly
        if "exp" not in payload or payload["exp"] < datetime.utcnow():
            print("Refresh token is expired or invalid.")
            return None

        # Generate a new access token with a short expiration time
        access_token = generate_jwt_token(payload["user_id"], payload["email"], payload["role"], expiration_minutes=15)
        return access_token
    except jwt.ExpiredSignatureError:
        print("Refresh token has expired.")
        return None
    except jwt.InvalidTokenError:
        print("Invalid refresh token.")
        return None
    
def login_and_generate_token(email, password):
    all_recipients, recipient_emails = read_recipient_emails()
    existing_emails = [entry['email'] for entry in all_recipients]

    if email in existing_emails:
        print("email exits. 1")
        for user in all_recipients:
            if user["email"] == email:
                print("email exits 2")
                if user:
                    print("active user")
                    if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                        access_token = generate_jwt_token(user["id"], user["email"], user["role"])
                        refresh_token = generate_refresh_token(user["id"], user["email"])
                        return access_token, refresh_token, [user["role"], user["id"]]
                    else:
                        raise ValueError("Wrong password")
                else:
                    raise ValueError("User is not active")
    else:
        raise ValueError("Email doesn't exist")

    print("Invalid credentials.")
    return


def revoke_tokens(user_id):
    all_recipients, _ = read_recipient_emails()

    for user in all_recipients:
        if user["id"] == user_id:
            user["active"] = False
            write_recipient_emails(all_recipients)  # Update the storage with the modified user
            return True  # Tokens revoked successfully

    return False  # User not found


def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    # Check if email and new_password are provided
    if not email or not new_password:
        return jsonify({"error": "Email and new password are required"}), 400

    # Read existing users from storage
    all_recipients, _ = read_recipient_emails()

    # Find the user with the provided email
    user = next((user for user in all_recipients if user["email"] == email), None)

    if user:
        # Update the user's password
        # user["password"] = hash_password(new_password)
        user["password"] = (hash_password(new_password)).decode('utf-8')
        user["active"] = True
    
        # new_user = {
        #         "id": user["id"],
        #         "first_name": user["first_name"],
        #         "last_name": user["last_name"],
        #         "email": email,
        #         "role": "user",
        #         "password": user["password"],
        #         "active": True
        #     }
        # # Save the changes to all recipients
        # all_recipients.append(new_user)
        write_recipient_emails(all_recipients)

        return jsonify({"message": "Password reset successful"}), 200
    else:
        return jsonify({"error": "User not found"}), 404