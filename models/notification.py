# models/notification.py
import datetime
from utils.json_handler import load_json, save_json
import uuid

class Notification:
    def createAdminNotification(self, content):
        """Create notification specifically for admin users"""
        notif = {
            "notificationId": str(uuid.uuid4()),
            "notificationType": "System_alert",
            "notificationStatus": "Unread",
            "notificationContent": f"[ADMIN] {content}",
            "notificationCreatedTime": datetime.datetime.now().isoformat(),
            "notificationPublishedTime": datetime.datetime.now().isoformat(),
            "recipientType": "admin"  # Special marker for admin notifications
        }
        self.saveNotification(notif)
        self.sendNotification(notif)

    def createUserNotification(self, content, user_ids):
        """Create notification for regular users"""
        notif = {
            "notificationId": str(uuid.uuid4()),
            "notificationType": "User_Notification",
            "notificationStatus": "Unread",
            "notificationContent": content,
            "notificationCreatedTime": datetime.datetime.now().isoformat(),
            "notificationPublishedTime": datetime.datetime.now().isoformat(),
            "recipientUserIds": user_ids,
            "recipientType": "user"
        }
        self.saveNotification(notif)
        self.sendNotification(notif)

    def saveNotification(self, notif):
        data = load_json("data/notifications.json")
        data.append(notif)
        save_json("data/notifications.json", data)

    def sendNotification(self, notif):
        print("\n[Notification Sent]")
        print(f"→ {notif['notificationContent']}")
        if notif.get('recipientUserIds'):
            print(f"Recipients: {len(notif['recipientUserIds'])} users")
        elif notif.get('recipientType') == 'admin':
            print("Recipient: System Administrators")