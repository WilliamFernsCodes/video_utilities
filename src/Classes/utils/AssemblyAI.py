import assemblyai as aai
from logging import getLogger
from typing import Union, List

logger = getLogger(__name__)
from assemblyai.types import TranscriptResponse
from models import AssemblyAIParsedTranscriptType
import json


class AssemblyAI:
    """
    Class to interact with AssemblyAI API, specifically for transcriptions
    """

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        aai.settings.api_key = api_key
        self.debugging = False
        self.parsed_transcript_path = (
            "./src/Classes/Bots/json_files/assembly_parsed_transcript.json"
        )
        self.transcript_path = (
            "./src/Classes/Bots/json_files/assembly_transcript.json"
        )

    def get_audio_transcription(
        self, audio_download_path: str
    ) -> Union[TranscriptResponse, None]:
        """
        Function to transcribe the audio, using Youtube Transcript API
        Parameters:
        - audio_dowload_path: str: The path to the downloaded audio file
        Returns Union[TranscriptResponse, None] - The transcript of the audio
        """
        logger.info("Transcribing audio...")
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_download_path)
        transcript = transcript.wait_for_completion()
        if transcript.json_response and "text" in transcript.json_response:
            logger.info(
                f"Transcript word length: {len(transcript.json_response["text"])}"
            )

            if self.debugging:
                with open(self.transcript_path, "w") as f:
                    f.write(json.dumps(transcript.json_response, indent=4))

            transcript_response: TranscriptResponse = json.loads(
                json.dumps(transcript.json_response)
            )
            return transcript_response
        else:
            logger.error("Transcription failed.")

    def parse_transcript(
        self, transcript
    ) -> List[AssemblyAIParsedTranscriptType]:
        """Function to parse transcript into full sentences."""
        logger.info("Parsing transcript...")
        all_transcript_words = self.remove_filler_words(transcript["words"])

        full_sentences_transcript: List[AssemblyAIParsedTranscriptType] = []
        current_sentence_dict: AssemblyAIParsedTranscriptType = {
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
        if self.debugging:
            with open(self.parsed_transcript_path, "w") as f:
                f.write(json.dumps(full_sentences_transcript, indent=4))

        logger.info("Transcription parsing complete.")
        return full_sentences_transcript

    def remove_filler_words(
        self, word_dicts_array: List[aai.Word]
    ) -> List[aai.Word]:
        """
        Function to remove filler words from the transcript
        Parameters:
        - word_dicts_array: List[aai.Word]: The array of word dictionaries
        Returns List[aai.Word] - The array of word dictionaries with filler words removed
        """
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
        final_word_dicts_array: List[aai.Word] = []
        for word_dict in word_dicts_array:
            if word_dict["text"] not in filler_words:
                final_word_dicts_array.append(word_dict)

        return final_word_dicts_array
