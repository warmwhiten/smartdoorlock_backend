import boto3
from django.http import HttpResponse
from django.core import serializers
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.shortcuts import render

from api.models import Video, Phone
from api.serializers import VideoSerializer, PhoneSerializer

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

class Video(APIView) :
    def get(self, request, format = None) :
        try :   
            request_id = request.GET.get('vidname')
            if request_id == 'None' :
                raise FieldDoesNotExist   
            download_url = S3_ACCESS_URL + str(request_id)
            if not download_url :
                raise ObjectDoesNotExist   
            res = {
                's3_link' : download_url
            }
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

    def post(self, request, format = None) :
        try : 
            request_id = request.GET.get('vidname')
            if request_id == 'None' :
                raise FieldDoesNotExist
            session = boto3.session.Session(aws_access_key_id = S3_ACCESS_KEY_ID, aws_secret_access_key = S3_SECRET_ACCESS_KEY, region_name = AWS_REGION)
            s3 = session.client('s3')
            
            target = Video.objects.get(vidname = request_id)
            s3.delete_object(Bucket = S3_STORAGE_BUCKET_NAME, Key = str(target.vidname))
            target.delete()
            return Response(status = status.HTTP_200_OK)
        except FieldDoesNotExist as error :
            return Response({
                'error' : "FieldDoesNotExist ",
                'date' : datetime.now()
            }, status = status.HTTP_400_BAD_REQUEST)

class CheckDate(APIView) :
    def post(self, request, format = None) :
            checkdate = datetime.now() + timedelta(days = -7)
            quaryset = Video.objects.filter(created__lt = checkdate)
            session = boto3.session.Session(aws_access_key_id = S3_ACCESS_KEY_ID, aws_secret_access_key = S3_SECRET_ACCESS_KEY, region_name = AWS_REGION)
            s3 = session.client('s3')
            for delvid in quaryset :
                s3.delete_object(Bucket = S3_STORAGE_BUCKET_NAME, Key = str(delvid.vidname))
            quaryset.delete()
            return Response(status = status.HTTP_200_OK)

    
