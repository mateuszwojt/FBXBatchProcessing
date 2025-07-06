"""Download and extract FBX files and textures."""
import os
import zipfile
import tempfile
import shutil
import requests
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import tqdm


def download_file(url: str, output_dir: str) -> str:
    """Download a file from URL to the specified directory.
    
    Args:
        url: URL of the file to download
        output_dir: Directory to save the downloaded file
        
    Returns:
        str: Path to the downloaded file
        
    Raises:
        Exception: If download fails
    """
    os.makedirs(output_dir, exist_ok=True)
    local_filename = os.path.join(output_dir, os.path.basename(urlparse(url).path))
    
    # Stream the download to handle large files
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        
        # Initialize progress bar
        progress = tqdm.tqdm(
            total=total_size, 
            unit='iB', 
            unit_scale=True,
            desc=f"Downloading {os.path.basename(local_filename)}"
        )
        
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                progress.update(len(chunk))
                f.write(chunk)
        
        progress.close()
    
    return local_filename


def extract_zip(zip_path: str, output_dir: str) -> Tuple[str, List[str]]:
    """Extract a zip file and find the FBX file and textures.
    
    Args:
        zip_path: Path to the zip file
        output_dir: Directory to extract files to
        
    Returns:
        tuple: (fbx_path, texture_paths) - Path to FBX file and list of texture paths
        
    Raises:
        ValueError: If no FBX file is found in the archive
    """
    os.makedirs(output_dir, exist_ok=True)
    fbx_path = None
    texture_paths = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extract all files
        zip_ref.extractall(output_dir)
        
        # Find FBX and texture files
        for file_info in zip_ref.infolist():
            file_path = os.path.join(output_dir, file_info.filename)
            if file_path.lower().endswith('.fbx'):
                if fbx_path is not None:
                    raise ValueError("Multiple FBX files found in archive")
                fbx_path = file_path
            elif any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                texture_paths.append(file_path)
    
    if fbx_path is None:
        raise ValueError("No FBX file found in archive")
    
    return fbx_path, texture_paths


def process_download_url(url: str, temp_dir: str) -> Tuple[str, List[str]]:
    """Download and extract a single URL.
    
    Args:
        url: URL to download
        temp_dir: Directory for temporary files
        
    Returns:
        tuple: (fbx_path, texture_paths)
    """
    # Create a subdirectory for this download
    download_id = os.path.splitext(os.path.basename(urlparse(url).path))[0]
    download_dir = os.path.join(temp_dir, download_id)
    os.makedirs(download_dir, exist_ok=True)
    
    try:
        # Download the file
        zip_path = download_file(url, download_dir)
        
        # Extract contents
        extract_dir = os.path.join(download_dir, 'extracted')
        fbx_path, texture_paths = extract_zip(zip_path, extract_dir)
        
        return fbx_path, texture_paths
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
        raise e
