import logging
from undetected_chromedriver import By
from src.utils import new_driver, find_element 
import time
import os

logger = logging.getLogger()

class GoogleDriveVideoAdder:
    def __init__(self, directory_id: str, chrome_profile_path: str, download_path: str):
        self.directory_url = f"https://drive.google.com/drive/folders/{directory_id}"
        self.driver = new_driver(chrome_profile_path=chrome_profile_path)
        self.downloads_path = download_path

    def get_final_video(self):
        self._download_videos()
        path_to_remove = "\\home\\adonis\\.config\\chromium\\Profile 1/Default/Preferences"
        if os.path.exists(path_to_remove):
            os.remove(path_to_remove)

        self._add_videos_together()

    def _add_videos_together(self):
        self.__rename_and_unzip()
        self.__remove_zip_files()
        self.__order_video_files()

    def _download_videos(self):
        params = {
            "behavior": "allow",
            "downloadPath": self.downloads_path,
        }
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        self.driver.get(self.directory_url)
        files_and_folders_container = find_element(self.driver, "xpath", "/html/body/div[3]/div/div[5]/div[2]/div/div/c-wiz/div/c-wiz/div[1]/c-wiz/div[2]/c-wiz/div[1]/c-wiz/c-wiz/div")
        all_children_elems = files_and_folders_container.find_elements(By.CSS_SELECTOR, "c-wiz")
        # allow download of multiple files
        logger.info(f"Total number of files and folders: {len(all_children_elems)}")
        all_children_container = self.driver.find_element(By.XPATH, "/html/body/div[3]/div/div[5]/div[2]/div/div/c-wiz/div/c-wiz/div[1]/c-wiz/div[2]/c-wiz/div[1]/c-wiz/c-wiz/div")
        # get all download buttons inside the all_children_container
        all_download_buttons = all_children_container.find_elements(By.CSS_SELECTOR, "div[role='button'][aria-label='Download']")
        print(f"Total number of download buttons: {len(all_download_buttons)}")
        download_function = """
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function downloadSequentially() {
    const allChildrenContainer = document.evaluate(
      "/html/body/div[3]/div/div[5]/div[2]/div/div/c-wiz/div/c-wiz/div[1]/c-wiz/div[2]/c-wiz/div[1]/c-wiz/c-wiz/div",
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null
    ).singleNodeValue;
    const buttons = allChildrenContainer.querySelectorAll("div[role='button'][aria-label='Download']");
    
    for (const button of buttons) {
        await sleep(Math.floor(Math.random() * (10000 - 5000 + 1)) + 5000;
        console.log("Clicking button");
        button.click();
    }
}
downloadSequentially();
        """
        # execute script
        self.driver.execute_script(download_function)
        while True:
            total_downloaded_files = 0
            for file_name in os.listdir(self.downloads_path):
                if file_name.endswith(".zip"):
                    total_downloaded_files += 1

            if total_downloaded_files == len(all_download_buttons):
                logger.info(f"{total_downloaded_files}/{len(all_download_buttons)} files downloaded")
                break

            logger.info(f"{total_downloaded_files}/{len(all_download_buttons)} files downloaded. Still downloading...")
            time.sleep(10)
    def __rename_and_unzip(self):
        all_zip_paths = os.listdir(self.downloads_path)
        for download_path in all_zip_paths:
            # see if the file name first 2 characters are in the range of 1 and 31
            first_two_chars = download_path[:2]
            first_char = download_path[0]
            if (first_two_chars.isdigit() and int(first_two_chars) in range(1, 32)) or (first_char.isdigit() and not download_path[1].isdigit()):
                name_before = os.path.join(self.downloads_path, download_path)
                if first_two_chars.isdigit():
                    name_after = os.path.join(self.downloads_path, f"{first_two_chars}.zip")
                else:
                    name_after = os.path.join(self.downloads_path, f"{first_char}.zip")
                os.rename(name_before, name_after)
                # unzip folder
                os.system(f"unzip {name_after} -d {self.downloads_path}")
            else:
                os.remove(os.path.join(self.downloads_path, download_path))


    def __order_video_files(self):
        return

    def __remove_zip_files(self):
        logger.info("Removing all zip files")
        all_files = os.listdir(self.downloads_path)
        for file_name in all_files:
            if file_name.endswith(".zip"):
                logger.info(f"Removing {file_name}...")
                os.remove(os.path.join(self.downloads_path, file_name))
