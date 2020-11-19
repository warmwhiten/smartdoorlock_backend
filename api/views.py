import boto3
import botocore
import threading
from django.http import HttpResponse
from django.core import serializers
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.shortcuts import render

from api.videorecord import record
from api.models import Video, Device, RemoteHistory, Lock, Record, Door, AddDevice
from api.serializers import VideoSerializer, DeviceSerializer, RemoteHistorySerializer, RecordSerializer, LockSerializer, AddDeviceSerializer


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
import json
# Create your views here.

#로그인 및 토큰 반환
class Login(APIView) : 
    def get(self, request, format = None) : # request query에 door_id 포함되어있음 : api/auth?door_id=12345
        try :
            request_id = request.GET.get('door_id', None)
            if request_id == None :
                raise FieldDoesNotExist
            queryset = Door.objects.filter(door_id = request_id) # door_id 유효성 검색
            if queryset.exists() :# 유효할 때
                res = {
                    'is_available' : True,
                    'access_token' : '토큰' # 토큰 도입 후 수정 필요
                }
            else :
                res = {
                    'is_available' : False
                }

            return Response(res, status = status.HTTP_200_OK)

        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

#기기 관련 api
class Devices(APIView) :
    # 기기 목록 조회
    def get(self, request, format = None) : 
        queryset = Device.objects.all()
        serializer = DeviceSerializer(queryset, many = True)
        res = {
            'deviceList': serializer.data
        }
        return Response(res, status = status.HTTP_200_OK)

    # 기기 추가 요청
    def put(self, request, format = None) :
        try :
            print(request.body)
            data = json.loads(request.body)
            target = AddDevice.objects.get(id=1)
            serializer = AddDeviceSerializer(target, many=False)
            state = serializer.data['state']
            if state == False:
                print(">> 기기추가 요청이 들어옴")
                target.state = True
                target.save()
            rfid_id = data.get('rfid_id', None)
            res = {
                'rfid_id': rfid_id
            }
            if rfid_id == None:
                raise FieldDoesNotExist
            return Response(res, status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

    # 기기 추가
    def post(self, request, format = None) : # request body에 rfid_id 포함되어있음 
        try : 
            print(request.body)
            data = json.loads(request.body)
            request_id = data.get('rfid_id', None)
            if request_id == None :
                raise FieldDoesNotExist
            queryset = Device.objects.create(rfid_id = request_id)
            return Response({
                'msg' : 'success device add'
            })

        except FieldDoesNotExist as error : 
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)



    # 기기 삭제
    def delete(self, request, device_id, format = None): # request URI에 device_id(자동생성되는 기기 고유 번호 != rfid_id) 포함
        try : 
            request_id = device_id
            if request_id == None:
                raise FieldDoesNotExist   
            queryset = Device.objects.get(device_id=request_id)
            queryset.delete()
            return Response({
                'msg' : 'success delete device'
            })
        
        except FieldDoesNotExist as error : 
             return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

# 원격 잠금 해제 
class Remote(APIView):
    # 원격 잠금 해제 기록 조회
    def get(self, request, format = None) : 
        #models.py의 class History 사용.
        queryset = RemoteHistory.objects.all()
        serializer = RemoteHistorySerializer(queryset, many = True)
        res = {
            "remoteHistoryList": serializer.data
        }
        return Response(res, status = status.HTTP_200_OK)

    # 원격 잠금 해제
    def post(self, request, format = None) :
        try:
            print(request.body)
            data = json.loads(request.body)
            device_name = data.get('device_name', None)
            if device_name == None :
                raise FieldDoesNotExist
            else:
                # 잠금 상태 변경
                target = Lock.objects.get(id=1)
                serializer = LockSerializer(target, many=False)
                state = serializer.data['state']
                if state == True:
                    print(">> 원격 잠금해제 요청이 들어옴")
                    target.state = False
                    target.save()
            return Response({
                'msg' : 'success remote unlock'
            }, status = status.HTTP_200_OK)
        except FieldDoesNotExist as error:
            return Response({
                'error': "FieldDoesNotExist ",
                'date': datetime.now()
            }, status=status.HTTP_400_BAD_REQUEST)



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
                's3link' : download_url
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
            return Response(status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)
