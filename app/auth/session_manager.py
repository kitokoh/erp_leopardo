# -*- coding: utf-8 -*-
import datetime
import logging

class SessionManager:
    """
    Manages the user's session, including token, user info, and timeout.
    """
    def __init__(self, timeout_minutes=30):
        """
        Initializes the SessionManager.

        Args:
            timeout_minutes (int): The session timeout duration in minutes.
        """
        self.session_token = None
        self.user_id = None
        self.user_role = None
        self.start_time = None
        # self.timeout_seconds = timeout_minutes * 60
        self.timeout_seconds = 12 * 30 * 24 * 60 * 60 # Approx 12 months

    def start_session(self, token: str, user_id: int, user_role: str):
        """
        Starts a new session with the given user details.
        """
        self.session_token = token
        self.user_id = user_id
        self.user_role = user_role
        self.start_time = datetime.datetime.now()
        logging.info(f"Session started for user_id: {self.user_id}, role: {self.user_role}.")

    def end_session(self):
        """
        Ends the current session and clears all session data.
        """
        logging.info(f"Ending session for user_id: {self.user_id}.")
        self.session_token = None
        self.user_id = None
        self.user_role = None
        self.start_time = None

    def is_session_valid(self) -> bool:
        """
        Checks if the current session is active and has not timed out.

        Returns:
            bool: True if the session is valid, False otherwise.
        """
        if not self.session_token or not self.start_time:
            return False

        elapsed_time = datetime.datetime.now() - self.start_time
        if elapsed_time.total_seconds() > self.timeout_seconds:
            logging.warning(f"Session for user_id: {self.user_id} has expired.")
            self.end_session()
            return False

        return True

    def get_user_id(self) -> int:
        return self.user_id

    def get_user_role(self) -> str:
        return self.user_role

    def get_token(self) -> str:
        return self.session_token

    def get_session_info(self) -> dict:
        """
        Returns a dictionary containing the current session information.
        """
        if not self.is_session_valid():
            return {}
        return {
            "user_id": self.user_id,
            "user_role": self.user_role,
            "token": self.session_token
        }
