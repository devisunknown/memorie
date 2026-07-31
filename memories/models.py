from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='family')
    note = models.CharField(max_length=200)
    image = CloudinaryField('image', folder='osei_antwi/memories/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    date_taken = models.DateField(null=True, blank=True)
    filter_style = models.CharField(max_length=20, choices=FILTER_CHOICES, default='none')

    class Meta:
        ordering = ['-date_taken', '-uploaded_at']

    def __str__(self):
        return f"{self.get_category_display()} — {self.user.username}"

    @property
    def is_recent(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.uploaded_at >= timezone.now() - timedelta(days=7)

    @property
    def display_date(self):
        return self.date_taken if self.date_taken else self.uploaded_at.date()