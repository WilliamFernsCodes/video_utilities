import unittest
import logging
from src.Classes.GoogleDriveVideoAdder import GoogleDriveVideoAdder
from dotenv import load_dotenv
import os
load_dotenv()

chrome_profile_path = os.environ.get("CHROME_PROFILE_PATH")
logger = logging.getLogger(__name__)

directory_id = "1XiXV6uBuOjJDsVoBrNLfyKdqGYUeL1YV"
download_path =  os.environ.get("DOWNLOAD_PATH") or ""

class TestGoogleDriveVideoAdder(unittest.TestCase):
    def test_add_video(self):
        if not chrome_profile_path:
            raise Exception("Chrome profile path not found")
        drive = GoogleDriveVideoAdder(directory_id=directory_id, chrome_profile_path=chrome_profile_path, download_path=download_path)
        result = drive.get_final_video()
