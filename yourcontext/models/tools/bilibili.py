
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel
from pydantic import Field


class BilibiliVideoCodec(str, Enum):
    DASH = "DASH"
    MP4 = "MP4"


class BilibiliVideoStreamInfo(BaseModel):
    quality: int = Field(..., description="视频质量")
    width: int = Field(..., description="视频宽度")
    height: int = Field(..., description="视频高度")
    codec: str = Field(..., description="视频编码")
    urls: List[str] = Field(..., description="视频URL列表")


class BilibiliAudioStreamInfo(BaseModel):
    quality: int = Field(..., description="音频质量")
    codec: str = Field(..., description="音频编码")
    urls: List[str] = Field(..., description="音频URL列表")


class BilibiliStreamInfo(BaseModel):
    stream_type: BilibiliVideoCodec = Field(..., description="流类型")
    video_streams: list[BilibiliVideoStreamInfo] = Field(default_factory=list, description="视频流信息")
    audio_streams: list[BilibiliAudioStreamInfo] = Field(default_factory=list, description="音频流信息")


class BilibiliVideoInfo(BaseModel):
    avid: int | None = Field(None, description="AV号")
    bvid: str | None = Field(..., description="BV号")
    cid: int | None = Field(..., description="分片ID")
    title: str = Field(..., description="视频标题")
    subtitle: dict[str, Any] | None = Field(default_factory=dict, description="字幕信息")
    stream_info: BilibiliStreamInfo | None = Field(default_factory=BilibiliStreamInfo, description="视频流信息")


class BilibiliVideoContent(BaseModel):
    content: str | None = Field(None, description="视频内容")
    message: str = Field(default="", description="错误信息")
