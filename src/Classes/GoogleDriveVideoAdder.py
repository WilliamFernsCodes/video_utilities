import json
import logging
import os
import time
from typing import List, TypedDict
import subprocess
from moviepy.editor import VideoFileClip
from undetected_chromedriver import By

from src.Classes.AssemblyAI import AssemblyAI
from src.utils import new_driver, find_element 
from models import AssemblyAIParsedTranscriptType
logger = logging.getLogger()

class AudioTranscriptType(TypedDict):
    audio_path: str
    parsed_transcript: List[AssemblyAIParsedTranscriptType]

class GoogleDriveVideoAdder:
    def __init__(
        self, directory_id: str, chrome_profile_path: str, download_path: str
    ):
        self.directory_url = (
            f"https://drive.google.com/drive/my-drive"
        )
        self.driver = new_driver(chrome_profile_path=chrome_profile_path)
        self.directory_id = directory_id
        self.downloads_path = download_path
        self.debugging = False
        self.final_assets_path = os.path.join(
            self.downloads_path, "final_assets"
        )
        os.makedirs(self.downloads_path, exist_ok=True)
        self.debugging_output_assets_path = os.path.abspath("./debugging_output_assets")

    def get_final_video(self, assembly_api_key: str):
        self._download_videos()
        self.driver.quit()
        path_to_remove = r"\home\adonis\.config\chromium\Profile 1"
        if os.path.exists(path_to_remove):
            subprocess.run(['rm', '-rf', path_to_remove], check=True)

        # self._add_videos_together(assembly_api_key)

    def _add_videos_together(self, assembly_api_key: str):
        self.__rename_and_unzip()
        all_assets_paths = self.__get_all_assets_paths();
        logger.info(f"Total number of assets: {len(all_assets_paths)}")

        remaining_assets_paths = self.__remove_unecessary_assets(all_assets_paths)
        logger.info(f"Total number of remaining assets: {len(remaining_assets_paths)}")
        video_transcripts = self._get_video_transcripts(assembly_api_key)
        final_videos = self.__shorten_transcript(video_transcripts)

    def _download_videos(self):
        params = {
            "behavior": "allow",
            "downloadPath": self.downloads_path,
        }
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        self.driver.get(self.directory_url)

        download_folder_script = f"""
            const folderContainer = document.querySelector("div[data-id='{self.directory_id}']");
            const downloadButton = folderContainer.querySelector("div[role='button'][aria-label='Download']");
            downloadButton ? downloadButton.click() : console.log('Download button not found')
        """

        self.driver.execute_script(download_folder_script)
        logger.info("Waiting for files to zip...")
        zip_timeout = 600
        while True:
            is_downloading = self.__is_downloading()
            logger.info(f"Is downloading: {is_downloading}")
            if is_downloading or not zip_timeout:
                break

            logger.info("Still unzipping...")
            time.sleep(10)
            zip_timeout -= 10

        if not zip_timeout:
            raise Exception("Zip timed out")

        logger.info("Done zipping folder. Waiting for downloads to finish...") 
        download_timeout = 600
        # while check_downloads(self.driver) and download_timeout:
        while True:
            is_downloading = self.__is_downloading()
            logger.info(f"Is downloading: {is_downloading}")
            if not is_downloading or not download_timeout:
                break

            logger.info("Still downloading...")
            time.sleep(10)
            download_timeout -= 10

        if not download_timeout:
            raise Exception("Download timed out")

        logger.info("Downloaded all zip folders successfully...")
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

        # exclude all the files that do not end with "mkv, mov, and mp4"
        files_to_include = ["mov", "mkv", "mp4"]
        include_files = []
        for path in all_assets_paths:
            if path.lower().endswith(tuple(files_to_include)):
                include_files.append(path)

        for index, path in enumerate(include_files):
            file_extension = path.split(".")[-1]

            new_path_name = os.path.join(
                self.final_assets_path,
                f"{index+1}_face_recording.{file_extension}",
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
                    self.debugging_output_assets_path, "audio_transcripts.json"
                )
                logger.info(f"Saving audio transcripts to '{audio_transcript_output_path}'...")
                with open(audio_transcript_output_path, "w") as f:
                    f.write(json.dumps(all_transcripts, indent=4))

        return all_transcripts


    def _convert_files_audio(
        self,
        file_type: str,
        file_paths: List[str],
        output_path: str
    ) -> List[str]:
        os.makedirs(output_path, exist_ok=True)
        allowed_file_types = ["mov", "mp4", "mkv"]
        if file_type not in allowed_file_types:
            raise Exception(f"File type {file_type} not allowed")

        audio_paths = []
        for file_path in file_paths:
            video = VideoFileClip(file_path)
            video_name = os.path.basename(file_path).split(".")[0]
            audio_path = os.path.join(output_path, f"{video_name}.mp3")
            video_audio = video.audio
            if not video_audio:
                raise Exception(f"Video {file_path} has no audio")

            video_audio.write_audiofile(audio_path)
            audio_paths.append(audio_path)
        return audio_paths

    def __is_downloading(self):
        if os.path.exists(self.downloads_path) and len(os.listdir(self.downloads_path)) > 0:
            # see if any of the files has a .crdownload extension
            for file in os.listdir(self.downloads_path):
                if file.endswith(".crdownload"):
                    return True
            return False
        return False

    def __shorten_transcript(self, transcripts):
        """

        """
        return
