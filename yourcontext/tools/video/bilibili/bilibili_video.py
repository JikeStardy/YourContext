import logging
from typing import List, Union
import requests
import json
import re
import sys
import os
from langchain.tools import tool
from urllib.parse import urlparse, parse_qs

from yourcontext.common.http.http_helper import download_temp_file
from yourcontext.common.oss.ali import AliyunOSS
from yourcontext.config import ConfigManager
from yourcontext.models.asr import ASRBailian, RespMode
from yourcontext.models.tools.bilibili import BilibiliAudioStreamInfo, BilibiliStreamInfo, BilibiliVideoCodec, BilibiliVideoContent, BilibiliVideoInfo, BilibiliVideoStreamInfo

class BilibiliVideo:
    def __init__(self, sessdata=None):
        """
        初始化B站视频提取器
        
        Args:
            sessdata (str): B站登录凭证，用于获取更高清晰度的视频流和字幕
        """
        self.sessdata = sessdata
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        })
        
        # 如果提供了SESSDATA，则添加到Cookie中
        if self.sessdata:
            self.session.cookies.set('SESSDATA', self.sessdata)
    
    def get_bvid_from_url(self, url):
        """
        从URL中提取BV号
        
        Args:
            url (str): B站视频URL
            
        Returns:
            str: BV号
        """
        # 匹配BV号的正则表达式
        bvid_pattern = r'BV[0-9A-Za-z]+'
        match = re.search(bvid_pattern, url)
        if match:
            return match.group(0)
        return None
    
    def get_avid_from_url(self, url):
        """
        从URL中提取AV号
        
        Args:
            url (str): B站视频URL
            
        Returns:
            str: AV号
        """
        # 匹配AV号的正则表达式
        avid_pattern = r'av(\d+)'
        match = re.search(avid_pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def get_cid_from_url(self, url):
        """
        从URL中提取CID（如果有的话）
        
        Args:
            url (str): B站视频URL
            
        Returns:
            str: CID或None
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 'p' in query_params:
            return query_params['p'][0]
        return None
    
    def get_video_info(self, avid=None, bvid=None, cid=None):
        """
        获取视频基本信息，包括字幕信息
        
        Args:
            avid (str): AV号
            bvid (str): BV号
            cid (str): CID（分P ID）
            
        Returns:
            dict: 视频信息
        """
        # 如果没有提供CID，需要先获取视频的CID
        if not cid:
            # 使用API获取视频信息
            if bvid:
                info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            elif avid:
                info_url = f"https://api.bilibili.com/x/web-interface/view?aid={avid}"
            else:
                raise ValueError("必须提供avid或bvid")
            
            try:
                response = self.session.get(info_url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == 0:
                    # 获取第一个分P的CID
                    cid = data["data"]["pages"][0]["cid"]
                    # 获取字幕信息
                    subtitle_info = data["data"].get("subtitle", {})
                    return {
                        "avid": data["data"]["aid"],
                        "bvid": data["data"]["bvid"],
                        "cid": cid,
                        "title": data["data"]["title"],
                        "subtitle": subtitle_info
                    }
                else:
                    raise Exception(f"获取视频信息失败: {data.get('message', '未知错误')}")
            except Exception as e:
                raise Exception(f"获取视频信息时出错: {str(e)}")
        else:
            # 如果提供了CID，需要获取视频的其他信息
            if bvid:
                info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            elif avid:
                info_url = f"https://api.bilibili.com/x/web-interface/view?aid={avid}"
            else:
                raise ValueError("必须提供avid或bvid")
            
            try:
                response = self.session.get(info_url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == 0:
                    # 获取字幕信息
                    subtitle_info = data["data"].get("subtitle", {})
                    return {
                        "avid": data["data"]["aid"],
                        "bvid": data["data"]["bvid"],
                        "cid": cid,
                        "title": data["data"]["title"],
                        "subtitle": subtitle_info
                    }
                else:
                    raise Exception(f"获取视频信息失败: {data.get('message', '未知错误')}")
            except Exception as e:
                raise Exception(f"获取视频信息时出错: {str(e)}")
    
    def get_player_info(self, avid=None, bvid=None, cid=None):
        """
        获取播放器信息，包括字幕信息
        
        Args:
            avid (str): AV号
            bvid (str): BV号
            cid (str): CID（分P ID）
            
        Returns:
            dict: 播放器信息
        """
        if not cid:
            # 先获取视频信息以获得CID
            video_info = self.get_video_info(avid=avid, bvid=bvid)
            cid = video_info["cid"]
            
        # 如果没有avid或bvid，从视频信息中获取
        if not avid and not bvid:
            video_info = self.get_video_info(cid=cid)
            avid = video_info["avid"]
        
        # 使用API获取播放器信息
        if bvid:
            player_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        else:
            player_url = f"https://api.bilibili.com/x/player/v2?aid={avid}&cid={cid}"
        
        try:
            response = self.session.get(player_url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                return data["data"]
            else:
                raise Exception(f"获取播放器信息失败: {data.get('message', '未知错误')}")
        except Exception as e:
            raise Exception(f"获取播放器信息时出错: {str(e)}")
    
    def extract_video_stream_info_from_dash(self, dash_info) -> BilibiliStreamInfo:
        video_streams = dash_info.get("video", [])
        audio_streams = dash_info.get("audio", [])
        result: BilibiliStreamInfo = BilibiliStreamInfo(stream_type=BilibiliVideoCodec.DASH)
        
        logging.info(f"找到 {len(video_streams)} 个视频流和 {len(audio_streams)} 个音频流")
        
        # 提取视频流链接
        video_urls: List[BilibiliVideoStreamInfo] = []
        for stream in video_streams:
            video_urls.append(BilibiliVideoStreamInfo(
                quality=stream.get("id"),
                width=stream.get("width"),
                height=stream.get("height"),
                codec=stream.get("codecs"),
                urls=[stream.get("baseUrl")]+stream.get("backupUrl", []),
            ))
        
        # 提取音频流链接
        audio_urls: List[BilibiliAudioStreamInfo] = []
        for stream in audio_streams:
            audio_urls.append(BilibiliAudioStreamInfo(
                quality=stream.get("id"),
                codec=stream.get("codecs"),
                urls=[stream.get("baseUrl")]+stream.get("backupUrl", []),
            ))
        
        result.video_streams = video_urls
        result.audio_streams = audio_urls

        return result

    def extract_video_stream_info_from_durl(self, durl_info) -> BilibiliStreamInfo:
        result: BilibiliStreamInfo = BilibiliStreamInfo(stream_type=BilibiliVideoCodec.MP4)
        video_urls: List[BilibiliVideoStreamInfo] = []
            
        for stream in durl_info:
            video_urls.append(BilibiliVideoStreamInfo(
                order=stream.get("order"),
                length=stream.get("length"),
                size=stream.get("size"),
                urls=[stream.get("url")]+stream.get("backup_url", []),
            ))
        
        result.video_streams = video_urls

        return result

    def get_video_info_with_stream_info(self, avid=None, bvid=None, cid=None, quality=64, fnval=4048) -> BilibiliVideoInfo:
        """
        获取视频流URL
        
        Args:
            avid (str): AV号
            bvid (str): BV号
            cid (str): CID（分P ID）
            quality (int): 视频清晰度代码，默认64（720P）
            fnval (int): 视频流格式标识，默认4048（DASH格式，所有可用视频流）
            
        Returns:
            dict: 视频流信息
        """
        if not cid:
            # 先获取视频信息以获得CID
            video_info = self.get_video_info(avid=avid, bvid=bvid)
            cid = video_info["cid"]
            
        # 如果没有avid或bvid，从视频信息中获取
        if not avid and not bvid:
            video_info = self.get_video_info(cid=cid)
            avid = video_info["avid"]
        
        # 使用API获取视频流URL
        # 注意：这里使用的是web端的API，需要登录才能获取高清晰度视频
        if bvid:
            play_url = f"https://api.bilibili.com/x/player/wbi/playurl?bvid={bvid}&cid={cid}&qn={quality}&fnval={fnval}&fnver=0&fourk=1"
        else:
            play_url = f"https://api.bilibili.com/x/player/wbi/playurl?avid={avid}&cid={cid}&qn={quality}&fnval={fnval}&fnver=0&fourk=1"
        
        try:
            response = self.session.get(play_url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                player_data = data["data"]
                if "dash" in player_data:
                    stream_info = self.extract_video_stream_info_from_dash(player_data["dash"])
                elif "durl" in player_data:
                    stream_info = self.extract_video_stream_info_from_durl(player_data["durl"])
                return BilibiliVideoInfo(
                    avid=avid,
                    bvid=bvid,
                    cid=cid,
                    title=video_info["title"],
                    subtitle=video_info["subtitle"],
                    stream_info=stream_info
                )
            else:
                raise Exception(f"获取视频流URL失败: {data.get('message', '未知错误')}")
        except Exception as e:
            logging.error(f"获取视频流URL时出错: {str(e)}")
            raise Exception(f"获取视频流URL时出错: {str(e)}")

    @tool("get_bilibili_video_content")
    @staticmethod
    def get_video_content(url: str=None, avid: int=None, bvid: str=None, need_timestamp: bool=False) -> BilibiliVideoContent:
        """
        retrieve video content from bilibili (an online video platform)
        
        Args:
            url (str): the url from "bilibili.com"
            avid (str): a string starts with "AV"
            bvid (str): a string starts with "BV"
            need_timestamp (bool): True for returning video content in srt format; False for plaintext without timestamp
            
        Returns:
            BilibiliVideoContent: the video content
            - content (str): the video content in srt format (if need_timestamp is True) or plaintext format (if need_timestamp is False)
            - message (str): the message if any error occurred
        """
        return BilibiliVideo.get_video_content_pipeline(url=url, avid=avid, bvid=bvid, need_timestamp=need_timestamp)

    @staticmethod
    def get_video_content_pipeline(url: str, avid: int=None, bvid: str=None, quality: int=16, fnval: int=4048, need_timestamp: bool=False) -> BilibiliVideoContent:
        # 实例化BilibiliVideo
        bili_client = BilibiliVideo(sessdata=ConfigManager.singleton().get("YourContext.tool.bilibili.sessdata"))

        # 从URL中提取参数
        if url:
            if not bvid:
                bvid = bili_client.get_bvid_from_url(url)
        
        # 获取视频信息
        video_info = bili_client.get_video_info(avid=avid, bvid=bvid)
        logging.info(f"视频标题: {video_info['title']}")
        logging.info(f"AV号: {video_info['avid']}, BV号: {video_info['bvid']}, CID: {video_info['cid']}")
        
        # 获取完整视频信息
        video_info = bili_client.get_video_info_with_stream_info(
            avid=avid, 
            bvid=bvid, 
            quality=16
        )

        match video_info.stream_info.stream_type:
            case BilibiliVideoCodec.DASH:
                audio_list = video_info.stream_info.audio_streams[0].urls
            case BilibiliVideoCodec.MP4:
                # audio = video_info.stream_info.audio_streams[-1].url
                return BilibiliVideoContent(
                    message="当前暂不支持MP4格式视频"
                )
            case _:
                return BilibiliVideoContent(
                    message="无法提取视频内容"
                )

        # 下载音频到tmp
        for audio in audio_list:
            audio_file_path = download_temp_file(audio)
            if os.path.exists(audio_file_path):
                break
        logging.debug(f"下载音频到tmp: {audio_file_path}")
        
        try:
            object_name = f"{bvid}.mp3"
            # 上传音频到oss
            logging.debug(f"上传音频到oss: {object_name}")
            ali_oss = AliyunOSS()
            logging.debug(ali_oss.get_presign_url(object_name))
            ali_oss.upload_file(audio_file_path, object_name)
            # 获取asr结果
            logging.debug("获取asr结果 ...")
            asr_result = ASRBailian.get_asr_result(
                file_url=ali_oss.get_presign_url(object_name),
                resp_mode=RespMode.SRT if need_timestamp else RespMode.TEXT_ONLY
            )
            # 组装返回数据
            logging.debug("组装返回数据 ...")
            result = BilibiliVideoContent(
                content=asr_result,
                message="成功获取视频内容"
            )
            return result
        except Exception as e:
            logging.debug(f"获取视频内容时出错: {e}", exc_info=True)
            return BilibiliVideoContent(
                message=f"获取视频内容时出错: {str(e)}"
            )
        finally:
            # 删除音频文件
            logging.debug(f"删除音频文件: {audio_file_path}")
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)

