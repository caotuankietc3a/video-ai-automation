import os
import shutil
from typing import List, Optional
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
    
    def download_video_from_url(self, url: str, project_name: str) -> Optional[str]:
        try:
            project_dir = os.path.join(VIDEOS_DIR, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            ydl_opts = {
                'outtmpl': os.path.join(project_dir, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            print(f"Error downloading video: {e}")
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

