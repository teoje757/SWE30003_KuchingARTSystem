# models/TripBooking.py
import json
import os
from datetime import datetime, time
from models.Notification import Notification
from models.enums import NotificationType, TripBookingStatus
from models.PointsLedger import PointsLedger
from models.enums import OrderStatus
from models.Trip import Trip
from models.Order import Order

class TripBooking:
    def __init__(self):
        self.stations = self._load_stations()
        self.routes = self._load_routes()

    def _load_stations(self):
        """Load all stations from JSON file"""
        with open("data/stations.json", "r") as f:
            lines = json.load(f)

        all_stations = {}
        for line in lines:
            for station in line["stations"]:
                sid = station["stationId"]
                all_stations[sid] = station

        return all_stations

    def _load_routes(self):
        """Load routes from JSON file"""
        try:
            with open("data/routes.json", "r") as f:
                routes_list = json.load(f)
                return {
                    route["routeId"]: {
                        "routeName": route["routeName"],
                        "stations": route["stopsSequence"],
                        "fare": route["basePrice"]
                    }
                    for route in routes_list
                }
        except FileNotFoundError:
            return {}

    def get_all_stations(self):
        """Return list of all stations as (id, name) tuples"""
        return [(sid, s["stationName"]) for sid, s in self.stations.items()]

    def validate_connection(self, from_station, to_station):
        """Check if two stations are connected and return connection details"""
        # Check direct connection
        for route_id, route in self.routes.items():
            stations_in_route = route.get("stations", [])
            if from_station in stations_in_route and to_station in stations_in_route:
                return {
                    "type": "direct",
                    "route_name": route["routeName"],
                    "fare": route["fare"],
                    "valid": True
                }
        
        # Check interchange possibility
        for route1_id, route1 in self.routes.items():
            if from_station in route1.get("stations", []):
                for route2_id, route2 in self.routes.items():
                    if route1_id != route2_id and to_station in route2.get("stations", []):
                        common_stations = set(route1["stations"]) & set(route2["stations"])
                        if common_stations:
                            return {
                                "type": "interchange",
                                "from_route_name": route1["routeName"],
                                "to_route_name": route2["routeName"],
                                "fare": route1["fare"] + route2["fare"],
                                "valid": True
                            }
        return None

    def get_trip_details(self, station_id, trip_date):
        """Get trips that start from the given station on the given date"""
        all_trips = Trip.load_all_trips()
        matching_trips = []
        
        for trip in all_trips:
            if hasattr(trip, 'start_station_id') and trip.start_station_id == station_id:
                if trip.trip_departure_time:
                    if "T" in trip.trip_departure_time:
                        time_part = datetime.fromisoformat(trip.trip_departure_time).time()
                    else:
                        try:
                            time_part = datetime.strptime(trip.trip_departure_time, "%H:%M").time()
                        except ValueError:
                            continue
                    
                    try:
                        selected_date = datetime.strptime(trip_date, "%Y-%m-%d").date()
                        departure_datetime = datetime.combine(selected_date, time_part)
                        departure_time = departure_datetime.isoformat()
                    except ValueError:
                        continue
                    
                    matching_trips.append({
                        "tripId": trip.trip_id,
                        "routeId": trip.route_id,
                        "departureTime": departure_time,
                        "arrivalTime": trip.trip_arrival_time,
                        "status": trip.trip_status
                    })
        
        return matching_trips
    
    def display_route_map(self):
        """Display the route map showing all connections"""
        print("\n🚉 Route Map:")
        for route_id, route in self.routes.items():
            print(f"\nRoute {route_id}: {route['routeName']}")
            print("Stations: " + " → ".join(
                f"{self.stations[sid]['stationName']}" 
                for sid in route["stations"]
            ))
            print(f"Fare: RM{route['fare']:.2f}")

    def process_cancellation(self, user):
        """Main method to handle trip cancellation process"""
        user_id = user["userID"]
        order = Order(user_id)
        
        active_bookings = order.get_active_trip_bookings()
        if not active_bookings:
            return
            
        selected_booking = self._prompt_booking_selection(active_bookings)
        if not selected_booking:
            return
            
        self._execute_cancellation(order, selected_booking)

    def _prompt_booking_selection(self, active_bookings):
        """Display bookings and get user selection"""
        print("\n🧾 Your Active Trip Bookings:")
        
        # Create a list of cancellable bookings
        cancellable_bookings = []
        
        for i, booking in enumerate(active_bookings, 1):
            status = booking.get("bookingStatus", "")
            status_icon = "❌" if status == TripBookingStatus.CANCELLED.value else "✓"
            
            # Display all bookings
            print(f"{i}. {status_icon} Booking ID: {booking['tripBookingId']}")
            print(f"   Trip ID: {booking['tripId']}")
            print(f"   From: {booking['fromStationId']} → To: {booking['toStationId']}")
            print(f"   Status: {status}")
            
            # Only add to cancellable list if not cancelled
            if status != TripBookingStatus.CANCELLED.value:
                cancellable_bookings.append((i, booking))

        if not cancellable_bookings:
            print("\nNo cancellable bookings available.")
            return None

        while True:
            selection = input("\nEnter booking number to cancel (or 'cancel'): ").strip()
            if selection.lower() == 'cancel':
                print("↩️ Returning to main menu.")
                return None

            if not selection.isdigit():
                print("❌ Please enter a valid number.")
                continue

            selected_num = int(selection)
            
            # Find the booking in cancellable_bookings
            selected_booking = None
            for num, booking in cancellable_bookings:
                if num == selected_num:
                    selected_booking = booking
                    break
            
            if not selected_booking:
                print("❌ Cannot cancel an already cancelled booking. Please select a valid booking.")
                continue
                
            confirm = input(f"\nCancel booking {selected_booking['tripBookingId']}? (y/n): ").strip().lower()
            if confirm == 'y':
                return selected_booking
            elif confirm == 'n':
                return None
            else:
                print("❌ Please enter 'y' or 'n'.")

    def _display_booking_details(self, index, booking):
        """Format and display booking details"""
        try:
            dep_time = booking.get("departureTime", "")
            if "T" in dep_time:
                dep_datetime = datetime.fromisoformat(dep_time)
            else:
                dep_datetime = datetime.combine(
                    datetime.now().date(),
                    datetime.strptime(dep_time, "%H:%M").time()
                )
            
            status = booking.get("bookingStatus", "UNKNOWN")
            status_icon = "❌" if status == TripBookingStatus.CANCELLED.value else "✓"
            
            print(f"{index}. {status_icon} Booking ID: {booking['tripBookingId']}")
            print(f"   Trip ID: {booking['tripId']}")
            print(f"   Date: {dep_datetime.strftime('%Y-%m-%d')}")
            print(f"   Departure: {dep_datetime.strftime('%H:%M')}")
            print(f"   From: {booking['fromStationId']} → To: {booking['toStationId']}")
            print(f"   Status: {status}")
        except ValueError:
            print(f"{index}. [Error parsing date for booking {booking['tripBookingId']}]")

    def _execute_cancellation(self, order, booking):
        """Execute all cancellation steps"""
        notification = Notification()
        
        try:
            dep_datetime = self._parse_departure_time(booking["departureTime"])
        except ValueError:
            print("❌ Error parsing departure time")
            return

        # Delegate status updates to Order class
        order.cancel_trip_booking(booking["tripBookingId"], dep_datetime)
        
        # Display status updates
        print(f"\n📊 Status Updates:")
        print(f"- Booking Status: {TripBookingStatus.CANCELLED.value}")
        print(f"- Order Status: {OrderStatus.REFUNDED_FAIL.value if (dep_datetime - datetime.now()).total_seconds() <= 86400 else OrderStatus.REFUNDED.value}")
        
        # Handle refund notification
        self._handle_refund_notification(
            order._user_id,
            booking,
            dep_datetime,
            notification
        )

    def _parse_departure_time(self, departure_time_str):
        """Parse departure time string into datetime object"""
        try:
            return datetime.fromisoformat(departure_time_str)
        except ValueError:
            departure_time = time.fromisoformat(departure_time_str)
            return datetime.combine(datetime.now().date(), departure_time)

    def _handle_refund_notification(self, user_id, booking, dep_datetime, notification):
        """Handle refund notification based on cancellation timing"""
        if (dep_datetime - datetime.now()).total_seconds() > 86400:
            fare = booking.get("fare", 0)
            PointsLedger().earn_points(user_id, int(fare))
            
            notification.create_notification(
                f"Booking {booking['tripBookingId']} cancelled. Refund: {int(fare)} points",
                NotificationType.REFUND_STATUS,
                "user",
                user_id
            )
            print(f"💸 Refund issued: RM{fare:.2f} → {int(fare)} points added")
        else:
            notification.create_notification(
                f"Booking {booking['tripBookingId']} cancelled (no refund - within 24h)",
                NotificationType.REFUND_STATUS,
                "user",
                user_id
            )
            print("⚠️ No refund - trip departs within 24 hours")