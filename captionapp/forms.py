from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import VideoUpload
import os

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = VideoUpload
        fields = ['video_file', 'platform', 'tone', 'keywords']
        widgets = {
            'video_file': forms.FileInput(attrs={
                'accept': 'video/*',
                'class': 'video-upload-input'
            }),
            'keywords': forms.TextInput(attrs={
                'placeholder': 'E.g., travel, adventure, nature (comma separated)'
            })
        }
    
    def clean_video_file(self):
        video_file = self.cleaned_data.get('video_file')
        if video_file:
            # Check file size (100MB max)
            max_size = 100 * 1024 * 1024
            if video_file.size > max_size:
                raise forms.ValidationError("Video file is too large (max 100MB)")
            
            # Check file extension
            valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv']
            ext = os.path.splitext(video_file.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(f"Unsupported file format. Supported formats: {', '.join(valid_extensions)}")
            
            # Check duration (will be validated during processing)
            # We'll handle this in the view after saving
            
        return video_file