import uuid

from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField




class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    profile_picture = CloudinaryField('profile_picture', folder='osei_antwi/profiles/', null=True, blank=True)
    
    
    
    @property
    def total_memories(self):
      return Image.objects.filter(user=self).count()
  
    def __str__(self):
      return self.user.username
    

class Album(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    owner = models.ForeignKey(UserProfile,
        on_delete=models.CASCADE,
        related_name='albums'
    )
    
    
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


    def __str__(self):
      return f"{self.title} ({self.owner})"

class Image(models.Model):
    CATEGORY_CHOICES = [
        ('family', 'Family'),
        ('travel', 'Travel'),
        ('milestones', 'Milestones'),
        ('mariage', 'Mariage'),
        ('celebrations', 'Celebrations'),
        ('childhood','Childhood'),
        ('pati','Pati'),
        ('eno','Eno'),
        ('nana_kwadwo','Nana kwadwo'),
        ('daddy','Daddy'),
        ('mummy','Mummy'),
    ]

    FILTER_CHOICES = [
        ('none', 'Original'),
        ('sepia', 'Sepia'),
        ('grayscale', 'B&W'),
        ('warm', 'Warm'),
        ('cool', 'Cool'),
        ('vintage', 'Vintage'),
    ]

    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='images'
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    image = CloudinaryField("image")
    note = models.TextField(blank=True)
    category = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filter_style = models.CharField(
    max_length=20,
    choices=FILTER_CHOICES,
    default='none'
)
    category = models.CharField(
    max_length=50,
    choices=CATEGORY_CHOICES
)

    class Meta:
        ordering = [ '-uploaded_at']

    def __str__(self):
      return f"{self.get_category_display()} — {self.user.user.username}"

    @property
    def is_recent(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.uploaded_at >= timezone.now() - timedelta(days=7)
    
    
    @property
    def display_date(self):
       return self.uploaded_at.date()

    @property
    def download_url(self):
        
        url = self.image.url
        if 'res.cloudinary.com' in url and '/image/upload/' in url:
            return url.replace('/image/upload/', '/image/upload/fl_attachment/')
        return url


from django.conf import settings

    


# memories/models.py


class AlbumShare(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='shared_albums')
    invited_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sent_invites')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('album', 'shared_with')  # can't invite the same person twice

    def __str__(self):
     return f"{self.album.title} → {self.shared_with.user.username} ({self.status})"
 
 
 
class GuestAccess(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='guest_requests')
    name = models.CharField(max_length=150)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} → {self.album.title} ({self.status})"