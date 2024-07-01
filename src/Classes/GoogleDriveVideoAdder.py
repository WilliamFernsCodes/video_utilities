import logging
from typing import Optional

from undetected_chromedriver import By
from src.utils import new_driver, find_element, simulate_typing
import time

logger = logging.getLogger()

class GoogleDriveVideoAdder:
    def __init__(self, directory_id: str, chrome_profile_path: str):
        self.directory_url = f"https://drive.google.com/drive/folders/{directory_id}"
        self.driver = new_driver(chrome_profile_path=chrome_profile_path)

    def add_videos_together(self):
        self.driver.get(self.directory_url)
        files_and_folders_container = find_element(self.driver, "xpath", "/html/body/div[3]/div/div[5]/div[2]/div/div/c-wiz/div/c-wiz/div[1]/c-wiz/div[2]/c-wiz/div[1]/c-wiz/c-wiz/div")
        all_children_elems = files_and_folders_container.find_elements(By.CSS_SELECTOR, "c-wiz")
        # allow download of multiple files
        logger.info(f"Total number of files and folders: {len(all_children_elems)}")
        download_function = """
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function downloadSequentially() {
    const buttons = document.querySelectorAll("div[role='button'][aria-label='Download']");
    
    for (const button of buttons) {
        await sleep(5000);
        console.log("Clicking button");
        button.click();
    }
}

downloadSequentially();
        """
        time.sleep(5000)
