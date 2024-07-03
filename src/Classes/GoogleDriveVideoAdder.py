from __future__ import absolute_import
import logging
from undetected_chromedriver import By
from src.utils import new_driver, find_element 
from moviepy.editor import VideoFileClip
import time
import os

logger = logging.getLogger()

class GoogleDriveVideoAdder:
    def __init__(self, directory_id: str, chrome_profile_path: str, download_path: str):
        self.directory_url = f"https://drive.google.com/drive/folders/{directory_id}"
        self.driver = new_driver(chrome_profile_path=chrome_profile_path)
        self.downloads_path = download_path
        if not os.path.exists(download_path):
            os.mkdir(download_path)

    def get_final_video(self):
        # self._download_videos()
        path_to_remove = "\\home\\adonis\\.config\\chromium\\Profile 1/Default/Preferences"
        if os.path.exists(path_to_remove):
            os.remove(path_to_remove)

        self._add_videos_together()

    def _add_videos_together(self):
        # self.__rename_and_unzip()
        all_assets_paths = self.__get_all_assets_paths();
        logger.info(f"Total number of assets: {len(all_assets_paths)}")

        remaining_assets_paths = self.__remove_unecessary_assets(all_assets_paths)
        logger.info(f"Total number of remaining assets: {len(remaining_assets_paths)}")

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
        const sleepDuration = Math.floor(Math.random() * (10000 - 5000 + 1)) + 5000;
            console.log(`Waiting for ${Math.floor(sleepDuration / 1000)} seconds...`)
        await sleep(sleepDuration);
        console.log("Clicking button");
        button.click();
    }
}
downloadSequentially();
        """
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
        for zip_name in all_zip_paths:
            first_two_chars = zip_name[:2]
            first_char = zip_name[0]
            zip_output_path = os.path.join(self.downloads_path, zip_name)
            if (first_two_chars.isdigit() and int(first_two_chars) in range(1, 32)) or (first_char.isdigit() and not zip_name[1].isdigit()):
                logger.info("Unzipping file...")
                os.system(f"unzip '{zip_output_path}' -d '{self.downloads_path}'/")

            logger.info("Removing zip file")
            os.remove(zip_output_path)

        all_unzipped_names = os.listdir(self.downloads_path)
        for unzipped_name in all_unzipped_names:
            name_before = os.path.join(self.downloads_path, unzipped_name)
            first_two_chars = unzipped_name[:2]
            first_char = unzipped_name[0]

            if first_two_chars.isdigit():
                name_after = os.path.join(self.downloads_path, first_two_chars)
            else:
                name_after = os.path.join(self.downloads_path, first_char)

            os.rename(name_before, name_after)



    def __get_all_assets_paths(self):
        all_folders = os.listdir(self.downloads_path)
        all_folders_path = [os.path.join(self.downloads_path, folder) for folder in all_folders]
        all_assets_paths = []
        for path in all_folders_path:
            all_children = os.listdir(path)
            all_assets_paths.extend(os.path.join(path, child) for child in all_children)

        return all_assets_paths


    def __remove_unecessary_assets(self, all_assets_paths):
        final_assets_path = os.path.join(self.downloads_path , "final_assets")
        if not os.path.exists(final_assets_path):
            os.mkdir(final_assets_path)

        for path in all_assets_paths:
            absolute_dir_path = os.path.dirname(path)
            file_name_parent_path = absolute_dir_path.split("/")[-1]
            file_extension = path.split(".")[-1]

            if path.lower().endswith(".mov"):
                new_path_name = os.path.join(final_assets_path, f"{file_name_parent_path}_face_recording.MOV")
                os.rename(path, new_path_name)

            elif path.lower().endswith(".mkv") or path.lower().endswith(".mp4"):
                new_path_name = os.path.join(final_assets_path, f"{file_name_parent_path}_screen_recording.{file_extension}")
                os.rename(path, new_path_name)

        self.__remove_extracted_folders()
        return os.listdir(final_assets_path)


    def __remove_extracted_folders(self):
        all_folders = os.listdir(self.downloads_path)
        exclude_folders = ["final_assets"]
        for folder in all_folders:
            if folder not in exclude_folders:
                os.system(f"rm -rf '{os.path.join(self.downloads_path, folder)}'")
