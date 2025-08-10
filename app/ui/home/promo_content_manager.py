# -*- coding: utf-8 -*-
import json
import os
import random
import logging

class PromoContentManager:
    def __init__(self, messages_file="promo_messages.json"):
        # Construct the full path to the messages file relative to this file's directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.messages_path = os.path.join(base_dir, messages_file)
        self.messages = []
        self.load_messages()

    def load_messages(self):
        """Loads promotional messages from the JSON file."""
        try:
            if os.path.exists(self.messages_path):
                with open(self.messages_path, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f)
                logging.info(f"Successfully loaded {len(self.messages)} promotional messages from {self.messages_path}")
            else:
                logging.warning(f"Promotional messages file not found: {self.messages_path}. No messages loaded.")
                self.messages = []
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from {self.messages_path}. No messages loaded.")
            self.messages = []
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading messages: {e}")
            self.messages = []

    def get_random_message(self):
        """Returns a random promotional message from the loaded list."""
        if not self.messages:
            return None
        return random.choice(self.messages)

    def get_all_messages(self):
        """Returns all loaded promotional messages."""
        return self.messages

if __name__ == '__main__':
    # Test basic functionality
    logging.basicConfig(level=logging.INFO)

    # Create a dummy promo_messages.json for testing if it doesn't exist
    dummy_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "promo_messages.json")
    if not os.path.exists(dummy_file_path):
        print(f"Creating dummy {dummy_file_path} for testing.")
        dummy_data = [
            {"title": "Test Title 1", "body": "This is a test body 1."},
            {"title": "Test Title 2", "body": "This is another test body 2."}
        ]
        with open(dummy_file_path, 'w', encoding='utf-8') as f:
            json.dump(dummy_data, f, indent=4)

    manager = PromoContentManager()

    print("\nAll Messages:")
    all_msgs = manager.get_all_messages()
    if all_msgs:
        for msg in all_msgs:
            print(f"- Title: {msg.get('title')}, Body: {msg.get('body')}")
    else:
        print("No messages loaded.")

    print("\nRandom Message:")
    random_msg = manager.get_random_message()
    if random_msg:
        print(f"- Title: {random_msg.get('title')}, Body: {random_msg.get('body')}")
    else:
        print("No message to select.")

    # Clean up dummy file if we created it
    # if os.path.exists(dummy_file_path) and "Test Title 1" in str(dummy_data):
    #     print(f"Removing dummy {dummy_file_path}.")
    #     os.remove(dummy_file_path)
