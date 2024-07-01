import unittest
import logging
from src.Classes.GoogleDriveVideoAdder import GoogleDriveVideoAdder
from dotenv import load_dotenv
import os
import json

chrome_profile_path = os.getenv("CHROME_PROFILE_PATH")

load_dotenv()
logger = logging.getLogger(__name__)

directory_id = "1XiXV6uBuOjJDsVoBrNLfyKdqGYUeL1YV"

class TestGoogleDriveVideoAdder(unittest.TestCase):
    def test_add_video(self):
        if not chrome_profile_path:
            raise Exception("Chrome profile path not found")
        drive = GoogleDriveVideoAdder(directory_id=directory_id, chrome_profile_path=chrome_profile_path)
        result = drive.add_videos_together()
