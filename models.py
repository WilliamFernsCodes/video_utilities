from typing import TypedDict, Optional

class AssemblyAIParsedTranscriptType(TypedDict):
    sentence: str
    start_time: int
    end_time: int

class FileType(TypedDict):
    file_path: str
    date_month_year: str
    timestamp: int
