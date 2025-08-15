import uuid
import json
import logging
import requests
from threading import Thread, Lock, Event
from queue import Queue, Empty

from datetime import datetime, timezone
from ._version import __version__
from .db import db_manager

# A placeholder for the telemetry server endpoint
TELEMETRY_ENDPOINT = "https://example.com/telemetry"

class TelemetryManager:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings_manager=None):
        # The singleton pattern means __init__ is called every time,
        # so we need to prevent re-initialization.
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.settings_manager = settings_manager # This will be used to get/set consent
        self.user_id = self.get_or_create_user_id()
        self.event_queue = Queue()
        self.stop_event = Event()
        self.worker_thread = Thread(target=self._send_events, daemon=True)
        self._initialized = False

    def start(self):
        """Starts the telemetry background worker thread."""
        if not self._initialized:
            self.worker_thread.start()
            self._initialized = True
            logging.info("TelemetryManager started.")

    def stop(self):
        """Stops the telemetry background worker thread."""
        if self._initialized:
            self.stop_event.set()
            # The worker will process the remaining queue and then exit.
            logging.info("TelemetryManager stopping.")

    def get_or_create_user_id(self):
        """
        Retrieves the anonymous user ID from settings, or creates a new one.
        """
        user_id = db_manager.get_setting('telemetry_user_id')
        if not user_id:
            user_id = str(uuid.uuid4())
            db_manager.set_setting('telemetry_user_id', user_id)
            logging.info(f"Generated new telemetry user ID: {user_id}")
        return user_id

    def track_event(self, event_name, properties=None):
        """
        Adds a new event to the queue to be sent.

        :param event_name: The name of the event (e.g., "app_started").
        :param properties: A dictionary of additional data related to the event.
        """
        if not self._initialized:
            logging.warning("TelemetryManager not started. Event will not be tracked.")
            return

        # The timestamp is added here to capture when the event occurred.
        event_data = {
            "event_name": event_name,
            "properties": properties or {},
            "user_id": self.user_id,
            "app_version": __version__,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.event_queue.put(event_data)
        logging.info(f"Queued telemetry event: '{event_name}'")

    def _send_events(self):
        """
        The background worker function that sends events from the queue.
        """
        session = requests.Session() # Use a session for connection pooling

        while not self.stop_event.is_set():
            try:
                # Block and wait for the first item
                first_item = self.event_queue.get(timeout=5)

                # Once we have one item, try to get more to create a batch
                batch = [first_item]
                while len(batch) < 10: # Max batch size
                    try:
                        batch.append(self.event_queue.get_nowait())
                    except Empty:
                        break # No more items in queue

                if batch:
                    logging.info(f"Attempting to send batch of {len(batch)} events...")
                    try:
                        # In a real app, you would uncomment the following line
                        # response = session.post(TELEMETRY_ENDPOINT, json=batch, timeout=15)
                        # response.raise_for_status()
                        logging.info(f"...batch sent successfully (simulated). Payload: {json.dumps(batch, indent=2)}")
                    except requests.RequestException as e:
                        logging.error(f"Failed to send telemetry data: {e}")
                        # Simple retry: put items back in the queue.
                        # A more robust system would use a backoff strategy.
                        for item in batch:
                            self.event_queue.put(item)

            except Empty:
                # This happens if self.event_queue.get() times out. It's normal.
                continue
            except Exception as e:
                logging.error(f"Error in telemetry worker thread: {e}", exc_info=True)
                # Wait longer after an error to prevent busy-looping on persistent issues
                self.stop_event.wait(timeout=60)

        logging.info("Telemetry worker thread has stopped.")

            except Empty:
                # If the queue is empty, wait for a while
                self.stop_event.wait(timeout=30)
            except Exception as e:
                logging.error(f"Error in telemetry worker thread: {e}")
                self.stop_event.wait(timeout=60) # Wait longer after an error

        logging.info("Telemetry worker thread has stopped.")

# Global instance for easy access from anywhere in the app
telemetry_manager = TelemetryManager()
