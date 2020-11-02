from django.contrib import admin
from .models import Video, Device, History, Lock, Record, Door
# Register your models here.
admin.site.register(Door)
admin.site.register(Video)
admin.site.register(Device)
admin.site.register(History)
admin.site.register(Lock)
admin.site.register(Record)