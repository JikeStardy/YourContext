from enum import Enum
import json
import logging
from typing import Any, Dict, List, Union

import dashscope
from dashscope.audio.qwen_asr import QwenTranscription
from dashscope.api_entities.dashscope_response import TranscriptionResponse

from yourcontext.common.oss.ali import AliyunOSS
from yourcontext.config.config_manager import ConfigManager
import requests

class RespMode(str, Enum):
    FULL_JSON = "json"
    SHORT_JSON = "json"
    TEXT_ONLY = "text"
    SRT = "srt"

class ASRBailian:

    @classmethod
    def _ms_to_srt_time(cls, ms: int) -> str:
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
        total_seconds = ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @classmethod
    def convert_to_srt_format(cls, sentences: List[Dict[str, Any]]) -> str:
        srt_lines = []
        for idx, item in enumerate(sentences):
            start = cls._ms_to_srt_time(item["begin_time"])
            end = cls._ms_to_srt_time(item["end_time"])
            text = item["text"]
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")
        srt_content = "\n".join(srt_lines)
        return srt_content

    @classmethod
    def shorten_transcript(cls, sentences: List[Dict[str, Any]]) -> str:
        shortened_resp = []
        for sentence in sentences:
            shortened_resp.append({
                "begin_time": sentence["begin_time"],
                "end_time": sentence["end_time"],
                "text": sentence["text"],
            })
        return shortened_resp

    @classmethod
    def get_asr_result(cls, file_url: str, resp_mode: RespMode, model: str=None, corpus: str="") -> Union[dict, str]:
        """
        获取语音识别结果
        
        Args:
            file_url (str): 语音文件URL
            resp_mode (RespMode): 响应模式
            corpus (str, optional): 语音识别领域. Defaults to "".
        
        Returns:
            Union[dict, str]: 响应内容，根据resp_mode不同而不同
                - RespMode.FULL_JSON: 原始转录内容 (dict)
                - RespMode.SHORT_JSON: 简化后的转录内容 (dict)
                - RespMode.SRT: SRT格式文本 (纯文本, str)
        """
        logging.debug("init dashscope")
        dashscope.api_key = ConfigManager.singleton().get("YourContext.tool.aliyun_bailian.api_key")
        dashscope.base_http_api_url = ConfigManager.singleton().get("YourContext.tool.aliyun_asr.base_url")
        task = QwenTranscription.async_call(
            model=model or ConfigManager.singleton().get("YourContext.model.asr.model"),
            file_url=file_url,
            corpus={
                "text": corpus,
            },
        )
        logging.debug("wait asr task done")
        asr_output = QwenTranscription.wait(task=task).output

        match asr_output.task_status:
            case "SUCCEEDED":
                asr_result_url = asr_output.result["transcription_url"]
            case _:
                logging.error(f"ASR task failed: {asr_output}")
                raise Exception(f"ASR task failed: {asr_output}")
        
        logging.debug("retrieve asr content")
        resp = requests.get(asr_result_url, timeout=60)
        resp.raise_for_status()

        asr_result_json = resp.json()
        transcript = asr_result_json["transcripts"][0]
        sentences = transcript["sentences"]

        logging.debug("construct asr content")
        match resp_mode:
            case RespMode.SHORT_JSON:
                return cls.shorten_transcript(sentences)
            case RespMode.SRT:
                return cls.convert_to_srt_format(sentences)
            case RespMode.TEXT_ONLY:
                return transcript.text
            case _, RespMode.FULL_JSON:
                return sentences

if __name__ == "__main__":
    # asr_bailian = ASRBailian()
    logging.basicConfig(level=logging.DEBUG)
    resp = ASRBailian.get_asr_result(
        file_url=AliyunOSS().get_presign_url(object_name="BV1ppmCBVEww.mp3"),
        resp_mode=RespMode.SRT,
    )
    with open("test2.srt", "w") as f:
        f.write(resp)
