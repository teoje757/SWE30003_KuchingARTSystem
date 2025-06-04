# main.py
from models.SystemAdmin import SystemAdmin
from models.UserService import signup
from models.User import show_main_menu
from models.AuthenticationService import AuthenticationService
import getpass

def main():
    auth_service = AuthenticationService()
    print("=== Welcome to Kuching ART Online System ===")
    
    while True:
        print("\nMain Menu:")
        print("1. Sign Up (User)")
        print("2. Log In")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ").strip()

        if choice == '1':
            signup()
        elif choice == '2':
            user = auth_service.handle_login()
            
            if user:
                if isinstance(user, SystemAdmin):
                    print(f"Admin login successful. Welcome, {user.system_admin_email}!")
                    user.request_manage_trip()
                else:
                    show_main_menu(user)
                
                # Get fresh device info for logout
                ip_address = "127.0.0.1"
                device_info = auth_service._get_device_info()
                
                # Handle logout
                user_type = "admin" if isinstance(user, SystemAdmin) else "user"
                user_id = user.system_admin_id if isinstance(user, SystemAdmin) else user["userID"]
                auth_service.handle_logout(user_id, user_type, ip_address, device_info)
                
        elif choice == '3':
            print("Exiting the system. Goodbye!")
            break
        else:
            print("Invalid option. Please select 1, 2, or 3.")

if __name__ == '__main__':
    main()