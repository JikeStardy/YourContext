#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili稍后再看视频列表管理工具
用于管理B站稍后再看视频列表，包括获取列表、删除指定视频、清空列表等功能
"""

import requests
import json
import sys

class BilibiliToView:
    def __init__(self, sessdata=None):
        """
        初始化B站稍后再看管理器
        
        Args:
            sessdata (str): B站登录凭证，用于访问稍后再看功能
        """
        self.sessdata = sessdata
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        })
        
        # 如果提供了SESSDATA，则添加到Cookie中
        if self.sessdata:
            self.session.cookies.set('SESSDATA', self.sessdata)
    
    def _get_csrf(self):
        """
        从Cookie中获取CSRF Token
        
        Returns:
            str: CSRF Token
        """
        cookies = self.session.cookies
        return cookies.get('bili_jct', '')
    
    def get_toview_list(self, save_to_file=False):
        """
        获取稍后再看视频列表
        
        Args:
            save_to_file (bool): 是否将列表保存到文件，默认为False
        
        Returns:
            dict: 稍后再看视频列表信息
        """
        url = "https://api.bilibili.com/x/v2/history/toview"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            if save_to_file:
                import hashlib, time
                timestamp = int(time.time())
                sha256 = hashlib.sha256(str(timestamp).encode()).hexdigest()[:16]
                filename = f"toview_list_{timestamp}_{sha256}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            if data.get("code") == 0:
                return data
            else:
                raise Exception(f"获取稍后再看列表失败: {data.get('message', '未知错误')}")
        except Exception as e:
            raise Exception(f"获取稍后再看列表时出错: {str(e)}")
    
    def delete_toview_video(self, avid=None, delete_viewed=False):
        """
        删除稍后再看列表中的指定视频
        
        Args:
            avid (int): 要删除的视频avid，如果不提供则删除所有已观看的视频
            delete_viewed (bool): 是否删除所有已观看的视频，默认为False
            
        Returns:
            dict: 删除结果
        """
        url = "https://api.bilibili.com/x/v2/history/toview/del"
        
        # 准备请求参数
        data = {
            'csrf': self._get_csrf()
        }
        
        if delete_viewed:
            data['viewed'] = 'true'
        elif avid:
            data['aid'] = str(avid)
        else:
            raise ValueError("必须提供avid或设置delete_viewed为True")
        
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                return result
            else:
                raise Exception(f"删除视频失败: {result.get('message', '未知错误')}")
        except Exception as e:
            raise Exception(f"删除视频时出错: {str(e)}")
    
    def clear_toview_list(self):
        """
        清空稍后再看视频列表
        
        Returns:
            dict: 清空结果
        """
        url = "https://api.bilibili.com/x/v2/history/toview/clear"
        
        # 准备请求参数
        data = {
            'csrf': self._get_csrf()
        }
        
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                return result
            else:
                raise Exception(f"清空列表失败: {result.get('message', '未知错误')}")
        except Exception as e:
            raise Exception(f"清空列表时出错: {str(e)}")
    
    def format_toview_list(self, toview_data):
        """
        格式化稍后再看列表数据，便于显示
        
        Args:
            toview_data (dict): 稍后再看列表原始数据
            
        Returns:
            list: 格式化后的视频列表
        """
        if not toview_data or toview_data.get("code") != 0:
            return []
        
        formatted_list = []
        video_list = toview_data.get("data", {}).get("list", [])
        
        for index, video in enumerate(video_list, 1):
            formatted_video = {
                "index": index,
                "aid": video.get("aid", 0),
                "bvid": video.get("bvid", ""),
                "title": video.get("title", ""),
                "author": video.get("owner", {}).get("name", ""),
                "duration": video.get("duration", 0),
                "progress": video.get("progress", 0),
                "add_time": video.get("add_at", 0),
                "pic": video.get("pic", "")
            }
            formatted_list.append(formatted_video)
        
        return formatted_list
    
    def print_toview_list(self, toview_data=None):
        """
        打印稍后再看列表
        
        Args:
            toview_data (dict): 稍后再看列表数据，如果不提供则自动获取
        """
        if toview_data is None:
            toview_data = self.get_toview_list()
        
        if toview_data.get("code") != 0:
            print(f"获取列表失败: {toview_data.get('message', '未知错误')}")
            return
        
        video_list = self.format_toview_list(toview_data)
        count = toview_data.get("data", {}).get("count", 0)
        
        print(f"稍后再看列表 (共{count}个视频):")
        print("-" * 80)
        
        if not video_list:
            print("列表为空")
            return
        
        for video in video_list:
            # 格式化时长
            duration = video["duration"]
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes:02d}:{seconds:02d}"
            
            # 格式化进度
            progress = video["progress"]
            if progress > 0:
                progress_minutes = progress // 60
                progress_seconds = progress % 60
                progress_str = f"{progress_minutes:02d}:{progress_seconds:02d}"
                progress_info = f" [已观看: {progress_str}]"
            else:
                progress_info = ""
            
            print(f"{video['index']:2d}. {video['title']}")
            print(f"    UP: {video['author']}  时长: {duration_str}{progress_info}")
            print(f"    AV号: {video['aid']}  BV号: {video['bvid']}")
            print()
            
        # 返回标题和时长
        return [{"title": v["title"], "duration": v["duration"]} for v in video_list]
    
    def _seconds_to_time_str(self, seconds):
        """
        将秒数转换为时间字符串 (MM:SS)
        
        Args:
            seconds (int): 秒数
            
        Returns:
            str: 时间字符串
        """
        if seconds <= 0:
            return "00:00"
        
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"


def main():
    """
    主函数，提供命令行接口
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Bilibili稍后再看视频列表管理工具')
    parser.add_argument('-s', '--sessdata', help='SESSDATA登录凭证')
    parser.add_argument('-sf', '--sessdatafile', help='SESSDATA登录凭证 (文件路径)')
    parser.add_argument('-a', '--action', choices=['list', 'delete', 'clear', 'delete_viewed'], 
                       default='list', help='操作类型: list(获取列表), delete(删除指定视频), clear(清空列表), delete_viewed(删除已观看视频)')
    parser.add_argument('--aid', type=int, help='要删除的视频AV号')
    
    args = parser.parse_args()

    # 从文件读取SESSDATA
    if args.sessdatafile:
        try:
            with open(args.sessdatafile, 'r') as f:
                args.sessdata = f.read().strip()
        except FileNotFoundError:
            print(f"错误: 未找到文件 {args.sessdatafile}")
            sys.exit(1)
    
    try:
        # 创建管理器实例
        manager = BilibiliToView(sessdata=args.sessdata)
        
        if args.action == 'list':
            # 获取并显示稍后再看列表
            toview_data = manager.get_toview_list(save_to_file=True)
            video_brief_list = manager.print_toview_list(toview_data)

            # 统计总时长
            total_duration = sum(video["duration"] for video in video_brief_list)
            total_minutes = total_duration // 60
            total_seconds = total_duration % 60
            print(f"总时长: {total_minutes:02d}:{total_seconds:02d}")
            
        elif args.action == 'delete':
            # 删除指定视频
            if not args.aid:
                print("删除视频时必须提供--aid参数")
                return
            
            result = manager.delete_toview_video(avid=args.aid)
            if result.get("code") == 0:
                print(f"成功删除视频 AV{args.aid}")
            else:
                print(f"删除视频失败: {result.get('message', '未知错误')}")
                
        elif args.action == 'clear':
            # 清空列表
            result = manager.clear_toview_list()
            if result.get("code") == 0:
                print("成功清空稍后再看列表")
            else:
                print(f"清空列表失败: {result.get('message', '未知错误')}")
                
        elif args.action == 'delete_viewed':
            # 删除已观看的视频
            result = manager.delete_toview_video(delete_viewed=True)
            if result.get("code") == 0:
                print("成功删除所有已观看的视频")
            else:
                print(f"删除已观看视频失败: {result.get('message', '未知错误')}")
                
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()