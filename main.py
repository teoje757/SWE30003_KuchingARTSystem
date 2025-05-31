# main.py
from models.system_admin import SystemAdmin
import getpass
import bcrypt

def main():
    print("===== Admin Login =====")
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ").strip()

        admin = SystemAdmin.authenticateSystemAdmin(email, password)
        if admin:
            print(f"Login successful. Welcome, {admin.systemAdminEmail}!")
            admin.requestManageTrip()  # Single entry point
            print("Logging out...")
            return
        else:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"Invalid credentials. {remaining} attempts remaining.")

    if attempts == max_attempts:
        print("Maximum login attempts reached. System locked.")

if __name__ == "__main__":
    main()