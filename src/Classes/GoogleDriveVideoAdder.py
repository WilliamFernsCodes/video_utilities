import logging
from typing import Optional
from src.utils import new_driver, find_element, simulate_typing
import time

logger = logging.getLogger()

class GoogleDriveVideoAdder:
    def __init__(self, directory_id: str, chrome_profile_path: str):
        self.directory_url = f"https://drive.google.com/drive/folders/{directory_id}"
        self.driver = new_driver(chrome_profile_path=chrome_profile_path)

    def add_videos_together(self):
        self.driver.get(self.directory_url)
        time.sleep(5000)
