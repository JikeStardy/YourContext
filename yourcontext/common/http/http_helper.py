import requests
import tempfile


def download_temp_file(url: str, file_path: str=None, session: requests.Session=None) -> str:
    """
    下载文件到指定路径
    
    Args:
        url (str): 文件URL
        file_path (str): 本地保存路径
        
    Returns:
        Union[str, bytes]: 成功返回文件路径，失败返回错误信息
    """
    if not file_path:
        file_path = tempfile.NamedTemporaryFile(delete=False).name
    if not session:
        session = requests.Session()
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                        
        return file_path
    except Exception as e:
        raise Exception(f"下载文件失败: {str(e)}")