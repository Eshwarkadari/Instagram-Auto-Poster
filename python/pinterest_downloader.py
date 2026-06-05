"""
pinterest_downloader.py
Pinterest Downloader using yt-dlp
Author: Kadari Eshwar
"""

import os
import glob
import yt_dlp


def download(url, folder="downloads"):
    """
    Download Pinterest image/video and return file path + media type
    """

    try:
        os.makedirs(folder, exist_ok=True)

        before = set(glob.glob(os.path.join(folder, "*")))

        ydl_opts = {
            "outtmpl": os.path.join(folder, "%(id)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        after = set(glob.glob(os.path.join(folder, "*")))
        new_files = list(after - before)

        if not new_files:
            print("❌ No file downloaded")
            return None, None

        file_path = max(new_files, key=os.path.getctime)

        ext = file_path.split(".")[-1].lower()

        if ext in ["mp4", "mov", "webm"]:
            media_type = "video"
        else:
            media_type = "image"

        print(f"✅ Downloaded: {file_path}")
        return file_path, media_type

    except Exception as e:
        print(f"❌ Pinterest download failed: {e}")
        return None, None
