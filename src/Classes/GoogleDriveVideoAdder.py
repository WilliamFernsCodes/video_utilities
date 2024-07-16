import json
import logging
import os
import time
from typing import List, Optional, TypedDict
import subprocess
from moviepy.editor import VideoFileClip
import re

from src.Classes.utils.AssemblyAI import AssemblyAI
from src.utils import get_timestamp, new_driver, get_path_size_mb
from models import AssemblyAIParsedTranscriptType, FileType

logger = logging.getLogger()

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL")


class AudioTranscriptType(TypedDict):
    audio_path: str
    parsed_transcript: List[AssemblyAIParsedTranscriptType]


class DriveVideoEditor:
    def __init__(
        self, directory_id: str, chrome_profile_path: str, download_path: str
    ):
        self.directory_url = f"https://drive.google.com/drive/my-drive"
        self.directory_id = directory_id
        self.downloads_path = download_path
        self.debugging = False
        self.final_assets_path = os.path.join(
            self.downloads_path, "final_assets"
        )
        os.makedirs(self.downloads_path, exist_ok=True)
        self.debugging_output_assets_path = os.path.abspath(
            "./debugging_output_assets"
        )
        self.chrome_profile_path = chrome_profile_path


class GoogleDriveVideoAdder(DriveVideoEditor):
    """Class to concatenate all my videos together, along with editing them automatically"""

    def __init__(
        self, directory_id: str, chrome_profile_path: str, download_path: str
    ):
        super().__init__(directory_id, chrome_profile_path, download_path)

    def get_final_video(self, assembly_api_key: str):
        # self._download_videos()
        path_to_remove = r"\home\adonis\.config\chromium\Profile 1"
        if os.path.exists(path_to_remove):
            subprocess.run(["rm", "-rf", path_to_remove], check=True)

        self._add_videos_together(assembly_api_key)

    def _add_videos_together(self, assembly_api_key: str):
        # self.__rename_and_unzip()
        all_assets_paths = self.__get_all_assets_paths()
        logger.info(f"Total number of assets: {len(all_assets_paths)}")

        remaining_assets_paths = self.join_videos_together(all_assets_paths)
        # logger.info(f"Total number of remaining assets: {len(remaining_assets_paths)}")
        # video_transcripts = self._get_video_transcripts(assembly_api_key)
        # final_videos = self.__shorten_transcript(video_transcripts)
        #

    def _download_videos(self):
        driver = new_driver(chrome_profile_path=self.chrome_profile_path)
        params = {
            "behavior": "allow",
            "downloadPath": self.downloads_path,
        }
        driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        driver.get(self.directory_url)

        download_folder_script = f"""
            const folderContainer = document.querySelector("div[data-id='{self.directory_id}']");
            const downloadButton = folderContainer.querySelector("div[role='button'][aria-label='Download']");
            downloadButton ? downloadButton.click() : console.log('Download button not found')
        """

        driver.execute_script(download_folder_script)
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
        # while check_downloads(driver) and download_timeout:
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
        driver.quit()

    def __rename_and_unzip(self):
        all_zip_paths = os.listdir(self.downloads_path)
        for index, zip_name in enumerate(all_zip_paths):
            zip_path = os.path.join(self.downloads_path, zip_name)
            output_path = os.path.join(self.downloads_path, f"{index+1}")
            os.system(f"unzip '{zip_path}' -d '{output_path}'")

        downloads_children = os.listdir(self.downloads_path)
        # remove all the zip files
        for child in downloads_children:
            child_path = os.path.join(self.downloads_path, child)
            if child_path.endswith(".zip"):
                os.remove(child_path)
            else:
                # move the content out of the folder, into the downloads directory
                folder_children_paths = [
                    os.path.join(child_path, child)
                    for child in os.listdir(child_path)
                ]
                all_folder_children_folders_paths = []
                planned_destination_paths = []
                for folder_child_path in folder_children_paths:
                    folders_in_folder_child_path_paths = [
                        os.path.join(folder_child_path, folder_name)
                        for folder_name in os.listdir(folder_child_path)
                    ]
                    planned_destination_paths.extend(
                        [
                            os.path.join(self.downloads_path, folder_name)
                            for folder_name in os.listdir(folder_child_path)
                        ]
                    )
                    all_folder_children_folders_paths.extend(
                        folders_in_folder_child_path_paths
                    )

                files_to_move = []

                for index, planned_path in enumerate(
                    planned_destination_paths
                ):
                    current_path = all_folder_children_folders_paths[index]
                    if os.path.exists(planned_path):
                        # move all the files inside the current path to the already existing path
                        move_commands = [
                            f"mv '{os.path.join(current_path, file_name)}' '{planned_path}'"
                            for file_name in os.listdir(current_path)
                        ]
                        os.system(" && ".join(move_commands))

                        # remove the current path folder
                        os.system(f"rm -rf {current_path}")
                    else:
                        files_to_move.append(f"'{current_path}'")

                # move all the files out of the folder, inside the downloads path
                for file in files_to_move:
                    move_cmd = f"mv {file} {self.downloads_path}"
                    os.system(move_cmd)
                # delete the child_path
                os.system(f"rm -rf {child_path}")

    def __get_all_assets_paths(self):
        all_folders_paths = [
            os.path.join(self.downloads_path, folder)
            for folder in os.listdir(self.downloads_path) if folder != "final_assets"
        ]

        all_assets_paths = []
        for path in all_folders_paths:
            all_children = os.listdir(path)
            all_assets_paths.extend(
                os.path.join(path, child) for child in all_children
            )

        return all_assets_paths

    def join_videos_together(self, all_assets_paths) -> List[str]:
        """Join all the videos together from the same date and return the joined videos paths in the correct order"""
        os.system(f"rm -rf {self.final_assets_path}")
        os.makedirs(self.final_assets_path)
        ordered_video_dict_list = [
            sorted(
                array,
                key=lambda x: get_path_size_mb(x["file_path"]),
                reverse=True,
            )
            for array in self.__order_video_paths(all_assets_paths)
        ]
        ordered_final_video_output_paths: List[str] = []

        for ordered_video_path_array in ordered_video_dict_list:
            output_video_name = "_".join(
                [
                    str(item)
                    for item in ordered_video_path_array[0]["date_month_year"]
                ]
            )
            joined_path = self.__get_video_relative_path(
                output_video_name=output_video_name
            )
            ordered_final_video_output_paths.append(joined_path)
            self.join_videos(
                videos_paths_array=[
                    self.__get_video_relative_path(
                        video_full_path=dict["file_path"]
                    )
                    for dict in ordered_video_path_array
                ],
                video_output_path=joined_path,
            )

        # remove all of the folders in the downloads directory, except the final_assets.
        self.__remove_extracted_folders()

        return ordered_final_video_output_paths

    def join_videos(
        self, videos_paths_array: List[str], video_output_path: str
    ) -> bool:
        if len(videos_paths_array) == 1:
            os.system(f"mv '{videos_paths_array[0]}' '{video_output_path}'")
            return True
        try:
            # Prepare the ffmpeg command
            logger.info(f"Joining {len(videos_paths_array)} videos together.")
            command = ["ffmpeg", "-f", "concat"]
            for path in videos_paths_array:
                command.extend(
                    [
                        "-i",
                        f'"{path}"',
                    ]
                )
            command.extend(
                [
                    "-vcodec",
                    "copy",
                    "-acodec",
                    "copy",
                    video_output_path,
                ]
            )

            subprocess.run(command)

            return True
        except Exception as e:
            logger.error(f"Error joining videos: {e}")
            return False

    def __remove_extracted_folders(self):
        all_folders = os.listdir(self.downloads_path)
        exclude_folders = ["final_assets"]
        for folder in all_folders:
            if folder not in exclude_folders:
                os.system(
                    f"rm -rf '{os.path.join(self.downloads_path, folder)}'"
                )

    def _get_video_transcripts(self, assembly_api_key: str):
        final_assets_paths = [
            os.path.join(self.final_assets_path, path)
            for path in os.listdir(self.final_assets_path)
        ]

        audio_output_path = os.path.abspath("./video_audio")
        audio_paths = self._convert_files_audio(
            file_type="mov",
            file_paths=final_assets_paths,
            output_path=audio_output_path,
        )
        if not audio_paths:
            logger.error("No audio files found")
            return

        logger.info(f"Total number of audio files: {len(audio_paths)}")
        assembly_ai = AssemblyAI(api_key=assembly_api_key)
        all_transcripts = []
        for audio_path in audio_paths:
            parsed_transcript = assembly_ai.parse_transcript(
                assembly_ai.get_audio_transcription(audio_path)
            )
            append_dict = {
                "parsed_transcript": parsed_transcript,
                "audio_path": audio_path,
            }
            all_transcripts.append(append_dict)

            if self.debugging:
                audio_transcript_output_path = os.path.join(
                    self.debugging_output_assets_path, "audio_transcripts.json"
                )
                logger.info(
                    f"Saving audio transcripts to '{audio_transcript_output_path}'..."
                )
                with open(audio_transcript_output_path, "w") as f:
                    f.write(json.dumps(all_transcripts, indent=4))

        return all_transcripts

    def _convert_files_audio(
        self, file_type: str, file_paths: List[str], output_path: str
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
        if (
            os.path.exists(self.downloads_path)
            and len(os.listdir(self.downloads_path)) > 0
        ):
            # see if any of the files has a .crdownload extension
            for file in os.listdir(self.downloads_path):
                if file.endswith(".crdownload"):
                    return True
            return False
        return False

    def __order_video_paths(
        self, all_assets_paths: List[str]
    ) -> List[List[FileType]]:
        """Filter out all the unnecessary paths and order them to be from oldest to newest."""
        face_recording_files = [
            path
            for path in all_assets_paths
            if path.lower().split(".")[-1] == "mov"
        ]

        # the order of how the video will be edited:
        # 1. oldest to newest
        #  - start with mov video
        # - if there is a mp4 or mkv video on the same date, use that then.

        all_folders = [
            path.split("/")[-2].replace(" ", "")
            for path in face_recording_files
        ]
        regex = re.compile(r"(\d{1,2})([A-Za-z]+)(\d{4})")
        folders_date_month_year = []
        for folder_name in all_folders:
            match = regex.match(folder_name)
            if match:
                groups = match.groups()
                if not all([isinstance(group, str) for group in groups]):
                    raise Exception(f"Matched item/s are not string type.")

                if len(groups) != 3:
                    raise Exception(
                        f"Matched groups length is not three. Make sure '{folder_name}' folder has a year, month and date."
                    )
                groups = [group.lower() for group in groups]
                folders_date_month_year.append(groups)
                logger.info(
                    f"Folder {folder_name}. Date: {match.group(1)}, Month: {match.group(2)}. Year: {match.group(3)}"
                )
            else:
                raise Exception(
                    f"Folder {folder_name} is not in correct format."
                )

        # Objective: Order the files from the oldest to newest date. All files in same folder (same date), must be in the same list. The final result must be a list of lists
        # How to do it:
        # get all the files with the same folders grouped together.

        grouped_paths = {}
        for index, file_path in enumerate(face_recording_files):
            date_month_year = folders_date_month_year[index]
            date = int(date_month_year[0])
            month = date_month_year[1]
            year = int(date_month_year[2])
            key = "_".join(date_month_year)

            timestamp = get_timestamp(month=month, date=date, year=year)
            if grouped_paths.get(key):
                grouped_paths[key].append(
                    {
                        "file_path": file_path,
                        "date_month_year": date_month_year,
                        "timestamp": timestamp,
                    }
                )
            else:
                grouped_paths[key] = [
                    {
                        "file_path": file_path,
                        "date_month_year": [date, month, year],
                        "timestamp": get_timestamp(
                            month=month, date=date, year=year
                        ),
                    }
                ]
        dict_values: List[List[FileType]] = sorted(
            list(grouped_paths.values()), key=lambda x: x[0]["timestamp"]
        )
        return dict_values

    def __get_video_relative_path(
        self,
        video_full_path: Optional[str] = None,
        output_video_name: Optional[str] = None,
    ):
        """Helper function to convert the video paths to relative paths."""
        if output_video_name:
            return (
                "."
                + f"{self.final_assets_path}/{output_video_name}.MOV".split(
                    "/video_utilities"
                )[-1]
            )
        else:
            if not video_full_path:
                raise Exception("video_full_path is required.")
            else:
                return "." + video_full_path.split("/video_utilities")[-1]


class GoogleDriveVideoEditorUtils(DriveVideoEditor):
    def __init__(
        self, directory_id: str, chrome_profile_path: str, download_path: str
    ):
        super().__init__(directory_id, chrome_profile_path, download_path)
