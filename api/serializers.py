from api.models import Device, Video, Lock, RemoteHistory, Record, Door
from rest_framework import serializers


class DeviceSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Device
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Video
        fields = '__all__'

class RemoteHistorySerializer(serializers.ModelSerializer) :
    class Meta :
        model = RemoteHistory
        fields = '__all__'

class RecordSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Record
        fields = '__all__'