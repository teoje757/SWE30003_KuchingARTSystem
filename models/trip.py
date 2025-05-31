# models/trip.py
import json
from utils.json_handler import load_json, save_json
from models.route import Route
from models.notification import Notification
from datetime import datetime, timedelta
from models.reschedule import Reschedule

class Trip:
    def __init__(self, data):
        self.tripId = data["tripId"]
        self.routeId = data["routeId"]
        self.tripDepartureTime = data["tripDepartureTime"]
        self.tripArrivalTime = data["tripArrivalTime"]
        self.tripStatus = data["tripStatus"]
        self.tripRescheduleTime = data.get("tripRescheduleTime")

    @staticmethod
    def loadAllTrips():
        data = load_json("data/trips.json")
        return [Trip(trip) for trip in data]

    @staticmethod
    def loadTripsByRoute(route_color):
        valid_routes = {"BLUE", "RED", "GREEN"}
        if route_color not in valid_routes:
            print("Invalid route color. Must be BLUE, RED, or GREEN.")
            return []
            
        data = load_json("data/trips.json")
        filtered = [trip for trip in data if route_color in trip["tripId"]]
        return [Trip(trip) for trip in filtered]
    
    def manageTrip(self):
        print(f"\n===== Managing Trip: {self.tripId} =====")
        print(f"Route: {self.routeId}")
        print(f"Departure: {self.tripDepartureTime}")
        print(f"Arrival: {self.tripArrivalTime}")
        print(f"Current Status: {self.tripStatus}")
        
        if self.tripRescheduleTime:
            print(f"Rescheduled to: {self.tripRescheduleTime}")
        
        while True:
            print("\nActions:")
            print("1. Update Status")
            print("2. View Route Details")
            print("3. Back to Dashboard")
            
            choice = input("Select action (1-3): ").strip()
            
            if choice == "1":
                self.updateTripStatus()
                break
            elif choice == "2":
                self.requestViewRouteDetails()
            elif choice == "3":
                return
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    def updateTripStatus(self):
        print("\nUpdate Trip Status:")
        options = ["Scheduled", "Rescheduled", "Started", "Cancelled", "Completed"]
        
        valid_transitions = {
            "Scheduled": ["Started", "Cancelled", "Rescheduled"],
            "Rescheduled": ["Started", "Cancelled"],
            "Started": ["Completed"],
            "Cancelled": ["Scheduled", "Rescheduled"],
            "Completed": []
        }.get(self.tripStatus, [])
        
        if not valid_transitions:
            print("This trip is already completed and cannot be modified.")
            return
        
        print("Available status changes:")
        available_options = []
        for idx, status in enumerate(options, 1):
            if status in valid_transitions:
                print(f"{idx}. {status}")
                available_options.append(status)
            elif status == self.tripStatus:
                print(f"{idx}. {status} (current)")
        
        while True:
            choice = input("Select new status (number): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                selected_status = options[int(choice)-1]
                if selected_status in available_options or selected_status == self.tripStatus:
                    break
            print("Invalid choice. Please select from available options.")
        
        # Exit if same status selected
        if selected_status == self.tripStatus:
            print("Status remains unchanged.")
            return
        
        old_status = self.tripStatus
        self.tripStatus = selected_status
        
        # Handle rescheduling
        if selected_status == "Rescheduled" or (selected_status == "Scheduled" and old_status == "Cancelled"):
            reschedule = input("Do you want to set a new date? (y/n): ").strip().lower()
            if reschedule == 'y':
                reschedule_instance = Reschedule(self)
                while True:
                    new_datetime = input("Enter new date AND time (YYYY-MM-DD HH:MM, e.g., 2025-06-01 14:30): ").strip()
                    success, message = reschedule_instance.setNewDate(new_datetime)
                    
                    if not success:
                        print(f"Error: {message}")
                        continue
                    
                    if self.rescheduleHasTimeConflict(reschedule_instance.newDeparture, reschedule_instance.newArrival):
                        print("Error: This time conflicts with another trip on the same route.")
                        continue
                    
                    self.tripDepartureTime = reschedule_instance.newDeparture
                    self.tripArrivalTime = reschedule_instance.newArrival
                    self.tripRescheduleTime = reschedule_instance.newDeparture
                    self.tripStatus = "Rescheduled"
                    reschedule_instance.save()
                    print("Trip rescheduled successfully.")
                    break
            else:
                if selected_status == "Rescheduled":
                    self.tripStatus = old_status
                    print("Rescheduling cancelled.")
                    return
        
        self.saveTrip()
        self.createAndSendNotification()

    def rescheduleHasTimeConflict(self, new_departure, new_arrival):
        """Check if the new time overlaps with existing trips on the same route."""
        try:
            # Parse new times (handling both formats)
            new_start = datetime.strptime(new_departure.replace("T", " "), "%Y-%m-%d %H:%M:%S") if "T" in new_departure else datetime.strptime(new_departure, "%Y-%m-%d %H:%M")
            new_end = datetime.strptime(new_arrival.replace("T", " "), "%Y-%m-%d %H:%M:%S") if "T" in new_arrival else datetime.strptime(new_arrival, "%Y-%m-%d %H:%M")
            
            trips = Trip.loadAllTrips()
            for trip in trips:
                if trip.routeId == self.routeId and trip.tripId != self.tripId:
                    # Parse existing trip times (handling both formats)
                    existing_start = datetime.strptime(trip.tripDepartureTime.replace("T", " "), "%Y-%m-%d %H:%M:%S") if "T" in trip.tripDepartureTime else datetime.strptime(trip.tripDepartureTime, "%Y-%m-%d %H:%M")
                    existing_end = datetime.strptime(trip.tripArrivalTime.replace("T", " "), "%Y-%m-%d %H:%M:%S") if "T" in trip.tripArrivalTime else datetime.strptime(trip.tripArrivalTime, "%Y-%m-%d %H:%M")
                    
                    # Check for actual overlap (with buffer time)
                    buffer = timedelta(minutes=5)  # 5-minute buffer between trips
                    if (new_start < existing_end + buffer) and (new_end > existing_start - buffer):
                        print(f"Conflict detected with trip {trip.tripId} ({existing_start} to {existing_end})")
                        return True
            return False
        except ValueError as e:
            print(f"Error parsing datetime: {e}")
            return True  # Fail-safe if parsing fails
        
    def requestViewRouteDetails(self):
        Route().viewRouteDetails(self.routeId)

    def createAndSendNotification(self):
        if self.tripStatus == "Rescheduled":
            content = f"Trip {self.tripId} has been rescheduled to {self.tripRescheduleTime}."
        elif self.tripStatus == "Cancelled":
            content = f"Trip {self.tripId} has been cancelled."
            if self.tripRescheduleTime:
                content += f" Originally rescheduled to {self.tripRescheduleTime}."
        elif self.tripStatus == "Started":
            content = f"Trip {self.tripId} has started its journey."
        elif self.tripStatus == "Completed":
            content = f"Trip {self.tripId} has completed its journey."
        else:  # Scheduled
            content = f"Trip {self.tripId} is now scheduled for {self.tripDepartureTime}."
        
        Notification().createAdminNotification(content)

    def saveTrip(self):
        data = load_json("data/trips.json")
        for i, trip in enumerate(data):
            if trip["tripId"] == self.tripId:
                data[i] = self.__dict__
                break
        save_json("data/trips.json", data)