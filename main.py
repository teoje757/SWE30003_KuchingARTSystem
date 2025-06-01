from UserService import login, signup
from User import show_main_menu

def main():
    print("=== Welcome to Kuching ART Online System ===")

    while True:
        print("""
Main Menu:
1. Sign Up
2. Log In
3. Exit
        """)
        choice = input("Enter your choice (1-3): ").strip()

        if choice == '1':
            signup()
        elif choice == '2':
            user = login()
            if user:
                show_main_menu(user)
        elif choice == '3':
            print("Exiting the system. Goodbye!")
            break
        else:
            print("Invalid option. Please select 1, 2, or 3.")

if __name__ == '__main__':
    main()
