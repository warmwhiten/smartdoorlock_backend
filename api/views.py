import boto3
from django.http import HttpResponse
from django.core import serializers
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.shortcuts import render

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
from datetime import datetime, timedelta
# Create your views here.

# 비디오 목록 조회
class VideoList(APIView) : 
    def get(self, request, format = None) :
        '''
            request_id = request.GET.get('last_id') # requst의 last_id 받아옴
            queryset = Video.objects.filter(vid_id__range = (request_id, request_id + 10))   # 쿼리셋 필터로 vid_id의 범위가 last_id ~ las_id + 10인 객체 찾기
        '''
        queryset = Video.objects.all()
        serializer = VideoSerializer(queryset, many = True)
        res = {     
            'videoList': serializer.data
        }       # 응답코드에 포함될 데이터
        return Response(res, status = status.HTTP_200_OK) 

# 비디오 수동 삭제
    def delete(self, request, vid_id, format = None) :  # request URI에 vid_id가 포함되어있음 : api/video/{vid_id}
        try : 
            request_id = vid_id
            if request_id == 'None' :
                raise FieldDoesNotExist
            session = boto3.session.Session(aws_access_key_id = S3_ACCESS_KEY_ID, aws_secret_access_key = S3_SECRET_ACCESS_KEY, region_name = AWS_REGION)
            s3 = session.client('s3')
            
            target = Video.objects.get(vid_id = request_id)
            s3.delete_object(Bucket = S3_STORAGE_BUCKET_NAME, Key = str(target.vid_id))
            target.delete()
            return Response(status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

# 비디오 확인(다운로드)
class VideoDownload(APIView) :
    def get(self, request, vid_id, format = None) : # 요청한 URI에 vid_id가 포함되어있음 ex) api/video/1
        try :   
            request_id = vid_id
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
                s3.delete_object(Bucket = S3_STORAGE_BUCKET_NAME, Key = str(delvid.vid_id))
            quaryset.delete()
            return Response(status = status.HTTP_200_OK)

# 비디오 녹화 설정 조회/변경
class Recording(APIView) :
    def get(self, request, format = None) :
        try :
            '''
            request_id = request.GET.get('door_id')
            target = Record.objects.filter(door_id = request_id)
            '''
            target = Record.objects.all()
            serializer = RecordSerializer(target, many = True)
            res = {
                'recording' : serializer.data
            }
            return Response(res, status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

    def put(self, request, format = None) :
        try :  
            request_id = request.GET.get('door_id')
            if not request_id :
                raise FieldDoesNotExist
            target = Record.objects.filter(door_id = request_id)
            target.update(recording = request.data['recording'])
            return Response(status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)
