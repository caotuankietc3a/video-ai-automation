import os
import shutil
import re
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import yt_dlp
import cv2
from ..config.constants import VIDEOS_DIR, OUTPUTS_DIR

class VideoManager:
    def __init__(self):
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
    
    def upload_video(self, source_path: str, project_name: str) -> str:
        filename = os.path.basename(source_path)
        project_dir = os.path.join(VIDEOS_DIR, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        dest_path = os.path.join(project_dir, filename)
        shutil.copy2(source_path, dest_path)
        return dest_path
    
    @staticmethod
    def _validate_url(url: str) -> Tuple[bool, str]:
        """
        Validate if the provided URL is a valid YouTube or TikTok URL
        
        Args:
            url (str): URL to validate
            
        Returns:
            tuple[bool, str]: (is_valid, platform_type)
        """
        url_lower = url.lower()
        
        tiktok_pattern = r'https?://((?:vm|vt|www)\.)?tiktok\.com/.*'
        if re.match(tiktok_pattern, url_lower):
            return True, 'tiktok'
        
        youtube_patterns = [
            r'https?://(www\.)?(youtube\.com|youtu\.be)/.*',
            r'https?://(www\.)?youtube\.com/watch\?v=.*',
            r'https?://youtu\.be/.*',
        ]
        for pattern in youtube_patterns:
            if re.match(pattern, url_lower):
                return True, 'youtube'
        
        return False, 'unknown'
    
    @staticmethod
    def _progress_hook(d: Dict[str, Any]) -> None:
        """
        Hook to display download progress
        
        Args:
            d (Dict[str, Any]): Progress information dictionary
        """
        if d['status'] == 'downloading':
            progress = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"Đang tải: {progress} tốc độ {speed} còn lại {eta}", end='\r')
        elif d['status'] == 'finished':
            print("\n✓ Đã tải xong, đang xử lý...")
    
    def download_video_from_url(self, url: str, project_name: str) -> Optional[str]:
        """
        Download video from YouTube or TikTok URL
        
        Args:
            url (str): URL of the video (YouTube or TikTok)
            project_name (str): Project name to save video in
            
        Returns:
            Optional[str]: Path to downloaded file if successful, None otherwise
        """
        is_valid, platform = self._validate_url(url)
        if not is_valid:
            print(f"❌ Lỗi: URL không hợp lệ. Chỉ hỗ trợ YouTube và TikTok")
            return None
        
        try:
            project_dir = os.path.join(VIDEOS_DIR, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            ydl_opts = {
                'outtmpl': os.path.join(project_dir, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',
                'noplaylist': True,
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [self._progress_hook],
            }
            
            if platform == 'tiktok':
                ydl_opts.update({
                    'extractor_args': {
                        'tiktok': {
                            'webpage_download': True,
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.tiktok.com/',
                    },
                })
                
                try:
                    ydl_opts['cookiesfrombrowser'] = ('chrome',)
                except Exception:
                    try:
                        ydl_opts['cookiesfrombrowser'] = ('safari',)
                    except Exception:
                        pass
            
            elif platform == 'youtube':
                ydl_opts.update({
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    },
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    print(f"📥 Đang tải video từ {platform.upper()}...")
                    info = ydl.extract_info(url, download=True)
                    
                    if info:
                        filename = ydl.prepare_filename(info)
                        if os.path.exists(filename):
                            print(f"✓ Đã tải video thành công: {filename}")
                            return filename
                        
                        title = info.get('title', 'video')
                        ext = info.get('ext', 'mp4')
                        sanitized_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                        possible_filename = os.path.join(project_dir, f"{sanitized_title}.{ext}")
                        if os.path.exists(possible_filename):
                            print(f"✓ Đã tải video thành công: {possible_filename}")
                            return possible_filename
                        
                        for file in os.listdir(project_dir):
                            if file.endswith(('.mp4', '.webm', '.mkv')):
                                file_path = os.path.join(project_dir, file)
                                file_mtime = os.path.getmtime(file_path)
                                if file_mtime > (os.path.getmtime(project_dir) - 60):
                                    print(f"✓ Đã tải video thành công: {file_path}")
                                    return file_path
                    
                    print("⚠ Không tìm thấy file video đã tải")
                    return None
                    
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e)
                    if platform == 'tiktok':
                        print(f"❌ Lỗi khi tải video TikTok: {error_msg}")
                        print("💡 Gợi ý khắc phục:")
                        print("   1. Cập nhật yt-dlp: pip install -U yt-dlp")
                        print("   2. Sử dụng URL đầy đủ từ TikTok (không phải short link)")
                        print("   3. Kiểm tra video có còn tồn tại và công khai không")
                        print("   4. Thử mở video trong browser trước để đảm bảo video có thể truy cập")
                    else:
                        print(f"❌ Lỗi khi tải video YouTube: {error_msg}")
                    return None
                except Exception as extract_error:
                    error_msg = str(extract_error)
                    print(f"❌ Lỗi không mong đợi: {error_msg}")
                    if platform == 'tiktok':
                        print("💡 Có thể thử cập nhật yt-dlp: pip install -U yt-dlp")
                    return None
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Lỗi khi tải video: {error_msg}")
            if platform == 'tiktok':
                print("💡 Gợi ý: Cập nhật yt-dlp lên phiên bản mới nhất")
            return None
    
    def extract_frames(self, video_path: str, num_frames: int = 10) -> List[str]:
        frames_dir = os.path.join(os.path.dirname(video_path), "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame_indices = [int(total_frames * i / (num_frames + 1)) for i in range(1, num_frames + 1)]
        frame_paths = []
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count in frame_indices:
                frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
            
            frame_count += 1
        
        cap.release()
        return frame_paths
    
    def get_video_info(self, video_path: str) -> dict:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'duration': duration,
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'size': os.path.getsize(video_path)
        }
    
    def save_output_video(self, video_path: str, project_name: str, scene_id: str) -> str:
        project_output_dir = os.path.join(OUTPUTS_DIR, project_name)
        os.makedirs(project_output_dir, exist_ok=True)
        
        filename = f"scene_{scene_id}.mp4"
        dest_path = os.path.join(project_output_dir, filename)
        
        if os.path.exists(video_path):
            shutil.copy2(video_path, dest_path)
        
        return dest_path
    
    def merge_videos(self, video_paths: List[str], output_path: str) -> bool:
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            
            clips = [VideoFileClip(path) for path in video_paths if os.path.exists(path)]
            if not clips:
                return False
            
            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            for clip in clips:
                clip.close()
            final_clip.close()
            
            return True
        except Exception as e:
            print(f"Error merging videos: {e}")
            return False
    
    def get_video_thumbnail(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        if output_path is None:
            output_path = video_path.replace('.mp4', '_thumb.jpg')
        
        cv2.imwrite(output_path, frame)
        return output_path

video_manager = VideoManager()

