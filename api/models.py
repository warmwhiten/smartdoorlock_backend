from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class Door(models.Model) :
    door_id = models.CharField(max_length = 255, primary_key = True)

class Device(models.Model) :
    rfid_id = models.CharField(max_length = 255, primary_key = True)
    created = models.DateTimeField(default = timezone.now)

class Video(models.Model) :
    vid_id = models.IntegerField(primary_key = True)
    created = models.DateTimeField(default = timezone.now)
    s3_link = models.CharField(max_length = 255)

class Lock(models.Model) :
    door = models.ForeignKey(Door, on_delete=models.CASCADE)
    state = models.BooleanField(default = True)

class History(models.Model) :
    device_name = models.CharField(max_length = 255)
    ctrtime = models.DateTimeField(default = timezone.now)

class Record(models.Model) :
    door = models.ForeignKey(Door, on_delete=models.CASCADE)
    recording = models.BooleanField(default = True)