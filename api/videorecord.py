import os
import boto3
import botocore
import time
import datetime
from django.core import serializers

from api.models import Video, Record
from api.serializers import VideoSerializer, RecordSerializer
'''
import picamera
from boto3.session import Session
from src.settings import AWS_REGION, S3_ACCESS_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_STORAGE_BUCKET_NAME
'''

def record() :
    path = '/home/pi/recorded'  # 저장할 경로
    state = True

    while state :
        target = Record.objects.get(id = 1)
        serializer = RecordSerializer(target, many = False)
        state = serializer.data['recording']
        with picamera.Picamera() as camera :
            camera.resolution = [320,240]
            now = datetime.datetime.now()
            vid_name = now.strftime('%Y%m%d-%H%M%S')

            vid_path = path + '/' + vid_name + '.h264'
            camera.start_recording(output = vid_path)
            camera.wait_recording(10)
            camera.stop_recording()

            s3 = boto3.client('s3', region_name = 'ap-northeast-2')
            s3.upload_file(Filename = vid_path, Bucket = S3_STORAGE_BUCKET_NAME, Key = vid_name)

            uploadVideo = {}
            uploadVideo['vid_name'] = vid_name
            uploadVideo['created'] = now
            serializer = VideoSerializer(data = uploadVideo)
            serializer.save()

            os.remove(vid_path)