import boto3
import botocore
import threading
from django.http import HttpResponse
from django.core import serializers
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.shortcuts import render

from api.videorecord import record
from api.models import Video, Device, History, Lock, Record, Door
from api.serializers import VideoSerializer, DeviceSerializer, HistorySerializer, RecordSerializer

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
"""
from boto3.session import Session
from src.settings import AWS_REGION
from src.settings import S3_ACCESS_URL
from src.settings import S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_STORAGE_BUCKET_NAME
"""
import time
from datetime import datetime, timedelta
# Create your views here.

#로그인 및 토큰 반환
class Login(APIView) : 
    def get(self, request, format = None) : # request query에 door_id 포함되어있음 : api/auth?door_id=12345
        try :
            request_id = request.GET.get('door_id', None)
            if request_id == 'None' :
                raise FieldDoesNotExist
            queryset = Door.objects.filter(door_id = request_id) # door_id 유효성 검색
            if queryset.exists() # 유효할 때
                res = {
                    'is_available' : True
                    'access_token' : '토큰' # 토큰 도입 후 수정 필요
                }
            else
                res = {
                    'is_available' : False
                }

            return Response(res, status = status.HTTP_200_OK)

        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

#기기 관련 api
class Device(APIView) :
    # 기기 추가
    def post(self, request, format = None) : # request query에 device_id 포함되어있음 : api/device?device_id=12345
        try : 
            request_id = request.POST.get('device_id', None)
            if request_id == 'None' :
                raise FieldDoesNotExist
            queryset = Device.objects.create(rfid_id = request_id)

        except FieldDoesNotExist as error : 
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

    # 기기 목록 조회
    def get(self, request, format = None) : 
        queryset = Device.objects.all()
        serializer = DeviceSerializer(queryset, many = True)
        res = {
            'deviceList': serializer.data
        }
        return Response(res, status = status.HTTP_200_OK)

    # 기기 삭제
    def delete(self, request, device_id, format = None): # request URI에 device_id 포함
        try : 
            request_id = device_id
            if request_id == 'None':
                raise FieldDoesNotExist
            queryset = Device.objects.get(device_id=request_id)
            queryset.delete()
        
        except FieldDoesNotExist as error : 
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

# 원격 잠금 해제 기록 조회
class History(APIView):
    def get(self, request, format = None) : 
        queryset = History.objects.all()
        serializer = HistorySerializer(queryset, many = True)
        res = {
            'deviceList': serializer.data
        }
        return Response(res, status = status.HTTP_200_OK)

# 비디오 목록 조회
class VideoList(APIView) : 
    def get(self, request, format = None) :
        queryset = Video.objects.all()
        serializer = VideoSerializer(queryset, many = True)
        res = {     
            'videoList': serializer.data
        }       # 응답코드에 포함될 데이터
        return Response(res, status = status.HTTP_200_OK) 

# 비디오 수동 삭제
    def delete(self, request, vid_name, format = None) :  # request URI에 vid_name가 포함되어있음 : api/video/{vid_name}
        try : 
            request_id = vid_name
            if request_id == 'None' :
                raise FieldDoesNotExist
            session = boto3.session.Session(aws_access_key_id = S3_ACCESS_KEY_ID, aws_secret_access_key = S3_SECRET_ACCESS_KEY, region_name = AWS_REGION)
            s3 = session.client('s3')
            
            target = Video.objects.get(vid_name = request_id)
            s3.delete_object(Bucket = S3_STORAGE_BUCKET_NAME, Key = str(target.vid_name))
            target.delete()
            return Response(status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

# 비디오 확인(다운로드)
class VideoDownload(APIView) :
    def get(self, request, vid_name, format = None) : # 요청한 URI에 vid_name가 포함되어있음
        try :   
            request_id = vid_name
            if request_id == 'None' :
                raise FieldDoesNotExist   
            download_url = S3_ACCESS_URL + str(request_id)  # S3 다운로드 링크 변환
            if not download_url :
                raise ObjectDoesNotExist   
            res = {
                's3_link' : download_url
            }   # 응답 코드에 보낼 데이터
            return Response(res, status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as error :
            return Response({
                'error' : "ObjectDoesNotExist",
                'date' : datetime.now()
            }, status = status.HTTP_404_NOT_FOUND)

# 비디오 자동 삭제
class CheckDate(APIView) :
    def delete(self, request, format = None) :
            checkdate = datetime.now() + timedelta(days = -7)
            quaryset = Video.objects.filter(created__lt = checkdate)
            session = boto3.session.Session(aws_access_key_id = S3_ACCESS_KEY_ID, aws_secret_access_key = S3_SECRET_ACCESS_KEY, region_name = AWS_REGION)
            s3 = session.client('s3')
            for delvid in quaryset :
                s3.delete_object(Bucket = S3_STORAGE_BUCKET_NAME, Key = str(delvid.vid_name))
            quaryset.delete()
            return Response(status = status.HTTP_200_OK)

# 비디오 녹화 설정 조회/변경
class Recording(APIView) :
    def get(self, request, format = None) :
        try :
            target = Record.objects.get(id = 1)
            serializer = RecordSerializer(target, many = False)
            res = {
                'recording' : serializer.data['recording']
            }
            return Response(res, status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

    def put(self, request, format = None) :
        try :  
            target = Record.objects.filter(id = 1)
            target.update(recording = request.data['recording'])

            if request.data['recording'] :
                threading.Thread(target=record).start()

            return Response(status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)
