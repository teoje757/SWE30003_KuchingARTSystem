# models/system_admin.py
import json
import bcrypt
from datetime import datetime
from utils.json_handler import load_json, save_json
from models.trip import Trip
class SystemAdmin:
    def __init__(self, admin_data):
        self.systemAdminId = admin_data["systemAdminId"]
        self.systemAdminEmail = admin_data["systemAdminEmail"]
        self.systemAdminCreatedAt = admin_data["systemAdminCreatedAt"]
        self.systemAdminLastLogin = admin_data.get("systemAdminLastLogin")

    @staticmethod
    def authenticateSystemAdmin(email, password):
        admins = load_json("data/admins.json")
        admin_data = next((a for a in admins if a["systemAdminEmail"] == email), None)
        
        if not admin_data:
            
            return None

        stored_hash = admin_data["systemAdminPassword"]
        

        # bcrypt requires bytes
        password_bytes = password.encode()
        stored_hash_bytes = stored_hash.encode()

        if bcrypt.checkpw(password_bytes, stored_hash_bytes):
            admin_data["systemAdminLastLogin"] = datetime.now().isoformat()
            save_json("data/admins.json", admins)
            return SystemAdmin(admin_data)
        else:
            return None

    def requestManageTrip(self):
        while True:
            print("\n===== Trip Management Dashboard =====")
            print("1. View All Trips")
            print("2. Filter by Route")
            print("3. Exit")
            
            choice = input("Select option (1-3): ").strip()
            
            if choice == "1":
                trips = Trip.loadAllTrips()
                if not self.selectAndManageTrip(trips):
                    continue
            elif choice == "2":
                route_filter = input("Enter route color (BLUE/RED/GREEN): ").strip().upper()
                if route_filter in {"BLUE", "RED", "GREEN"}:
                    trips = Trip.loadTripsByRoute(route_filter)
                    if not self.selectAndManageTrip(trips):
                        continue
                else:
                    print("Invalid route color. Must be BLUE, RED, or GREEN.")
            elif choice == "3":
                return  # Exit directly
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    def selectAndManageTrip(self, trips):
        if not trips:
            print("No trips found.")
            return True
            
        print("\nAvailable Trips:")
        for idx, trip in enumerate(trips, 1):
            print(f"{idx}. {trip.tripId} - {trip.tripDepartureTime} to {trip.tripArrivalTime} ({trip.tripStatus})")
        
        while True:
            choice = input("\nSelect trip (number) or '0' to cancel: ").strip()
            
            if choice == "0":
                return False  # Return to dashboard
                
            if choice.isdigit() and 1 <= int(choice) <= len(trips):
                selected_trip = trips[int(choice)-1]
                selected_trip.manageTrip()
                return True  # Operation completed
                
            print(f"Invalid selection. Please enter a number between 1 and {len(trips)} or 0 to cancel.")