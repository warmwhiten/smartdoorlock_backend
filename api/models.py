from django.db import models
from django.utils import timezone

# Create your models here.
class Phone(models.Model) :
    username = models.CharField(max_length = 255)
    and_id = models.CharField(max_length = 255, primary_key = True)

class Video(models.Model) :
    vidname = models.CharField(max_length = 255)
    created = models.DateTimeField(default = timezone.now)
    s3_link = models.CharField(max_length = 255)