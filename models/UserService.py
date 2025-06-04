import json
import os
import re
import uuid

USERS_FILE = 'data/users.json'

def load_users():
    """Load users from JSON file, return dict keyed by userID."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users dict back to JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.(com)$", email)

def is_valid_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[0-9]", password)
        and re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

def is_valid_contact(contact):
    return re.fullmatch(r"60\d{9}", contact)

def signup():
    users = load_users()

    print("\n--- User Registration ---")

    # Auto-generate user ID using UUID
    userID = str(uuid.uuid4())

    userEmail = input("Enter your email (e.g. abc@example.com): ").strip()
    while not is_valid_email(userEmail):
        print("❌ Invalid email format. Must contain '@' and end with '.com'")
        userEmail = input("Enter your email again: ").strip()

    userName = input("Enter your name (e.g. John Doe): ").strip()

    userPassword = input("Enter your password: ").strip()
    while not is_valid_password(userPassword):
        print("❌ Password must be at least 8 characters, include one capital letter, one number, and one special character.")
        userPassword = input("Enter your password again: ").strip()

    userContactNumber = input("Enter your contact number (must start with 60, total 11 digits): ").strip()
    while not is_valid_contact(userContactNumber):
        print("❌ Invalid contact number. It must start with '60' and contain 11 digits total (e.g. 60123456789).")
        userContactNumber = input("Enter your contact number again: ").strip()

    new_user = {
        "userID": userID,
        "userEmail": userEmail,
        "userName": userName,
        "userPassword": userPassword,
        "userContactNumber": userContactNumber,
        "userRole": "user"
    }

    users[userID] = new_user
    save_users(users)

    print(f"✅ Account created successfully for {userName}. Your user ID is {userID}")
    return new_user

# In UserService.py
def login(email=None, password=None):
    users = load_users()

    if email is None:
        print("\n--- User Login ---")
        email = input("Enter your email: ").strip()
        password = input("Enter your password: ").strip()

    # Search for user with matching email
    for user in users.values():
        if user["userEmail"] == email and user["userPassword"] == password:
            print(f"👋 Welcome back, {user['userName']}!")
            return user

    return None