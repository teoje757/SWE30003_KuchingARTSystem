"""Module for system administrator functionality and trip management."""

import bcrypt
from datetime import datetime, timedelta
from utils.json_handler import load_json, save_json
from models.Trip import Trip
from models.enums import TripStatus


class SystemAdmin:
    """A class representing a system administrator with trip management capabilities."""

    def __init__(self, admin_data):
        """Initialize a SystemAdmin instance."""
        self.system_admin_id = admin_data["systemAdminId"]
        self.system_admin_email = admin_data["systemAdminEmail"]
        self.system_admin_created_at = admin_data["systemAdminCreatedAt"]
        self.system_admin_last_login = admin_data.get("systemAdminLastLogin")

    @staticmethod
    def authenticate_system_admin(email, password):
        """Authenticate a system administrator."""
        admins = load_json("data/admins.json")
        admin_data = next(
            (a for a in admins if a["systemAdminEmail"] == email),
            None
        )
        
        if not admin_data:
            return None

        stored_hash = admin_data["systemAdminPassword"]
        password_bytes = password.encode()
        stored_hash_bytes = stored_hash.encode()

        if bcrypt.checkpw(password_bytes, stored_hash_bytes):
            admin_data["systemAdminLastLogin"] = datetime.now().isoformat()
            save_json("data/admins.json", admins)
            return SystemAdmin(admin_data)
        return None

    def request_manage_trip(self):
        """Display trip management dashboard and handle user input."""
        while True:
            print("\n===== Admin Management Dashboard =====")
            print("1. View All Trips")
            print("2. Filter by Route")
            print("3. Logout")
            
            choice = input("Select option (1-3): ").strip()
            
            if choice == "1":
                trip_date = self._get_valid_trip_date()
                if not trip_date:
                    continue
                trips = Trip.load_all_trips()
                # Create new trip objects with the selected date
                trips_with_date = []
                for trip in trips:
                    # Parse the time from the trip ID (format: COLOR_HHMM_STATION)
                    time_part = trip.trip_id.split("_")[1]
                    hours = time_part[:2]
                    minutes = time_part[2:]
                    
                    # Combine with the selected date
                    try:
                        departure_datetime = datetime.strptime(
                            f"{trip_date} {hours}:{minutes}", 
                            "%Y-%m-%d %H:%M"
                        )
                        
                        # Create a new trip data dictionary with the correct datetime
                        trip_data = {
                            "tripId": trip.trip_id,
                            "routeId": trip.route_id,
                            "departureTime": departure_datetime.isoformat(),
                            "tripStatus": trip.trip_status,
                            "startStationId": trip.start_station_id
                        }
                        
                        # Create a new Trip instance
                        new_trip = Trip(trip_data)
                        trips_with_date.append(new_trip)
                    except ValueError:
                        continue
                
                print(f"\nAvailable Trips for {trip_date}:")
                if not self.select_and_manage_trip(trips_with_date):
                    continue
                    
            elif choice == "2":
                route_filter = input(
                    "Enter route color (BLUE/RED/GREEN): "
                ).strip().upper()
                if route_filter in {"BLUE", "RED", "GREEN"}:
                    trip_date = self._get_valid_trip_date()
                    if not trip_date:
                        continue
                    trips = Trip.load_trips_by_route_and_date(route_filter, trip_date)
                    if not trips:
                        print(f"No trips found for route {route_filter} on {trip_date}")
                        continue
                    print(f"\nAvailable Trips for {route_filter} route on {trip_date}:")
                    if not self.select_and_manage_trip(trips):
                        continue
                else:
                    print("Invalid route color. Must be BLUE, RED, or GREEN.")
                    
            elif choice == "3":
                return True  # Signal to logout
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    def _get_valid_trip_date(self):
        """Get a valid trip date from user input (within 30 days)."""
        while True:
            trip_date = input(
                "Which date's trip would you like to update? (YYYY-MM-DD, within 30 days): "
            ).strip()
            
            if not trip_date:
                trip_date = datetime.now().strftime("%Y-%m-%d")
            
            try:
                parsed_date = datetime.strptime(trip_date, "%Y-%m-%d").date()
                today = datetime.now().date()
                max_date = today + timedelta(days=30)
                
                if parsed_date < today:
                    print("❌ Cannot manage trips in the past. Please enter a future date.")
                    continue
                if parsed_date > max_date:
                    print(f"❌ Cannot manage trips more than 30 days in advance. Please enter a date before {max_date.strftime('%Y-%m-%d')}.")
                    continue
                
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD format.")

    def select_and_manage_trip(self, trips):
        """Display and manage selection of trips."""
        if not trips:
            print("No trips found for the selected date.")
            return True
            
        print("\nAvailable Trips:")
        for idx, trip in enumerate(trips, 1):
            dep_time = trip.trip_departure_time
            if "T" in dep_time:  # Full datetime
                dep_time = datetime.fromisoformat(dep_time).strftime("%H:%M")
            print(
                f"{idx}. {trip.trip_id} - {dep_time} to "
                f"{trip.trip_arrival_time} ({trip.trip_status})"
            )
        
        while True:
            choice = input("\nSelect trip (number) or '0' to cancel: ").strip()
            
            if choice == "0":
                return False  # Return to dashboard
                
            if choice.isdigit() and 1 <= int(choice) <= len(trips):
                selected_trip = trips[int(choice)-1]
                selected_trip.manage_trip()
                return True  # Operation completed
                
            print(
                f"Invalid selection. Please enter a number between 1 and {len(trips)} "
                "or 0 to cancel."
            )