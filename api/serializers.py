from api.models import Phone, Video
from rest_framework import serializers


class PhoneSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Device
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Video
        fields = '__all__'
