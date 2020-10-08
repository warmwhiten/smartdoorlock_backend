from api.models import Phone, Video
from rest_framework import serializers

class PhoneSerializer(serializers.ModelSerializer) :
    class Meta :
        model = models.Phone
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer) :
    class Meta :
        model = models.Video
        fields = '__all__'
