import os
import cv2
from moviepy.editor import VideoFileClip
import tempfile
import uuid
from datetime import datetime
from django.core.files.storage import default_storage

def validate_video(file):
    """Validate video file"""
    # Check file size (max 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size > max_size:
        return False, "File size exceeds 100MB limit"
    
    # Check file extension
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.m4v']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        return False, f"Invalid file format. Allowed: {', '.join(valid_extensions)}"
    
    return True, ""

def save_video_file(user, video_file):
    """Save video file with proper naming"""
    # Create directory if it doesn't exist
    user_dir = f'media/videos/user_{user.id}'
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{os.path.splitext(video_file.name)[1]}"
    filepath = os.path.join(user_dir, filename)
    
    # Save file
    with open(filepath, 'wb+') as destination:
        for chunk in video_file.chunks():
            destination.write(chunk)
    
    return filepath

def get_video_duration(filepath):
    """Get video duration in seconds using multiple methods"""
    try:
        # Method 1: Using moviepy
        try:
            clip = VideoFileClip(filepath)
            duration = clip.duration
            clip.close()
            if duration > 0:
                return duration
        except:
            pass
        
        # Method 2: Using OpenCV
        try:
            cap = cv2.VideoCapture(filepath)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            if fps > 0 and frame_count > 0:
                return frame_count / fps
        except:
            pass
        
        # Method 3: Using ffprobe (if available)
        try:
            import subprocess
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                   'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        
        return 0
        
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return 0