import os
import boto3
import botocore
import time
import datetime

from django.core import serializers
from api.models import Video, Record
from api.serializers import VideoSerializer, RecordSerializer
'''
from boto3.session import Session
from src.settings import AWS_REGION, S3_ACCESS_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_STORAGE_BUCKET_NAME
import RPi.GPIO as GPIO
from picamera import PiCamera
'''

def record() :
    path = '/home/pi/recorded'  # save path

    target = Record.objects.get(id = 1)
    serializer = RecordSerializer(target, many = False)
    state = serializer.data['recording']
    #'''
    # rpi setting
    GPIO.setmode(GPIO.BCM)
    pir_pin = 7
    GPIO.setup(pir_pin, GPIO.IN)
    camera = PiCamera()
    #'''

    try:
        while state :
            if GPIO.input(pir_pin):  # motion detected
                # take a video
                camera.resolution = [320, 240]
                camera.start_preview()

                now = datetime.datetime.now()
                start_time = time.time()

                vid_name = now.strftime('%Y%m%d-%H%M%S')
                vid_path = path + '/' + vid_name + '.h264'
                thumbnail_path = path + '/' + vid_name + '.jpg'

                camera.start_recording(output=vid_path)
                time.sleep(1)
                camera.capture(thumbnail_path)
                while GPIO.input(pir_pin) :
                    print("recoring..")
                    time.sleep(2)
                camera.stop_recording()
                camera.stop_preview()
                
                rec_time = time.time() - start_time
                vid_time = rec_time.strftime("%H:%M:%S")

                # s3 upload
                '''
                s3 = boto3.client('s3', region_name = 'ap-northeast-2')
                s3.upload_file(Filename = vid_path, Bucket = S3_STORAGE_BUCKET_NAME, Key = vid_name)
                s3.upload_file(Filename = thumbnail_path, Bucket = S3_STORAGE_BUCKET_NAME, Key = vid_name + '_thumb')
    
                uploadVideo = {}
                uploadVideo['vid_name'] = vid_name
                uploadVideo['created'] = now
                uploadVideo['vid_time'] = vid_time
                uploadVideo['thumb'] = S3_ACCESS_URL + vid_name + '_thumb'
                serializer = VideoSerializer(data = uploadVideo)
                serializer.save()
                '''
                print(vid_path, "upload success")
                os.remove(vid_path)
            else:
                camera.stop_preview()
    except KeyboardInterrupt:
        print("quit")
        GPIO.cleanup()


if __name__ == '__main__':
    record()
