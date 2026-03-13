import os
import cv2
import numpy as np
import torch
import whisper
from transformers import pipeline
from ultralytics import YOLO
import subprocess
import tempfile
from moviepy.editor import VideoFileClip
import json
from typing import List, Dict, Any
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        # Initialize models (lazy loading)
        self.yolo_model = None
        self.whisper_model = None
        self.llm_model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        
        # Popular hashtags database
        self.popular_hashtags = {
            'instagram': ['#love', '#instagood', '#photooftheday', '#fashion', '#beautiful'],
            'tiktok': ['#fyp', '#foryou', '#viral', '#trending', '#tiktok'],
            'youtube': ['#shorts', '#youtubeshorts', '#viral', '#trending', '#comedy'],
            'facebook': ['#facebook', '#love', '#instagood', '#photooftheday', '#fashion'],
            'twitter': ['#twitter', '#trending', '#news', '#viral', '#love'],
            'linkedin': ['#linkedin', '#career', '#job', '#business', '#networking']
        }
    
    def load_yolo(self):
        """Load YOLO model for object detection"""
        if self.yolo_model is None:
            try:
                # Using YOLOv8n (nano) for faster processing
                logger.info("Loading YOLO model...")
                self.yolo_model = YOLO('yolov8n.pt')
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
                self.yolo_model = None
        return self.yolo_model
    
    def load_whisper(self):
        """Load Whisper model for speech recognition"""
        if self.whisper_model is None:
            try:
                # Using tiny model for faster processing
                logger.info("Loading Whisper model...")
                self.whisper_model = whisper.load_model("tiny")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                self.whisper_model = None
        return self.whisper_model
    
    def load_llm(self):
        """Load LLM model for caption generation"""
        if self.llm_model is None:
            try:
                logger.info("Loading LLM model...")
                # Use a small model that's quick to load
                self.llm_model = pipeline(
                    "text-generation",
                    model="gpt2",  # Small model that's quick to load
                    tokenizer="gpt2"
                )
                logger.info("LLM model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load LLM model: {e}")
                self.llm_model = None
        return self.llm_model
    
    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video file"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmpfile:
                audio_path = tmpfile.name
            
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ac', '1', '-ar', '16000',
                '-y', audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return None
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                return audio_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract audio: {e}")
            return None
    
    def detect_objects(self, video_path: str) -> List[Dict]:
        """Detect objects in video using YOLO"""
        try:
            model = self.load_yolo()
            if model is None:
                logger.warning("YOLO model not available, skipping object detection")
                return []
            
            objects_detected = []
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return []
            
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            if fps == 0:
                fps = 30  # Default assumption
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                logger.warning("Video has 0 frames")
                return []
            
            # Sample frames (every 2 seconds)
            frame_interval = fps * 2
            if frame_interval == 0:
                frame_interval = 60
            
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    try:
                        # Run YOLO detection
                        results = model(frame, conf=0.25, verbose=False)
                        
                        for result in results:
                            boxes = result.boxes
                            if boxes is not None:
                                for box in boxes:
                                    cls_id = int(box.cls[0])
                                    conf = float(box.conf[0])
                                    label = model.names[cls_id]
                                    
                                    objects_detected.append({
                                        'object': label,
                                        'confidence': conf,
                                        'frame': frame_count
                                    })
                    except Exception as e:
                        logger.error(f"YOLO detection error on frame {frame_count}: {e}")
                        continue
                
                frame_count += 1
                if frame_count >= total_frames:
                    break
            
            cap.release()
            
            # Aggregate results
            object_counts = {}
            for obj in objects_detected:
                label = obj['object']
                if label in object_counts:
                    object_counts[label] += 1
                else:
                    object_counts[label] = 1
            
            # Get top 5 most frequent objects
            top_objects = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return [
                {'object': obj, 'count': count}
                for obj, count in top_objects
            ]
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Whisper"""
        try:
            model = self.load_whisper()
            if model is None:
                logger.warning("Whisper model not available, skipping audio transcription")
                return ""
            
            if not os.path.exists(audio_path):
                logger.warning(f"Audio file not found: {audio_path}")
                return ""
            
            result = model.transcribe(audio_path, fp16=False)  # fp16=False for CPU
            return result['text']
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return ""
    
    def analyze_video_content(self, objects: List[Dict], transcript: str, duration: float) -> str:
        """Analyze video content and generate description"""
        description_parts = []
        
        if objects:
            object_summary = ", ".join([obj['object'] for obj in objects[:3]])
            description_parts.append(f"Shows: {object_summary}")
        
        if transcript and len(transcript.strip()) > 10:
            short_transcript = transcript[:100].strip()
            if len(transcript) > 100:
                short_transcript += "..."
            description_parts.append(f"Audio: {short_transcript}")
        
        if duration:
            description_parts.append(f"Duration: {duration:.1f}s")
        
        return " | ".join(description_parts) if description_parts else "Video content"
    
    def generate_caption(self, description: str, platform: str, tone: str, keywords: str = "") -> str:
        """Generate caption using LLM or fallback"""
        try:
            model = self.load_llm()
            if model is None:
                return self._generate_fallback_caption(description, platform, tone, keywords)
            
            # Build prompt
            prompt = self._build_prompt(description, platform, tone, keywords)
            
            # Generate caption
            response = model(
                prompt,
                max_length=150,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=model.tokenizer.eos_token_id
            )
            
            if response and len(response) > 0:
                caption = response[0]['generated_text'].strip()
                # Extract just the caption part
                if 'CAPTION:' in caption:
                    caption = caption.split('CAPTION:')[-1].strip()
                return caption[:500]  # Limit length
            
            return self._generate_fallback_caption(description, platform, tone, keywords)
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback_caption(description, platform, tone, keywords)
    
    def _build_prompt(self, description: str, platform: str, tone: str, keywords: str) -> str:
        """Build prompt for LLM"""
        platform_guides = {
            'instagram': "Instagram post with emojis",
            'tiktok': "TikTok video caption, trendy",
            'youtube': "YouTube Shorts description",
            'facebook': "Facebook post",
            'twitter': "Tweet, concise",
            'linkedin': "LinkedIn post, professional"
        }
        
        tone_guides = {
            'friendly': "friendly and engaging",
            'professional': "professional and formal",
            'funny': "funny and humorous",
            'inspirational': "inspirational and motivational",
            'casual': "casual and relaxed",
            'educational': "educational and informative",
            'dramatic': "dramatic and exciting"
        }
        
        platform_guide = platform_guides.get(platform, "social media post")
        tone_guide = tone_guides.get(tone, "engaging")
        
        prompt = f"""Create a {tone_guide} caption for a {platform_guide}.

