from typing import Tuple
import os
import requests
import tempfile


def download_file(url: str, file_path, session: requests.Session=None, retry: int=3) -> Tuple[str, bool]:
    """
    下载文件到指定路径
    
    Args:
        url (str): 文件URL
        file_path (str): 本地保存路径
        
    Returns:
        str: 成功返回文件路径，失败返回错误信息
        bool: 是否成功
    """
    if not session:
        session = requests.Session()
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                        
        return file_path, True
    except Exception as e:
        if retry > 0:
            return download_file(url, file_path, session=session, retry=retry-1)
        return str(e), False
    
def download_temp_file(url: str, session: requests.Session=None) -> Tuple[str, bool]:
    """
    下载文件到临时路径
    
    Args:
        url (str): 文件URL
        
    Returns:
        str: 临时文件路径
        bool: 是否成功
    """
    file_path = tempfile.NamedTemporaryFile(delete=False).name
    return download_file(url, file_path, session=session)
