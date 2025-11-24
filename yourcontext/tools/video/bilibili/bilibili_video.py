#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili视频流和字幕提取工具
用于提取B站视频的字幕或视频流下载链接
"""

import requests
import json
import re
import sys
import os
from urllib.parse import urlparse, parse_qs

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
    
    def get_video_stream_url(self, avid=None, bvid=None, cid=None, quality=64, fnval=4048):
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
                return data["data"]
            else:
                raise Exception(f"获取视频流URL失败: {data.get('message', '未知错误')}")
        except Exception as e:
            raise Exception(f"获取视频流URL时出错: {str(e)}")
    
    def get_subtitle_urls(self, avid=None, bvid=None, cid=None):
        """
        获取视频字幕URL列表
        
        Args:
            avid (str): AV号
            bvid (str): BV号
            cid (str): CID（分P ID）
            
        Returns:
            list: 字幕信息列表
        """
        # 获取播放器信息，其中包含字幕信息
        player_info = self.get_player_info(avid=avid, bvid=bvid, cid=cid)
        
        # 提取字幕信息
        subtitle_info = player_info.get("subtitle", {})
        subtitles = subtitle_info.get("subtitles", [])
        
        # 处理字幕URL，确保是完整的URL
        subtitle_list = []
        for subtitle in subtitles:
            subtitle_url = subtitle.get("subtitle_url", "")
            # 如果URL不是完整的，需要补全
            if subtitle_url.startswith("//"):
                subtitle_url = "https:" + subtitle_url
            elif subtitle_url.startswith("/"):
                subtitle_url = "https://www.bilibili.com" + subtitle_url
            
            subtitle_list.append({
                "id": subtitle.get("id"),
                "language": subtitle.get("lan"),
                "language_doc": subtitle.get("lan_doc"),
                "url": subtitle_url,
                "is_lock": subtitle.get("is_lock", False),
                "type": subtitle.get("type", 0)
            })
        
        return subtitle_list
    
    def download_subtitle(self, subtitle_url, output_path=None):
        """
        下载字幕文件
        
        Args:
            subtitle_url (str): 字幕文件URL
            output_path (str): 输出文件路径，如果为None则返回字幕内容
            
        Returns:
            str or bool: 字幕内容或保存结果
        """
        try:
            response = self.session.get(subtitle_url)
            response.raise_for_status()
            subtitle_data = response.json()
            
            # 如果指定了输出路径，则保存到文件
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
                return True
            else:
                # 返回字幕内容
                return subtitle_data
        except Exception as e:
            raise Exception(f"下载字幕时出错: {str(e)}")
    
    def parse_subtitle_content(self, subtitle_data):
        """
        解析字幕内容，提取文本
        
        Args:
            subtitle_data (dict): 字幕数据
            
        Returns:
            list: 字幕文本列表
        """
        if not subtitle_data or "body" not in subtitle_data:
            return []
        
        subtitles = []
        for item in subtitle_data["body"]:
            subtitles.append({
                "from": item.get("from", 0),
                "to": item.get("to", 0),
                "content": item.get("content", "")
            })
        
        return subtitles
    
    def extract_video_content(self, url=None, avid=None, bvid=None, cid=None, quality=64, fnval=4048):
        """
        提取视频内容，优先提取字幕，如果没有字幕则提取视频流链接
        
        Args:
            url (str): B站视频URL
            avid (str): AV号
            bvid (str): BV号
            cid (str): CID（分P ID）
            quality (int): 视频清晰度代码，默认64（720P）
            fnval (int): 视频流格式标识，默认4048（DASH格式，所有可用视频流）
            
        Returns:
            dict: 提取结果
        """
        # 从URL中提取参数
        if url:
            if not bvid:
                bvid = self.get_bvid_from_url(url)
            if not avid:
                avid = self.get_avid_from_url(url)
            if not cid:
                cid = self.get_cid_from_url(url)
        
        # 获取视频信息
        video_info = self.get_video_info(avid=avid, bvid=bvid, cid=cid)
        print(f"视频标题: {video_info['title']}")
        print(f"AV号: {video_info['avid']}, BV号: {video_info['bvid']}, CID: {video_info['cid']}")
        
        # 获取字幕URL列表
        subtitle_list = self.get_subtitle_urls(avid=avid, bvid=bvid, cid=video_info['cid'])
        
        # 如果有字幕，优先提取字幕
        if subtitle_list:
            print(f"发现 {len(subtitle_list)} 个字幕:")
            result = {
                "type": "subtitle",
                "video_info": video_info,
                "subtitles": []
            }
            
            for i, subtitle in enumerate(subtitle_list):
                print(f"  {i+1}. {subtitle['language_doc']} ({subtitle['language']})")
                try:
                    # 下载字幕内容
                    subtitle_data = self.download_subtitle(subtitle['url'])
                    # 解析字幕内容
                    parsed_subtitles = self.parse_subtitle_content(subtitle_data)
                    
                    subtitle_info = {
                        "language": subtitle['language'],
                        "language_doc": subtitle['language_doc'],
                        "url": subtitle['url'],
                        "content": parsed_subtitles
                    }
                    result["subtitles"].append(subtitle_info)
                except Exception as e:
                    print(f"    下载字幕时出错: {str(e)}")
                    result["subtitles"].append({
                        "language": subtitle['language'],
                        "language_doc": subtitle['language_doc'],
                        "url": subtitle['url'],
                        "error": str(e)
                    })
            
            return result
        else:
            # 如果没有字幕，提取视频流链接
            print("未找到字幕，正在获取视频流链接...")
            try:
                stream_info = self.get_video_stream_url(
                    avid=video_info['avid'], 
                    bvid=video_info['bvid'], 
                    cid=video_info['cid'],
                    quality=quality,
                    fnval=fnval
                )
                
                result = {
                    "type": "video_stream",
                    "video_info": video_info,
                    "stream_info": stream_info
                }
                
                # 提取DASH格式的视频流链接
                if "dash" in stream_info:
                    dash_info = stream_info["dash"]
                    video_streams = dash_info.get("video", [])
                    audio_streams = dash_info.get("audio", [])
                    
                    print(f"找到 {len(video_streams)} 个视频流和 {len(audio_streams)} 个音频流:")
                    
                    # 提取视频流链接
                    video_urls = []
                    for stream in video_streams:
                        video_urls.append({
                            "quality": stream.get("id"),
                            "width": stream.get("width"),
                            "height": stream.get("height"),
                            "codec": stream.get("codecs"),
                            "url": stream.get("baseUrl"),
                            "backup_urls": stream.get("backupUrl", [])
                        })
                    
                    # 提取音频流链接
                    audio_urls = []
                    for stream in audio_streams:
                        audio_urls.append({
                            "quality": stream.get("id"),
                            "codec": stream.get("codecs"),
                            "url": stream.get("baseUrl"),
                            "backup_urls": stream.get("backupUrl", [])
                        })
                    
                    result["video_urls"] = video_urls
                    result["audio_urls"] = audio_urls
                    
                    # 显示最高质量的视频流
                    if video_urls:
                        best_video = video_urls[0]
                        print(f"最佳视频流: {best_video['width']}x{best_video['height']}, 编码: {best_video['codec']}")
                        print(f"URL: {best_video['url']}")
                    
                    # 显示最佳音频流
                    if audio_urls:
                        best_audio = audio_urls[0]
                        print(f"最佳音频流: 编码: {best_audio['codec']}")
                        print(f"URL: {best_audio['url']}")
                
                # 如果是MP4/FLV格式
                elif "durl" in stream_info:
                    durl_info = stream_info["durl"]
                    video_urls = []
                    
                    for stream in durl_info:
                        video_urls.append({
                            "order": stream.get("order"),
                            "length": stream.get("length"),
                            "size": stream.get("size"),
                            "url": stream.get("url"),
                            "backup_urls": stream.get("backup_url", [])
                        })
                    
                    result["video_urls"] = video_urls
                    
                    # 显示第一个视频流
                    if video_urls:
                        first_video = video_urls[0]
                        print(f"视频流长度: {first_video['length']}ms, 大小: {first_video['size']}bytes")
                        print(f"URL: {first_video['url']}")
                
                return result
            except Exception as e:
                raise Exception(f"获取视频流时出错: {str(e)}")
    
    def save_subtitle_to_file(self, subtitle_data, filename):
        """
        将字幕保存为SRT格式文件
        
        Args:
            subtitle_data (list): 解析后的字幕数据
            filename (str): 输出文件名
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for i, subtitle in enumerate(subtitle_data, 1):
                    # 转换时间格式为SRT格式
                    start_time = self._seconds_to_srt_time(subtitle['from'])
                    end_time = self._seconds_to_srt_time(subtitle['to'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{subtitle['content']}\n\n")
            
            return True
        except Exception as e:
            print(f"保存字幕文件时出错: {str(e)}")
            return False
    
    def _seconds_to_srt_time(self, seconds):
        """
        将秒数转换为SRT时间格式 (HH:MM:SS,mmm)
        
        Args:
            seconds (float): 秒数
            
        Returns:
            str: SRT时间格式字符串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main():
    """
    主函数，提供命令行接口
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Bilibili视频字幕和流链接提取工具')
    parser.add_argument('url', nargs='?', help='B站视频URL')
    parser.add_argument('-a', '--aid', help='AV号')
    parser.add_argument('-b', '--bvid', help='BV号')
    parser.add_argument('-c', '--cid', help='CID')
    parser.add_argument('-s', '--sessdata', help='SESSDATA登录凭证')
    parser.add_argument('-q', '--quality', type=int, default=64, help='视频清晰度代码 (默认: 64)')
    parser.add_argument('-f', '--fnval', type=int, default=4048, help='视频流格式标识 (默认: 4048)')
    parser.add_argument('-o', '--output', help='字幕输出文件名前缀')
    
    args = parser.parse_args()
    
    # 检查是否提供了必要的参数
    if not args.url and not args.aid and not args.bvid:
        parser.print_help()
        return
    
    try:
        # 创建提取器实例
        extractor = BilibiliVideo(sessdata=args.sessdata)
        
        # 提取视频内容
        result = extractor.extract_video_content(
            url=args.url,
            avid=args.aid,
            bvid=args.bvid,
            cid=args.cid,
            quality=args.quality,
            fnval=args.fnval
        )
        
        # 根据提取结果进行处理
        if result["type"] == "subtitle":
            print("\n=== 字幕提取完成 ===")
            for i, subtitle in enumerate(result["subtitles"], 1):
                lang = subtitle["language_doc"]
                if "error" in subtitle:
                    print(f"{i}. {lang} 字幕下载失败: {subtitle['error']}")
                    continue
                
                print(f"{i}. {lang} 字幕:")
                
                # 保存字幕到文件
                filename = f"subtitle_{lang}"
                if args.output:
                    filename = f"{args.output}_{lang}"
                
                # 保存为JSON格式
                json_filename = f"{filename}.json"
                try:
                    with open(json_filename, 'w', encoding='utf-8') as f:
                        json.dump(subtitle["content"], f, ensure_ascii=False, indent=2)
                    print(f"  JSON格式已保存到: {json_filename}")
                except Exception as e:
                    print(f"  保存JSON格式时出错: {str(e)}")
                
                # 保存为SRT格式
                srt_filename = f"{filename}.srt"
                if extractor.save_subtitle_to_file(subtitle["content"], srt_filename):
                    print(f"  SRT格式已保存到: {srt_filename}")
                else:
                    print(f"  保存SRT格式时出错")
        else:
            print("\n=== 视频流链接提取完成 ===")
            # 保存视频流信息到文件
            filename = "video_stream_info.json"
            if args.output:
                filename = f"{args.output}_stream_info.json"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"视频流信息已保存到: {filename}")
            except Exception as e:
                print(f"保存视频流信息时出错: {str(e)}")
                
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()