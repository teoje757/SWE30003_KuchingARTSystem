# models/reschedule.py
from datetime import datetime, timedelta
from utils.json_handler import load_json, save_json
import uuid

class Reschedule:
    def __init__(self, trip=None):
        if trip:
            self.rescheduleId = f"RES_{trip.tripId}_{uuid.uuid4().hex[:4]}"
            self.tripId = trip.tripId
            self.originalDeparture = trip.tripDepartureTime
            self.originalArrival = trip.tripArrivalTime
            self.newDeparture = None
            self.newArrival = None
            self.status = "Pending"

    @staticmethod
    def createReschedule(trip):
        """Static factory method to create a reschedule instance."""
        return Reschedule(trip)

    @staticmethod
    def parseDatetime(dt_str):
        """Parse both 'YYYY-MM-DD HH:MM' and 'YYYY-MM-DDTHH:MM:SS' formats."""
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return None

    def setNewDate(self, new_departure):
        """Process rescheduling with flexible input formats."""
        new_date = self.parseDatetime(new_departure)
        if not new_date:
            return False, "Invalid format. Use YYYY-MM-DD HH:MM or YYYY-MM-DDTHH:MM:SS."

        original_departure = self.parseDatetime(self.originalDeparture)
        if not original_departure:
            return False, "Original trip time is invalid."

        if new_date <= datetime.now():
            return False, "New time must be in the future."

        if new_date == original_departure:
            return False, "New time must differ from the original schedule."

        original_arrival = self.parseDatetime(self.originalArrival)
        if not original_arrival:
            return False, "Original arrival time is invalid."

        duration = original_arrival - original_departure
        self.newDeparture = new_date.strftime("%Y-%m-%dT%H:%M:%S")
        self.newArrival = (new_date + duration).strftime("%Y-%m-%dT%H:%M:%S")

        self.status = "Confirmed"
        return True, "Reschedule successful."

    def saveReschedule(self):
        data = load_json("data/reschedules.json")
        data.append(self.__dict__)
        save_json("data/reschedules.json", data)