from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class Device(models.Model) :
    username = models.CharField(max_length = 255)
    and_id = models.CharField(max_length = 255, primary_key = True)


class Video(models.Model) :
    vidname = models.CharField(max_length = 255, primary_key = True)
    created = models.DateTimeField(default = timezone.now)
    s3_link = models.CharField(max_length = 255)

class Lock(models.Model) :
    state = models.BooleanField(default = True)

class History(models.Model) :
    device = ForeignKey(Device, on_delete=models.CASCADE)
    ctrtime = created = models.DateTimeField(default = timezone.now)