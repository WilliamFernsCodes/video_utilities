import logging
from typing import List, Union
from undetected_chromedriver import By
from src.utils import new_driver, find_element
from moviepy.editor import VideoFileClip
from src.Classes.AssemblyAI import AssemblyAI
import time
import os
import json

logger = logging.getLogger()


class GoogleDriveVideoAdder:
    def __init__(
        self, directory_id: str, chrome_profile_path: str, download_path: str
    ):
        self.directory_url = (
            f"https://drive.google.com/drive/folders/{directory_id}"
        )
        self.driver = new_driver(chrome_profile_path=chrome_profile_path)
        self.downloads_path = download_path
        self.debugging = False
        self.final_assets_path = os.path.join(
            self.downloads_path, "final_assets"
        )
        os.makedirs(self.downloads_path, exist_ok=True)
        self.debugging_output_assets_path = os.path.abspath("./debugging_output_assets")

    def get_final_video(self, assembly_api_key: str):
        # self._download_videos()
        self.driver.quit()
        path_to_remove = (
            "\\home\\adonis\\.config\\chromium\\Profile 1/Default/Preferences"
        )
        if os.path.exists(path_to_remove):
            os.remove(path_to_remove)

        self._add_videos_together(assembly_api_key)

    def _add_videos_together(self, assembly_api_key: str):
        # self.__rename_and_unzip()
        # all_assets_paths = self.__get_all_assets_paths();
        # logger.info(f"Total number of assets: {len(all_assets_paths)}")

        # remaining_assets_paths = self.__remove_unecessary_assets(all_assets_paths)
        # logger.info(f"Total number of remaining assets: {len(remaining_assets_paths)}")
        video_transcripts = self._get_video_transcripts(assembly_api_key)
    def _download_videos(self):
        params = {
            "behavior": "allow",
            "downloadPath": self.downloads_path,
        }
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        self.driver.get(self.directory_url)
        files_and_folders_container = find_element(
            self.driver,
            "xpath",
            "/html/body/div[3]/div/div[5]/div[2]/div/div/c-wiz/div/c-wiz/div[1]/c-wiz/div[2]/c-wiz/div[1]/c-wiz/c-wiz/div",
        )
        all_children_elems = files_and_folders_container.find_elements(
            By.CSS_SELECTOR, "c-wiz"
        )
        # allow download of multiple files
        logger.info(
            f"Total number of files and folders: {len(all_children_elems)}"
        )
        all_children_container = self.driver.find_element(
            By.XPATH,
            "/html/body/div[3]/div/div[5]/div[2]/div/div/c-wiz/div/c-wiz/div[1]/c-wiz/div[2]/c-wiz/div[1]/c-wiz/c-wiz/div",
        )
        # get all download buttons inside the all_children_container
        all_download_buttons = all_children_container.find_elements(
            By.CSS_SELECTOR, "div[role='button'][aria-label='Download']"
        )
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
                logger.info(
                    f"{total_downloaded_files}/{len(all_download_buttons)} files downloaded"
                )
                break

            logger.info(
                f"{total_downloaded_files}/{len(all_download_buttons)} files downloaded. Still downloading..."
            )
            time.sleep(10)

        self.driver.quit()

    def __rename_and_unzip(self):
        all_zip_paths = os.listdir(self.downloads_path)
        for zip_name in all_zip_paths:
            first_two_chars = zip_name[:2]
            first_char = zip_name[0]
            zip_output_path = os.path.join(self.downloads_path, zip_name)
            if (
                first_two_chars.isdigit()
                and int(first_two_chars) in range(1, 32)
            ) or (first_char.isdigit() and not zip_name[1].isdigit()):
                logger.info("Unzipping file...")
                os.system(
                    f"unzip '{zip_output_path}' -d '{self.downloads_path}'/"
                )

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
        all_folders_path = [
            os.path.join(self.downloads_path, folder) for folder in all_folders
        ]
        all_assets_paths = []
        for path in all_folders_path:
            all_children = os.listdir(path)
            all_assets_paths.extend(
                os.path.join(path, child) for child in all_children
            )

        return all_assets_paths

    def __remove_unecessary_assets(self, all_assets_paths):
        os.makedirs(self.final_assets_path, exist_ok=True)

        for path in all_assets_paths:
            absolute_dir_path = os.path.dirname(path)
            file_name_parent_path = absolute_dir_path.split("/")[-1]
            file_extension = path.split(".")[-1]

            if path.lower().endswith(".mov"):
                new_path_name = os.path.join(
                    self.final_assets_path,
                    f"{file_name_parent_path}_face_recording.MOV",
                )
                os.rename(path, new_path_name)

            elif path.lower().endswith(".mkv") or path.lower().endswith(
                ".mp4"
            ):
                new_path_name = os.path.join(
                    self.final_assets_path,
                    f"{file_name_parent_path}_screen_recording.{file_extension}",
                )
                os.rename(path, new_path_name)

        self.__remove_extracted_folders()
        return os.listdir(self.final_assets_path)

    def __remove_extracted_folders(self):
        all_folders = os.listdir(self.downloads_path)
        exclude_folders = ["final_assets"]
        for folder in all_folders:
            if folder not in exclude_folders:
                os.system(
                    f"rm -rf '{os.path.join(self.downloads_path, folder)}'"
                )

    def _get_video_transcripts(self, assembly_api_key: str):
        final_assets_paths = os.listdir(self.final_assets_path)
        mov_files_paths: List[str] = []
        for final_assets_path in final_assets_paths:
            if final_assets_path.lower().endswith(".mov"):
                path_to_append: str = os.path.join(
                    self.final_assets_path, final_assets_path
                )
                mov_files_paths.append(path_to_append)

        audio_output_path = os.path.abspath("./video_audio")
        audio_paths = self._convert_files_audio(
            file_type="mov",
            file_paths=mov_files_paths,
            output_path=audio_output_path,
        )
        if not audio_paths:
            logger.error("No audio files found")
            return

        logger.info(f"Total number of audio files: {len(audio_paths)}")
        assembly_ai = AssemblyAI(api_key=assembly_api_key)
        all_transcripts = []
        for audio_path in audio_paths:
            parsed_transcript = assembly_ai.parse_transcript(assembly_ai.get_audio_transcription(audio_path))
            append_dict = {
                "parsed_transcript": parsed_transcript,
                "audio_path": audio_path,
            }
            all_transcripts.append(append_dict)

            if self.debugging:
                audio_transcript_output_path = os.path.join(
                    self.debugging_output_assets_path, "audio_transcripts"
                )
                logger.info(f"Saving audio transcripts to '{audio_transcript_output_path}'...")
                with open(audio_transcript_output_path, "w") as f:
                    f.write(json.dumps(all_transcripts, indent=4))


        return all_transcripts


    def _convert_files_audio(
        self, file_type: str, file_paths: List[str], output_path: str
    ) -> Union[List[str], None]:
        os.makedirs(output_path, exist_ok=True)
        allowed_file_types = ["mov", "mp4", "mkv"]
        if file_type not in allowed_file_types:
            logger.error(f"File type {file_type} not allowed")
            return None

        audio_paths = []
        for file_path in file_paths:
            video = VideoFileClip(file_path)
            video_name = os.path.basename(file_path).split(".")[0]
            audio_path = os.path.join(output_path, f"{video_name}.mp3")
            video_audio = video.audio
            if not video_audio:
                logger.error(f"Video {file_path} has no audio")
                return

            video_audio.write_audiofile(audio_path)
            audio_paths.append(audio_path)
        return audio_paths
