# notification.py

import datetime

class Notification:
    def __init__(self):
        self.notifications = []

    def createNotification(self, userID, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification = {
            "userID": userID,
            "message": message,
            "timestamp": timestamp
        }
        self.notifications.append(notification)
        return notification

    def sendNotification(self, notification):
        print("\n🔔 Notification")
        print(f"[{notification['timestamp']}] {notification['message']}")

    def getNotificationsForUser(self, userID):
        return [n for n in self.notifications if n["userID"] == userID]
