import assemblyai as aai
from logging import getLogger

from undetected_chromedriver import re

logger = getLogger(__name__)


class AssemblyAI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        aai.settings.api_key = api_key
        self.debugging = False

    def get_video_transcription(self, video_path: str):
        logger.info("Transcribing video...")
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(video_path)
        transcript = transcript.wait_for_completion()
        if transcript.json_response and "text" in transcript.json_response:
            logger.info(
                f"Transcript word length: {len(transcript.json_response["text"])}"
            )

            return transcript.json_response
        else:
            logger.error("Transcription failed.")
            return {}

    def parse_transcript(self, transcript):
        """Function to parse transcript into full sentences."""
        logger.info("Parsing transcript...")
        all_transcript_words = self.remove_filler_words(transcript["words"])

        full_sentences_transcript = []
        current_sentence_dict = {
            "sentence": "",
            "start_time": 0,
            "end_time": 0,
            "speaker": "",
        }

        for word_dict in all_transcript_words:
            current_sentence_dict["sentence"] += word_dict["text"] + " "
            if (
                word_dict["text"][0].isupper()
                and not current_sentence_dict["start_time"]
            ):
                current_sentence_dict["start_time"] = word_dict["start"]
                current_sentence_dict["speaker"] = word_dict["speaker"]

            if current_sentence_dict["sentence"].strip()[-1] in [
                "?",
                "!",
                ".",
            ]:
                current_sentence_dict["end_time"] = word_dict["end"]
                current_sentence_dict["sentence"] = current_sentence_dict[
                    "sentence"
                ].strip()
                full_sentences_transcript.append(current_sentence_dict)
                current_sentence_dict = {
                    "sentence": "",
                    "start_time": 0,
                    "end_time": 0,
                    "speaker": "",
                }

        logger.info(
            f"Full sentences transcript length: {len(full_sentences_transcript)}"
        )

        logger.info("Transcription parsing complete.")
        return full_sentences_transcript

    def remove_filler_words(self, word_dicts_array):
        filler_words = [
            "um",
            "uh",
            "ah",
            "literally",
            "uh-huh",
            "oh",
            "uh-oh",
            "hmm",
        ]
        final_word_dicts_array = []
        for word_dict in word_dicts_array:
            if not word_dict["text"] in filler_words:
                final_word_dicts_array.append(word_dict)

        return final_word_dicts_array