Video content: {description}
Keywords: {keywords if keywords else "not specified"}

CAPTION:"""
        
        return prompt
    
    def _generate_fallback_caption(self, description: str, platform: str, tone: str, keywords: str) -> str:
        """Fallback caption generation without LLM"""
        tone_intros = {
            'friendly': ["Check this out!", "Just wanted to share", "Hope you enjoy this"],
            'professional': ["Presenting", "Showcasing", "An overview of"],
            'funny': ["You won't believe this!", "Wait for it...", "This is hilarious"],
            'inspirational': ["Be inspired", "A moment of reflection", "This will motivate you"],
            'casual': ["Here's something cool", "Just sharing", "Take a look"],
            'educational': ["Learn something new", "Educational moment", "Knowledge sharing"],
            'dramatic': ["You HAVE to see this!", "Incredible moment", "Unbelievable!"]
        }
        
        import random
        intro = random.choice(tone_intros.get(tone, tone_intros['friendly']))
        
        # Platform-specific formatting
        if platform in ['instagram', 'tiktok']:
            emojis = ['🎬', '🔥', '✨', '🌟', '👀']
            emoji = random.choice(emojis)
            caption = f"{intro} {description[:80]} {emoji}"
        elif platform == 'twitter':
            caption = f"{intro} {description[:120]}"
        else:
            caption = f"{intro} {description[:150]}"
        
        return caption
    
    def suggest_hashtags(self, description: str, keywords: str, platform: str, num_hashtags: int = 8) -> List[str]:
        """Suggest relevant hashtags"""
        hashtags = []
        
        # Add user keywords as hashtags
        if keywords:
            for keyword in keywords.split(','):
                keyword = keyword.strip()
                if keyword and len(keyword) > 2:
                    hashtag = f"#{keyword.replace(' ', '')}"
                    if hashtag not in hashtags:
                        hashtags.append(hashtag)
        
        # Add platform-specific popular hashtags
        platform_tags = self.popular_hashtags.get(platform, [])
        for tag in platform_tags[:5]:  # Top 5 popular tags
            if tag not in hashtags:
                hashtags.append(tag)
        
        # Add generic hashtags based on description
        common_words = set(['the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'was', 'were'])
        words = description.lower().split()
        for word in words:
            word = ''.join(c for c in word if c.isalnum())
            if (len(word) > 3 and word not in common_words and 
                word.isalpha() and len(hashtags) < num_hashtags):
                hashtag = f"#{word}"
                if hashtag not in hashtags:
                    hashtags.append(hashtag)
        
        # Limit number of hashtags
        return hashtags[:num_hashtags]
    
    def process_video(self, video_path: str, platform: str, tone: str, keywords: str = "") -> Dict[str, Any]:
        """Main processing pipeline"""
        logger.info(f"Starting video processing: {video_path}")
        results = {
            'detected_objects': [],
            'audio_transcript': '',
            'video_description': '',
            'generated_caption': '',
            'suggested_hashtags': [],
            'success': False
        }
        
        try:
            # Check if video exists
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                results['error'] = "Video file not found"
                return results
            
            # Get video duration
            try:
                clip = VideoFileClip(video_path)
                duration = clip.duration
                clip.close()
                
                if duration > 60:
                    results['error'] = f"Video too long: {duration:.1f}s (max 60s)"
                    return results
                
                if duration < 0.5:
                    results['error'] = f"Video too short: {duration:.1f}s"
                    return results
                    
            except Exception as e:
                logger.warning(f"Could not get video duration: {e}")
                duration = 0
            
            # Step 1: Detect objects (parallelize if possible)
            logger.info("Step 1: Object detection")
            objects = self.detect_objects(video_path)
            results['detected_objects'] = objects
            
            # Step 2: Extract and transcribe audio
            logger.info("Step 2: Audio transcription")
            audio_path = self.extract_audio(video_path)
            if audio_path:
                transcript = self.transcribe_audio(audio_path)
                results['audio_transcript'] = transcript
                # Clean up audio file
                try:
                    os.remove(audio_path)
                except:
                    pass
            else:
                logger.warning("Could not extract audio")
            
            # Step 3: Generate video description
            logger.info("Step 3: Generate description")
            description = self.analyze_video_content(objects, results['audio_transcript'], duration)
            results['video_description'] = description
            
            # Step 4: Generate caption
            logger.info("Step 4: Generate caption")
            caption = self.generate_caption(description, platform, tone, keywords)
            results['generated_caption'] = caption
            
            # Step 5: Suggest hashtags
            logger.info("Step 5: Suggest hashtags")
            hashtags = self.suggest_hashtags(description, keywords, platform)
            results['suggested_hashtags'] = hashtags
            
            results['success'] = True
            logger.info("Video processing completed successfully")
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results['error'] = str(e)
        
        return results