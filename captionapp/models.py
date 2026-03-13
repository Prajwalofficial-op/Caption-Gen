from django.db import models
from django.contrib.auth.models import User
import os
from django.utils import timezone

def user_video_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/videos/user_<id>/<filename>
    return f'videos/user_{instance.user.id}/{timezone.now().strftime("%Y%m%d_%H%M%S")}_{filename}'

class VideoUpload(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube Shorts'),
    ]
    
    TONE_CHOICES = [
        ('friendly', 'Friendly'),
        ('professional', 'Professional'),
        ('funny', 'Funny'),
        ('inspirational', 'Inspirational'),
        ('casual', 'Casual'),
        ('educational', 'Educational'),
        ('dramatic', 'Dramatic'),
    ]
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    video_file = models.FileField(upload_to=user_video_path)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='instagram')
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default='friendly')
    keywords = models.CharField(max_length=500, blank=True)
    
    # Processing results
    detected_objects = models.JSONField(default=list, blank=True, null=True)
    audio_transcript = models.TextField(blank=True)
    video_description = models.TextField(blank=True)
    generated_caption = models.TextField(blank=True)
    suggested_hashtags = models.JSONField(default=list, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    duration = models.FloatField(default=0)  # in seconds
    file_size = models.BigIntegerField(default=0)  # in bytes
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {os.path.basename(self.video_file.name)}"

class CaptionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captions')
    video = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, related_name='histories')
    caption_text = models.TextField()
    platform = models.CharField(max_length=20)
    tone = models.CharField(max_length=20)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        verbose_name_plural = "Caption Histories"
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.used_at.date()}"