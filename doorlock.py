# -*- coding:utf-8 -*-

import time
import RPi.GPIO as GPIO
import mfrc522
import requests
from multiprocessing import Queue
import os
import django
import datetime
import sys

sys.path.append('/home/pi/Desktop/smartdoorlock-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
django.setup()

from django.core import serializers
from api.models import Lock, AddDevice, Device
from api.serializers import LockSerializer, AddDeviceSerializer, DeviceSerializer


GPIO.setmode(GPIO.BCM)
MFIAREReader = mfrc522.MFRC522()  # RFID Reader
BASE_URL = "http://127.0.0.1:8000"
PIN = {
    'Motor_MT_N': 12,
    'Motor_MT_P': 6
}


class Motor:
    LEFT = 0
    RIGHT = 1

    def __init__(self):
        self.pwmN = GPIO.PWM(PIN['Motor_MT_N'], 100)
        self.pwmP = GPIO.PWM(PIN['Motor_MT_P'], 100)
        self.pwmN.start(0)
        self.pwmP.start(0)

    def rotate(self, direction):
        if direction == Motor.LEFT:
            GPIO.output(PIN['Motor_MT_N'], GPIO.HIGH)
            GPIO.output(PIN['Motor_MT_P'], GPIO.LOW)
            self.pwmN.ChangeDutyCycle(50)
        else:
            GPIO.output(PIN['Motor_MT_N'], GPIO.LOW)
            GPIO.output(PIN['Motor_MT_P'], GPIO.HIGH)
            self.pwmP.ChangeDutyCycle(50)

    def stop(self):
        self.pwmP.ChangeDutyCycle(0)
        self.pwmN.ChangeDutyCycle(0)


def RFIDProcess(signalQueue):
    while True:
        success = False
        try:
            (readerStatus, tagType) = MFIAREReader.MFRC522_Request(MFIAREReader.PICC_REQIDL)
            (readerStatus, uid) = MFIAREReader.MFRC522_Anticoll()  # uid = [1, 2, 3, 4, 5]
            if readerStatus == MFIAREReader.MI_OK:  # if RFID 태그가 됨:
		time.sleep(1)
                print("RIFD tag")
                deviceId = ""   # 방금 태그된 RFID 장치의 ID.
                for i in uid:
                    deviceId += str(i)  # deviceId = 12345
                print("DeviceID : ", deviceId)

                # devices = callApi(GET /api/device)  # 기기 조회
                response = requests.get(BASE_URL+"/api/device")
                deviceList = []  # 기기 목록
                if response.status_code == 200:
                    print("Success view device list")
                    deviceList = (response.json()['deviceList'])
                print("device list : ", deviceList)
                # state = getFromIPC(기기추가여부)

                target = AddDevice.objects.get(id=1)  # 장고 모델에서 AddDevice 객체 가져옴
                serializer = AddDeviceSerializer(target, many=False)  # python 데이터타입으로 변환
                state = serializer.data['state']  # state에 저장(boolean)

                findDevice = False  # 기기 등록 여부
                for i in deviceList:
                    if deviceId in i["rfid_id"]:
                        findDevice = True
                print("findDevice : ", findDevice)
                if state == True:  #  if state == 기기추가:
                    print("1-1 AddDevice is True")
                    try:
                        if findDevice:  # if devices.find(deviceId):
                            print("이미 등록된 RFID 장치")  # raise
                            pass
                        else:
                            # callApi(POST /api/device, {rfid_id:deviceId})  # 기기 추가
                            requests.post(BASE_URL+"/api/device", data={"rfid_id": deviceId})
                            print("딩동댕 ~ 완료하였습니다")  # 소리 출력
                            pass
                    except:
                        print("경고음 삑 -!")
                        pass
                    finally:  # setToIPC(기기 추가 여부, 기기 추가 아님)
                        target.state = False
                        target.save()
                else:  # 기기 추가 상태가 아님 = 도어락 해제 프로세스
                    print("1-2 Open Door")
                    try:
                        if not findDevice:  # if not devices.find(deviceId)
                            print("등록되지 않은 RFID 장치")  # raise
                            pass
                        else:
                            success = True
                    except:
                        print("경고음 삑 -!")  # 소리 출력
                        pass

            if success:
                print("등록된 RFID ID가 확인됨")
                signalQueue.put("RFID")
        except KeyboardInterrupt:
            GPIO.cleanup()
            break


def RemoteProcess(signalQueue):
    while True:
        success = False
        target = Lock.objects.get(id=1)  # 장고 모델에서 잠금 상태 모델(Lock) 객체 가져옴
        serializer = LockSerializer(target, many=False)  # python 데이터타입으로 변환
        state = serializer.data['state']  # state에 저장(boolean)
        if state == False:  # 잠금 해제 요청이 왔을 경우
            print(">> 원격 잠금해제 요청이 들어옴")
            success = True
            target.state = True  # 다시 잠금 상태로
            target.save()  # 바꾼 값으로 db에 저장
        if success:
            signalQueue.put("Remote")


def signalProcess(signalQueue):
    pid = os.fork()
    if pid == 0:
        RFIDProcess(signalQueue)
    else:
        RemoteProcess(signalQueue)


def doorProcess(doorQueue):
    # motor = Motor()
    while True:
        signal = doorQueue.get()
        print("{} 신호를 받아 문 열기 동작 수행 시작".format(signal))
        if signal is not None:
            print("문 열림")
            #motor.rotate(Motor.LEFT)
            time.sleep(0.5)
            #motor.stop()
            time.sleep(5)  # 열린 후 5초 지나면 닫힘
            print("문 닫힘")
            #motor.rotate(Motor.RIGHT)
            time.sleep(0.5)
            #motor.stop()


if __name__ == '__main__':
    try:
        GPIO.setmode(GPIO.BCM)
        #GPIO.setup(PIN['Motor_MT_N'], GPIO.OUT, initial=GPIO.LOW)
        #GPIO.setup(PIN['Motor_MT_P'], GPIO.OUT, initial=GPIO.LOW)

        signalQueue = Queue()
        pid = os.fork()
        if pid == 0:
            doorQueue = Queue()
            pid = os.fork()
            if pid == 0:
                while True:
                    signal = signalQueue.get()
                    print(signal)
                    print("{} 신호가 들어와 전달 준비".format(signal))
                    print(signal)
                    if signal is not None:
                        print("signal is not None")
                        doorQueue.put(signal)
            else:
                doorProcess(doorQueue)
        else:
            signalProcess(signalQueue)
    except Exception as e:
        raise e
    finally:
        GPIO.cleanup()
