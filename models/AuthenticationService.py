import json
import os
from datetime import datetime, timedelta
from models.enums import AuthenticationServiceStatus
from utils.json_handler import load_json, save_json
import getpass
import platform
import socket

class AuthenticationService:
    def __init__(self):
        self.service_file = "data/auth_service_logs.json"
        self.lock_file = "data/account_locks.json"
        self.max_attempts = 3
        self.lock_duration = timedelta(minutes=5)  # 5 minute lock
        self._initialize_files()

    def _initialize_files(self):
        for file in [self.service_file, self.lock_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump([], f)

    def _log_auth_attempt(self, auth_data):
        logs = load_json(self.service_file)
        logs.append(auth_data)
        save_json(self.service_file, logs)

    def _check_account_lock(self, email):
        locks = load_json(self.lock_file)
        now = datetime.now()
        
        for lock in locks:
            if lock["email"] == email:
                lock_time = datetime.fromisoformat(lock["lockTime"])
                if now < lock_time + self.lock_duration:
                    remaining = (lock_time + self.lock_duration - now).seconds // 60
                    return True, remaining
                else:
                    # Remove expired lock
                    locks.remove(lock)
                    save_json(self.lock_file, locks)
                    return False, 0
        return False, 0

    def _add_account_lock(self, email):
        locks = load_json(self.lock_file)
        locks.append({
            "email": email,
            "lockTime": datetime.now().isoformat()
        })
        save_json(self.lock_file, locks)

    def _get_failed_attempts(self, email, within_minutes=15):
        logs = load_json(self.service_file)
        now = datetime.now()
        cutoff = now - timedelta(minutes=within_minutes)
        
        failed_attempts = [
            log for log in logs 
            if log.get("email") == email 
            and log.get("authenticationServiceStatus") == AuthenticationServiceStatus.FAILED.value
            and datetime.fromisoformat(log["authenticationServiceTime"]) > cutoff
        ]
        return len(failed_attempts)

    def authenticate_user(self, email, password, ip_address, device_info):
        """Central authentication method with account locking"""
        from models.SystemAdmin import SystemAdmin
        from models.UserService import login as user_login
        
        # Check if account is locked
        is_locked, remaining = self._check_account_lock(email)
        if is_locked:
            print(f"Account locked. Please try again in {remaining} minutes.")
            return None, AuthenticationServiceStatus.LOCKED

        auth_data = {
            "email": email,
            "authenticationServiceTime": datetime.now().isoformat(),
            "authenticationServiceIpAddress": ip_address,
            "authenticationServiceDeviceInfo": device_info,
            "authenticationServiceStatus": AuthenticationServiceStatus.FAILED.value
        }

        # First try admin authentication
        admin = SystemAdmin.authenticate_system_admin(email, password)
        if admin:
            auth_data.update({
                "authenticationServiceStatus": AuthenticationServiceStatus.SUCCESS.value,
                "userType": "admin",
                "userId": admin.system_admin_id
            })
            self._log_auth_attempt(auth_data)
            return admin, AuthenticationServiceStatus.SUCCESS

        # Then try user authentication
        user = user_login(email, password)
        if user:
            auth_data.update({
                "authenticationServiceStatus": AuthenticationServiceStatus.SUCCESS.value,
                "userType": "user",
                "userId": user["userID"]
            })
            self._log_auth_attempt(auth_data)
            return user, AuthenticationServiceStatus.SUCCESS

        # If both fail, log the failed attempt
        self._log_auth_attempt(auth_data)
        
        # Check if we should lock the account
        failed_attempts = self._get_failed_attempts(email)
        if failed_attempts >= self.max_attempts:  # Changed from >= self.max_attempts - 1
            self._add_account_lock(email)
            print("Too many failed attempts. Account locked for 5 minutes.")
            return None, AuthenticationServiceStatus.LOCKED
        
        remaining_attempts = self.max_attempts - failed_attempts  # Removed the -1
        print(f"Invalid credentials. {remaining_attempts} attempts remaining.")
        return None, AuthenticationServiceStatus.FAILED

    def handle_login(self):
        """Handles the complete login flow"""
        print("\n===== Login =====")
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ").strip()
        
        ip_address = "127.0.0.1"  # Replace with actual IP detection
        device_info = self._get_device_info()
        
        user, status = self.authenticate_user(
            email, password, 
            ip_address, device_info
        )
        
        if status == AuthenticationServiceStatus.SUCCESS:
            return user
        return None

    def _get_device_info(self):
        """Get basic device information for auth logging"""
        return {
            "os": platform.system(),
            "hostname": socket.gethostname()
        }

    def handle_logout(self, user_id, user_type, ip_address, device_info):
        """Handles the complete logout flow"""
        auth_data = {
            "userId": user_id,
            "userType": user_type,
            "authenticationServiceTime": datetime.now().isoformat(),
            "authenticationServiceIpAddress": ip_address,
            "authenticationServiceDeviceInfo": device_info,
            "authenticationServiceStatus": "LOGOUT"
        }
        self._log_auth_attempt(auth_data)
        print("Logout successful. Session terminated.")