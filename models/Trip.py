"""Module for handling trip management and operations."""

from datetime import datetime, timedelta
from utils.json_handler import load_json, save_json
from models.Route import Route
from models.Notification import Notification
from models.enums import NotificationType
from models.Reschedule import Reschedule
from models.enums import TripStatus, TripBookingStatus, OrderStatus

class Trip:
    """A class representing a trip with management capabilities."""

    def __init__(self, data):
        """Initialize a Trip instance with standardized datetime handling."""
        self.trip_id = data["tripId"]
        self.route_id = data["routeId"]
        self.start_station_id = data.get("startStationId")
        
        # Handle departure time
        departure_time = data.get("departureTime") or data.get("tripDepartureTime", "")
        self.trip_departure_time = self._standardize_datetime(departure_time)
        self.original_departure = data.get("originalDeparture", self.trip_departure_time)  # Updated this line
        
        # Calculate arrival time if not provided
        self.trip_arrival_time = self._standardize_datetime(
            data.get("tripArrivalTime") or self._calculate_arrival_time()
        )
        
        self.trip_status = data.get("tripStatus", TripStatus.SCHEDULED.value)
        self.trip_reschedule_time = self._standardize_datetime(
            data.get("tripRescheduleTime")
        )

    def _format_datetime(self, dt_str):
        """Format datetime string for display."""
        if not dt_str:
            return "N/A"
        try:
            if "T" in dt_str:  # ISO format
                dt = datetime.fromisoformat(dt_str.replace("Z", ""))
                return dt.strftime("%Y-%m-%d %H:%M")
            else:  # Just time
                return dt_str
        except ValueError:
            return dt_str

    def _standardize_datetime(self, dt_str):
        """Convert any datetime string to full ISO format."""
        if not dt_str:
            return None
            
        try:
            # Handle full ISO format
            if "T" in dt_str:
                return dt_str  # Already in ISO format
                
            # Handle date + time format (YYYY-MM-DD HH:MM)
            if "-" in dt_str and ":" in dt_str:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                return dt.isoformat()
                
            # Handle time-only format (assume current date)
            if ":" in dt_str:
                time_part = datetime.strptime(dt_str, "%H:%M").time()
                dt = datetime.combine(datetime.now().date(), time_part)
                return dt.isoformat()
                
            return None
        except ValueError:
            return None
        
    def _calculate_arrival_time(self):
        """Calculate arrival time based on route and departure time."""
        if not self.trip_departure_time:
            return None
            
        try:
            # Parse departure time (now standardized)
            departure = datetime.fromisoformat(self.trip_departure_time)
        except ValueError:
            return None
            
        # Get route duration
        duration = self._get_route_duration()
        arrival = departure + timedelta(minutes=duration)
        return arrival.isoformat()

    def _get_route_duration(self):
        """Get standard duration for route based on route ID."""
        if "ROUTE_RED" in self.route_id:
            return 20  # minutes
        elif "ROUTE_BLUE" in self.route_id or "ROUTE_GREEN" in self.route_id:
            return 45  # minutes
        return 30  # default
    
    @staticmethod
    def load_all_trips():
        """Load all trips from the JSON file."""
        data = load_json("data/trips.json")
        return [Trip(trip) for trip in data]

    @staticmethod
    def load_trips_by_route(route_color):
        """Load trips filtered by route color."""
        valid_routes = {"BLUE", "RED", "GREEN"}
        if route_color not in valid_routes:
            print("Invalid route color. Must be BLUE, RED, or GREEN.")
            return []
            
        data = load_json("data/trips.json")
        filtered = [trip for trip in data if route_color in trip["tripId"]]
        return [Trip(trip) for trip in filtered]

    @staticmethod
    def load_trips_by_route_and_date(route_color, trip_date):
        """Load trips filtered by route color and date."""
        valid_routes = {"BLUE", "RED", "GREEN"}
        if route_color not in valid_routes:
            print("Invalid route color. Must be BLUE, RED, or GREEN.")
            return []
            
        data = load_json("data/trips.json")
        filtered = []
        
        for trip in data:
            if route_color in trip["tripId"]:
                # Create a copy of the trip with the full datetime
                trip_copy = trip.copy()
                
                # Parse the time from the trip ID (format: COLOR_HHMM_STATION)
                time_part = trip["tripId"].split("_")[1]
                hours = time_part[:2]
                minutes = time_part[2:]
                
                # Combine with the selected date
                try:
                    departure_datetime = datetime.strptime(
                        f"{trip_date} {hours}:{minutes}", 
                        "%Y-%m-%d %H:%M"
                    ).isoformat()
                except ValueError:
                    continue
                
                trip_copy["departureTime"] = departure_datetime
                trip_copy["startStationId"] = trip.get("startStationId", "")
                filtered.append(trip_copy)
        
        return [Trip(trip) for trip in filtered]


    def manage_trip(self):
        """Display trip management interface and handle user input."""
        print(f"\n===== Managing Trip: {self.trip_id} =====")
        print(f"Route: {self.route_id}")
        print(f"Departure: {self.trip_departure_time}")
        print(f"Arrival: {self.trip_arrival_time}")
        print(f"Current Status: {self.trip_status}")
        
        if self.trip_reschedule_time:
            print(f"Rescheduled to: {self.trip_reschedule_time}")
        
        while True:
            print("\nActions:")
            print("1. Update Status")
            print("2. View Route Details")
            print("3. Back to Dashboard")
            
            choice = input("Select action (1-3): ").strip()
            
            if choice == "1":
                self.update_trip_status()
                break
            elif choice == "2":
                self.request_view_route_details()
            elif choice == "3":
                return
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    def update_trip_status(self):
        """Update the status of the trip with validation."""
        print("\nUpdate Trip Status:")
        status_options = [status.value for status in TripStatus]
        
        valid_transitions = {
            TripStatus.SCHEDULED.value: [
                TripStatus.STARTED.value, 
                TripStatus.CANCELLED.value, 
                TripStatus.RESCHEDULED.value
            ],
            TripStatus.RESCHEDULED.value: [
                TripStatus.STARTED.value, 
                TripStatus.CANCELLED.value
            ],
            TripStatus.STARTED.value: [TripStatus.COMPLETED.value],
            TripStatus.CANCELLED.value: [
                TripStatus.SCHEDULED.value, 
                TripStatus.RESCHEDULED.value
            ],
            TripStatus.COMPLETED.value: []
        }.get(self.trip_status, [])
        
        if not valid_transitions:
            print("This trip is already completed and cannot be modified.")
            return
        
        print("Available status changes:")
        available_options = []
        for idx, status in enumerate(status_options, 1):
            if status in valid_transitions:
                print(f"{idx}. {status}")
                available_options.append(status)
            elif status == self.trip_status:
                print(f"{idx}. {status} (current)")
        
        while True:
            choice = input("Select new status (number): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(status_options):
                selected_status = status_options[int(choice)-1]
                if (selected_status in available_options or 
                    selected_status == self.trip_status):
                    break
            print("Invalid choice. Please select from available options.")
        
        # Exit if same status selected
        if selected_status == self.trip_status:
            print("Status remains unchanged.")
            return
        
        old_status = self.trip_status
        self.trip_status = selected_status
        
        # Handle rescheduling with better error messages
        if (selected_status == TripStatus.RESCHEDULED.value or 
            (selected_status == TripStatus.SCHEDULED.value and old_status == TripStatus.CANCELLED.value)):
            
            # Improved confirmation prompt
            while True:
                reschedule = input("\nDo you want to set a new date and time for this trip? (y/n): ").strip().lower()
                if reschedule in ('y', 'n'):
                    break
                print("⚠️ Please enter 'y' for yes or 'n' for no")
            
            if reschedule == 'y':
                reschedule_instance = Reschedule(self)
                while True:
                    print("\nCurrent schedule:")
                    print(f"Departure: {self.trip_departure_time}")
                    print(f"Arrival: {self.trip_arrival_time}")
                    print("\nEnter the new date AND time in format: YYYY-MM-DD HH:MM")
                    print("Example: 2025-06-10 14:30")
                    
                    new_datetime = input("New date/time: ").strip()
                    success, message = reschedule_instance.set_new_date(new_datetime)
                    
                    if not success:
                        print(f"\n❌ Error: {message}")
                        print("Please try again with the correct format.")
                        continue
                    
                    if self.reschedule_has_time_conflict(
                        reschedule_instance.new_departure,
                        reschedule_instance.new_arrival
                    ):
                        print("\n❌ Schedule conflict detected!")
                        print("This time overlaps with another trip on the same route.")
                        print("Please choose a different time.")
                        continue
                    
                    # Confirm the change
                    print(f"\nProposed change:")
                    print(f"Old departure: {self.trip_departure_time}")
                    print(f"New departure: {reschedule_instance.new_departure}")
                    print(f"Old arrival: {self.trip_arrival_time}")
                    print(f"New arrival: {reschedule_instance.new_arrival}")
                    
                    confirm = input("\nConfirm this change? (y/n): ").strip().lower()
                    if confirm == 'y':
                        # Store the original time before updating
                        self.original_departure = self.trip_departure_time
                        self.trip_departure_time = reschedule_instance.new_departure
                        self.trip_arrival_time = reschedule_instance.new_arrival
                        self.trip_reschedule_time = reschedule_instance.new_departure
                        self.trip_status = TripStatus.RESCHEDULED.value
                        reschedule_instance.save_reschedule()
                        print("\n✅ Trip rescheduled successfully!")
                        break
                    else:
                        print("\nRescheduling cancelled by user.")
                        break
            else:
                if selected_status == TripStatus.RESCHEDULED.value:
                    self.trip_status = old_status
                    print("\n⚠️ Rescheduling cancelled - status remains unchanged.")
                    return
        
        self.save_trip()
        self.create_and_send_notification()

    def reschedule_has_time_conflict(self, new_departure, new_arrival):
        """Check if new trip time conflicts with existing trips."""
        try:
            new_start = (
                datetime.strptime(new_departure.replace("T", " "), "%Y-%m-%d %H:%M:%S")
                if "T" in new_departure
                else datetime.strptime(new_departure, "%Y-%m-%d %H:%M")
            )
            new_end = (
                datetime.strptime(new_arrival.replace("T", " "), "%Y-%m-%d %H:%M:%S")
                if "T" in new_arrival
                else datetime.strptime(new_arrival, "%Y-%m-%d %H:%M")
            )
            
            trips = Trip.load_all_trips()
            for trip in trips:
                if trip.route_id == self.route_id and trip.trip_id != self.trip_id:
                    existing_start = (
                        datetime.strptime(
                            trip.trip_departure_time.replace("T", " "),
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if "T" in trip.trip_departure_time
                        else datetime.strptime(
                            trip.trip_departure_time,
                            "%Y-%m-%d %H:%M"
                        )
                    )
                    existing_end = (
                        datetime.strptime(
                            trip.trip_arrival_time.replace("T", " "),
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if "T" in trip.trip_arrival_time
                        else datetime.strptime(
                            trip.trip_arrival_time,
                            "%Y-%m-%d %H:%M"
                        )
                    )
                    
                    buffer = timedelta(minutes=5)
                    if ((new_start < existing_end + buffer) and 
                        (new_end > existing_start - buffer)):
                        print(
                            f"Conflict with trip {trip.trip_id} "
                            f"({existing_start} to {existing_end})"
                        )
                        return True
            return False
        except ValueError as e:
            print(f"Error parsing datetime: {e}")
            return True
        
    def request_view_route_details(self):
        """Display details of the trip's route."""
        Route().view_route_details(self.route_id)

    def create_and_send_notification(self):
        """Create and send notification about trip status change."""
        notification = Notification()
        
        try:
            # Base notification content for all status changes
            status_messages = {
                TripStatus.SCHEDULED.value: f"Trip {self.trip_id} is now scheduled for {self._format_datetime(self.trip_departure_time)}",
                TripStatus.STARTED.value: f"Trip {self.trip_id} has started its journey",
                TripStatus.CANCELLED.value: f"Trip {self.trip_id} has been cancelled",
                TripStatus.COMPLETED.value: f"Trip {self.trip_id} has completed its journey",
                # In Trip.py, in the create_and_send_notification method, update the RESCHEDULED status message:
                TripStatus.RESCHEDULED.value: (
                    f"Trip {self.trip_id} has been rescheduled from "
                    f"{self._format_datetime(self.original_departure)} to "  # Changed from trip_departure_time
                    f"{self._format_datetime(self.trip_reschedule_time)}"
                )
            }
            
            # Send admin notification for all status changes
            notification.create_notification(
                status_messages.get(self.trip_status, f"Trip {self.trip_id} status changed"),
                NotificationType.SYSTEM_ALERT,
                "admin"
            )
            
            # Notify affected users for all status changes
            affected_bookings = self.get_affected_bookings()
            if affected_bookings:
                user_ids = []
                booking_ids = []
                
                for booking_info in affected_bookings:
                    user_ids.append(booking_info["user_id"])
                    booking_ids.append(booking_info["booking"]["tripBookingId"])
                
                user_messages = {
                    TripStatus.SCHEDULED.value: (
                        f"Your trip {self.trip_id} has been scheduled for "
                        f"{self._format_datetime(self.trip_departure_time)}. "
                        f"Booking ID: {', '.join(booking_ids)}"
                    ),
                    TripStatus.STARTED.value: (
                        f"Your trip {self.trip_id} has started its journey. "
                        f"Booking ID: {', '.join(booking_ids)}"
                    ),
                    TripStatus.CANCELLED.value: (  # THIS IS WHERE THE NEW MESSAGE GOES
                        f"Your trip {self.trip_id} has been cancelled by the system. "
                        f"Booking ID: {', '.join(booking_ids)}. "
                        "Refund processing will begin automatically if eligible."
                    ),
                    TripStatus.COMPLETED.value: (
                        f"Your trip {self.trip_id} has completed its journey. "
                        f"Booking ID: {', '.join(booking_ids)}"
                    ),
                    TripStatus.RESCHEDULED.value: (
                        f"Your trip {self.trip_id} has been rescheduled from "
                        f"{self._format_datetime(self.original_departure)} to "
                        f"{self._format_datetime(self.trip_reschedule_time)}. "
                        f"Booking ID: {', '.join(booking_ids)}"
                    )
                }
                
                notification.create_notification(
                    user_messages.get(self.trip_status, f"Your trip {self.trip_id} status changed"),
                    NotificationType.ORDER_UPDATE,
                    "user",
                    user_ids
                )
                
        except Exception as e:
            print(f"Error creating notifications: {e}")
            # Fallback notification if something goes wrong
            notification.create_notification(
                f"Trip {self.trip_id} status changed to {self.trip_status}",
                NotificationType.SYSTEM_ALERT,
                "admin"
            )

    def save_trip(self):
        """Save the trip data to the JSON file and update related bookings."""
        # Save trip data (existing code)
        data = load_json("data/trips.json")
        for i, trip in enumerate(data):
            if trip["tripId"] == self.trip_id:
                data[i] = {
                    "tripId": self.trip_id,
                    "routeId": self.route_id,
                    "tripDepartureTime": self.trip_departure_time,
                    "originalDeparture": self.original_departure,  # Add this line
                    "tripArrivalTime": self.trip_arrival_time,
                    "tripStatus": self.trip_status,
                    "tripRescheduleTime": self.trip_reschedule_time
                }
                break
        save_json("data/trips.json", data)
        
        # Update booking status if trip is cancelled or rescheduled
        if self.trip_status in [TripStatus.CANCELLED.value, TripStatus.RESCHEDULED.value]:
            self._update_related_bookings()

    def _update_related_bookings(self):
        """Update status of all bookings for this trip in both orders.json and tripbookings.json."""
        try:
            orders_data = load_json("data/orders.json")
            tripbookings_data = load_json("data/tripbookings.json")
            
            affected_bookings = self.get_affected_bookings()
            
            for booking_info in affected_bookings:
                user_id = booking_info["user_id"]
                booking_id = booking_info["booking"]["tripBookingId"]
                
                # Update in orders.json
                for order in orders_data.get(user_id, {}).get("orders", []):
                    if "trip_bookings" in order:
                        for booking in order["trip_bookings"]:
                            if booking["tripBookingId"] == booking_id:
                                # For admin-initiated cancellations
                                booking["bookingStatus"] = TripBookingStatus.CANCELLED.value
                                
                                # Set order status based on cancellation timing
                                departure_time = booking.get("departureTime", "")
                                try:
                                    if "T" in departure_time:
                                        dep_datetime = datetime.fromisoformat(departure_time)
                                    else:
                                        dep_datetime = datetime.combine(
                                            datetime.now().date(),
                                            datetime.strptime(departure_time, "%H:%M").time()
                                        )
                                    
                                    time_until_departure = dep_datetime - datetime.now()
                                    
                                    if time_until_departure > timedelta(hours=24):
                                        order["status"] = OrderStatus.REFUND_REQUESTED.value
                                    else:
                                        order["status"] = OrderStatus.REFUNDED_FAIL.value
                                except:
                                    order["status"] = OrderStatus.REFUNDED_FAIL.value
                                break
                
                # Update in tripbookings.json
                if user_id in tripbookings_data:
                    for booking in tripbookings_data[user_id]:
                        if booking["tripBookingId"] == booking_id:
                            booking["bookingStatus"] = TripBookingStatus.CANCELLED.value
                            break
            
            save_json("data/orders.json", orders_data)
            save_json("data/tripbookings.json", tripbookings_data)
            
        except Exception as e:
            print(f"Error updating booking statuses: {e}")
            
    def get_affected_bookings(self):
        """Get all bookings for this trip."""
        try:
            orders = load_json("data/orders.json")
            affected_bookings = []
            
            for user_id, user_data in orders.items():
                for order in user_data.get("orders", []):
                    for booking in order.get("trip_bookings", []):
                        if booking.get("tripId") == self.trip_id:
                            affected_bookings.append({
                                "user_id": user_id,
                                "booking": booking
                            })
            return affected_bookings
        except Exception as e:
            print(f"Error loading bookings: {e}")
            return []