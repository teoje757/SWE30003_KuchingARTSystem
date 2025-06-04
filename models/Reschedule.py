"""Module for handling trip rescheduling operations."""

from datetime import datetime, timedelta
from utils.json_handler import load_json, save_json
import uuid

class Reschedule:
    """A class to manage trip rescheduling operations."""

    def __init__(self, trip=None):
        """Initialize a Reschedule instance.
        
        Args:
            trip (Trip, optional): The trip to be rescheduled. Defaults to None.
        """
        if trip:
            self.reschedule_id = f"RES_{trip.trip_id}_{uuid.uuid4().hex[:4]}"
            self.trip_id = trip.trip_id
            self.original_departure = trip.trip_departure_time
            self.original_arrival = trip.trip_arrival_time
            self.new_departure = None
            self.new_arrival = None
            self.status = "Pending"

    @staticmethod
    def create_reschedule(trip):
        """Create a new reschedule instance.
        
        Args:
            trip (Trip): The trip to be rescheduled.
            
        Returns:
            Reschedule: A new Reschedule instance.
        """
        return Reschedule(trip)

    @staticmethod
    def parse_datetime(dt_str):
        """Parse datetime strings in multiple formats.
        
        Args:
            dt_str (str): Datetime string to parse.
            
        Returns:
            datetime: Parsed datetime object or None if parsing fails.
        """
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return None

    def set_new_date(self, new_departure):
        """Set new departure date and calculate corresponding arrival time.
        
        Args:
            new_departure (str): New departure time as string.
            
        Returns:
            tuple: (success: bool, message: str)
        """
        new_date = self.parse_datetime(new_departure)
        if not new_date:
            return False, "Invalid format. Use YYYY-MM-DD HH:MM or YYYY-MM-DDTHH:MM:SS."

        original_departure = self.parse_datetime(self.original_departure)
        if not original_departure:
            return False, "Original trip time is invalid."

        if new_date <= datetime.now():
            return False, "New time must be in the future."

        if new_date == original_departure:
            return False, "New time must differ from the original schedule."

        original_arrival = self.parse_datetime(self.original_arrival)
        if not original_arrival:
            return False, "Original arrival time is invalid."

        duration = original_arrival - original_departure
        self.new_departure = new_date.strftime("%Y-%m-%dT%H:%M:%S")
        self.new_arrival = (new_date + duration).strftime("%Y-%m-%dT%H:%M:%S")

        self.status = "Confirmed"
        return True, "Reschedule successful."

    def save_reschedule(self):
        """Save the reschedule data to JSON file."""
        data = load_json("data/reschedules.json")
        data.append(self.__dict__)
        save_json("data/reschedules.json", data)