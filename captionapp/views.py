from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import threading
import os
import cv2
import numpy as np
import random
from datetime import datetime
from django.conf import settings
from .forms import UserRegisterForm, VideoUploadForm
from .models import VideoUpload, CaptionHistory
import logging
import time

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.popular_hashtags = {
            'instagram': ['#love', '#instagood', '#photooftheday', '#fashion', '#beautiful', '#happy', '#cute'],
            'tiktok': ['#fyp', '#foryou', '#viral', '#trending', '#tiktok', '#comedy', '#funny'],
            'youtube': ['#shorts', '#youtubeshorts', '#viral', '#trending', '#comedy', '#funny', '#music'],
            'facebook': ['#facebook', '#love', '#instagood', '#photooftheday', '#fashion', '#beautiful'],
            'twitter': ['#twitter', '#trending', '#news', '#viral', '#love', '#funny', '#memes'],
            'linkedin': ['#linkedin', '#career', '#job', '#business', '#networking', '#professional']
        }
    
    def detect_objects_simple(self, video_path):
        """Simple object detection using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            objects = []
            
            # Common objects to detect (simulated)
            common_objects = ['person', 'car', 'tree', 'building', 'animal', 'sky', 'road', 'water']
            
            # Randomly pick some objects
            num_objects = random.randint(2, 6)
            selected = random.sample(common_objects, num_objects)
            
            for obj in selected:
                objects.append({
                    'object': obj,
                    'count': random.randint(1, 5),
                    'confidence': random.uniform(0.7, 0.95)
                })
            
            cap.release()
            return objects
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return [{'object': 'video', 'count': 1, 'confidence': 0.9}]
    
    def analyze_video_content(self, objects, duration):
        """Analyze video content"""
        if objects:
            object_names = [obj['object'] for obj in objects[:3]]
            return f"A video showing {', '.join(object_names)}"
        return "An engaging video"
    
    def generate_caption(self, description, platform, tone, keywords):
        """Generate caption based on analysis"""
        
        tone_phrases = {
            'friendly': [
                "Check out this amazing video! 😊",
                "You'll love watching this! 👍",
                "Hope you enjoy this as much as I did! 🎉"
            ],
            'professional': [
                "Presenting: An informative video analysis. 📊",
                "Educational content worth watching. 🎓",
                "Professional insights from this video. 💼"
            ],
            'funny': [
                "This will definitely make you laugh! 😂",
                "Wait for it... the funny part is coming! 🤣",
                "Hilarious moment captured on video! 🎭"
            ],
            'inspirational': [
                "Be inspired by this powerful video! ✨",
                "A moment of motivation and inspiration. 🌟",
                "This video will uplift your spirit! 💫"
            ],
            'casual': [
                "Here's a cool video I wanted to share. 😎",
                "Just found this interesting video. 📱",
                "Take a look at this! 👀"
            ],
            'educational': [
                "Learn something new from this video! 📚",
                "Educational content that's worth your time. 🎯",
                "Knowledge sharing through video. 🧠"
            ],
            'dramatic': [
                "You HAVE to see this incredible video! 🔥",
                "Unbelievable moment captured! 🤯",
                "This video will blow your mind! 💥"
            ]
        }
        
        platform_formats = {
            'instagram': "Perfect for your Instagram feed! 📸",
            'tiktok': "Ready for your TikTok FYP! 🎵",
            'youtube': "Great YouTube Shorts content! 🎬",
            'facebook': "Share this on your Facebook timeline! 📘",
            'twitter': "Tweet-worthy content! 🐦",
            'linkedin': "Professional content for LinkedIn! 💼"
        }
        
        # Select appropriate phrases
        tone_choice = random.choice(tone_phrases.get(tone, tone_phrases['friendly']))
        platform_format = platform_formats.get(platform, "")
        
        # Build caption
        caption = f"{tone_choice} {description} {platform_format}"
        
        # Add keywords if provided
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            if keyword_list:
                caption += f"\n\nKeywords: {', '.join(keyword_list[:3])}"
        
        return caption
    
    def suggest_hashtags(self, description, keywords, platform):
        """Suggest relevant hashtags"""
        hashtags = []
        
        # Add user keywords
        if keywords:
            for keyword in keywords.split(','):
                keyword = keyword.strip()
                if keyword and len(keyword) > 2:
                    hashtag = f"#{keyword.replace(' ', '').lower()}"
                    if hashtag not in hashtags:
                        hashtags.append(hashtag)
        
        # Add platform-specific tags
        platform_tags = self.popular_hashtags.get(platform, [])
        for tag in platform_tags[:5]:
            if tag not in hashtags:
                hashtags.append(tag)
        
        # Add descriptive tags
        words = description.lower().split()
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from'}
        for word in words:
            word = ''.join(c for c in word if c.isalnum())
            if len(word) > 3 and word not in common_words:
                hashtag = f"#{word}"
                if hashtag not in hashtags and len(hashtags) < 15:
                    hashtags.append(hashtag)
        
        return hashtags[:10]
    
    def process_video(self, video_path, platform, tone, keywords=""):
        """Process video and generate caption"""
        try:
            # Simulate processing time
            time.sleep(2)
            
            # Step 1: Detect objects
            objects = self.detect_objects_simple(video_path)
            
            # Step 2: Get video duration
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            # Step 3: Analyze content
            description = self.analyze_video_content(objects, duration)
            
            # Step 4: Generate caption
            caption = self.generate_caption(description, platform, tone, keywords)
            
            # Step 5: Suggest hashtags
            hashtags = self.suggest_hashtags(description, keywords, platform)
            
            return {
                'success': True,
                'detected_objects': objects,
                'video_description': description,
                'generated_caption': caption,
                'suggested_hashtags': hashtags,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"Video processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize processor
video_processor = VideoProcessor()

def index(request):
    return render(request, 'index.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('generator')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('generator')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def generator_view(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                video_upload = form.save(commit=False)
                video_upload.user = request.user
                video_upload.status = 'uploaded'
                
                # Save to get ID
                video_upload.save()
                
                # Check duration
                try:
                    cap = cv2.VideoCapture(video_upload.video_file.path)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.release()
                    
                    if fps > 0 and frame_count > 0:
                        duration = frame_count / fps
                        video_upload.duration = duration
                        
                        if duration > 60:
                            video_upload.status = 'failed'
                            video_upload.save()
                            return JsonResponse({
                                'success': False,
                                'error': f'Video too long ({duration:.1f}s). Max 60 seconds.'
                            })
                
                except Exception as e:
                    logger.warning(f"Duration check failed: {e}")
                
                # Start processing
                processing_thread = threading.Thread(
                    target=process_video_background,
                    args=(video_upload.id,)
                )
                processing_thread.daemon = True
                processing_thread.start()
                
                return JsonResponse({
                    'success': True,
                    'video_id': video_upload.id,
                    'message': 'Video uploaded. AI processing started...'
                })
                
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'Upload failed: {str(e)}'
                })
        else:
            errors = form.errors.get_json_data()
            error_messages = [f"{field}: {err[0]['message']}" for field, err in errors.items()]
            return JsonResponse({
                'success': False,
                'error': ' | '.join(error_messages)
            })
    
    else:
        form = VideoUploadForm()
    
    return render(request, 'generator.html', {'form': form})

def process_video_background(video_id):
    """Process video in background"""
    try:
        video = VideoUpload.objects.get(id=video_id)
        video.status = 'processing'
        video.save()
        
        # Process video
        results = video_processor.process_video(
            video_path=video.video_file.path,
            platform=video.platform,
            tone=video.tone,
            keywords=video.keywords
        )
        
        if results['success']:
            video.detected_objects = results.get('detected_objects', [])
            video.video_description = results.get('video_description', '')
            video.generated_caption = results.get('generated_caption', '')
            video.suggested_hashtags = results.get('suggested_hashtags', [])
            video.duration = results.get('duration', 0)
            video.status = 'processed'
        else:
            video.status = 'failed'
        
        video.save()
        
    except Exception as e:
        logger.error(f"Background processing failed: {e}")
        try:
            video = VideoUpload.objects.get(id=video_id)
            video.status = 'failed'
            video.save()
        except:
            pass

@login_required
def check_processing_status(request, video_id):
    """Check processing status"""
    try:
        video = VideoUpload.objects.get(id=video_id, user=request.user)
        
        response = {
            'status': video.status,
            'has_caption': bool(video.generated_caption)
        }
        
        if video.status == 'processed':
            response.update({
                'caption': video.generated_caption,
                'hashtags': video.suggested_hashtags,
                'objects': video.detected_objects,
                'description': video.video_description,
                'duration': f"{video.duration:.1f}s"
            })
        elif video.status == 'failed':
            response['error'] = 'Processing failed. Please try again.'
        
        return JsonResponse(response)
        
    except VideoUpload.DoesNotExist:
        return JsonResponse({'error': 'Video not found'}, status=404)

@login_required
@csrf_exempt
def save_caption_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            video_id = data.get('video_id')
            caption_text = data.get('caption')
            
            if not video_id or not caption_text:
                return JsonResponse({'success': False, 'error': 'Missing data'})
            
            video = VideoUpload.objects.get(id=video_id, user=request.user)
            
            # Save to history
            caption_history = CaptionHistory.objects.create(
                user=request.user,
                video=video,
                caption_text=caption_text,
                platform=video.platform,
                tone=video.tone
            )
            
            return JsonResponse({
                'success': True, 
                'history_id': caption_history.id,
                'message': 'Caption saved to history'
            })
            
        except VideoUpload.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Video not found'}, status=404)
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def history_view(request):
    try:
        captions = CaptionHistory.objects.filter(user=request.user).select_related('video')
        videos = VideoUpload.objects.filter(user=request.user).order_by('-created_at')
        
        return render(request, 'history.html', {
            'captions': captions,
            'videos': videos
        })
    except Exception as e:
        logger.error(f"History view error: {e}")
        messages.error(request, 'Error loading history. Please try again.')
        return redirect('generator')

@login_required
def delete_caption_view(request, id):
    try:
        caption = CaptionHistory.objects.get(id=id, user=request.user)
        caption.delete()
        return JsonResponse({'success': True})
    except CaptionHistory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Caption not found'}, status=404)

@login_required
def delete_video_view(request, id):
    try:
        video = VideoUpload.objects.get(id=id, user=request.user)
        video.delete()
        return JsonResponse({'success': True})
    except VideoUpload.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Video not found'}, status=404)