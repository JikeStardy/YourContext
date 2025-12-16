import os

from typing import Optional

def ensure_dir(file_path: str=None, dir_path: str=None) -> str:
    """
    保证path存在：
    - 如果是文件，确保其父目录存在
    - 如果是目录，确保其存在
    """
    if file_path is not None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        return file_path
    elif dir_path is not None:
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
    else:
        raise ValueError("Either file_path or dir_path must be provided")
