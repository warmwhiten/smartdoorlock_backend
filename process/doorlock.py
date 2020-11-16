#-*- coding:utf-8 -*-

import time
import RPi.GPIO as GPIO
from multiprocessing import Queue
import os

PIN = {
	'Motor_MT_N':17,
	'Motor_MT_P':4
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
		################## 이곳을 지우고 코드를 작성해주세요 ################
		# RFID ID가 등록된 기기의 ID인 경우 success에 True를 넣습니다.
		#
		# RFID 태그가 된 경우 API에 요청을 보내 (GET /api/device) ID 목록을
		# 가져온 후 이 목록 안에 태그된 기기의 ID가 있는지 여부를 확인하는 방식으로
		# 동작하면 될 것 같습니다.
		#
		# ID 목록을 미리 받아온 후 비교하도록 하면 ID 목록 업데이트가 안 될 수 있으니
		# 태그가 된 경우 ID 목록을 받아오도록 해주세요.
		#
		# 기기 추가 상태인 경우를 확인해 기기 추가 상태라면 success를 True로 하지 않고
		# 그냥 기기 목록에 태그된 기기의 ID를 추가합니다.
		#
		# success가 True인 경우 모터가 회전합니다.
		#
		# 아래 코드는 테스트를 위한 코드입니다. 아래 코드까지 지우고 작성해주세요.
		time.sleep(30)
		success = True
		##############################################################
		#
		# 복잡한 것 같아 수도코드를 첨부합니다.
		#
		# success = False
		# if RFID 태그가 됨:
		#   deviceId = 방금 태그된 RFID 장치의 ID
		#   devices = callApi(GET /api/device)
		#   state = getFromIPC(원격 잠금해제 여부)
		#
		#   if state == 원격 잠금해제:
		#     try:
		#       if devices.find(deviceId):
		#         raise 이미 등록된 RFID 장치
		#       else:
		#         callApi(POST /api/device, {rfid_id:deviceId})
		#         (가능하다면) 완료됐다는 소리 출력 (딩동댕 정도?)
		#     except:
		#       (가능하다면) 경고음 출력 (삑!)
		#     finally:
		#       setToIPC(원격 잠금해제 여부, 원격 잠금해제 아님)
		#   else: # 원격 잠금해제 상태가 아님 = 도어락 해제 프로세스
		#     try:
		#       if not devices.find(deviceId):
		#         raise 등록되지 않은 RFID 장치
		#       else:
		#         success = True
		#     except:
		#       (가능하다면) 경고음 출력 (삑!)
		#
		##############################################################
		if success:
			print("등록된 RFID ID가 확인됨")
			signalQueue.put("RFID")

def RemoteProcess(signalQueue):
	while True:
		################## 이곳을 지우고 코드를 작성해주세요 ################
		# 원격 잠금해제 요청이 들어온 경우 success에 True를 넣습니다.
		# 원격 잠금해제 요청은 IPC로 처리합니다.
		# 지우님과 협업하여 작업해주세요.
		# 
		# 제 생각으로는 한 파일에 대해서 (ex ~/IPC.txt) API에서는 write하고
		# 도어락 프로세스에서는 read하는 방법으로 하면 될 것 같습니다.
		# 원격 잠금해제 요청이 들어온 경우 API에서 write하도록 하면 되겠죠..?
		#
		# success가 True인 경우 모터가 회전합니다.
		#
		# 아래 코드는 테스트를 위한 코드입니다. 아래 코드까지 지우고 작성해주세요.
		time.sleep(13)
		success = True
		##############################################################
		if success:
			print("원격 잠금해제 요청이 들어옴")
			signalQueue.put("Remote")

def signalProcess(signalQueue):
	pid = os.fork()
	if pid == 0:
		RFIDProcess(signalQueue)
	else:
		RemoteProcess(signalQueue)

def doorProcess(doorQueue):
	motor = Motor()
	while True:
		signal = doorQueue.get()
		print("{} 신호를 받아 문 열기 동작 수행 시작".format(signal))
		if signal is not None:
			print("문 열림")
			motor.rotate(Motor.LEFT)
			time.sleep(0.5)
			motor.stop()
			time.sleep(5)				# 열린 후 5초 지나면 닫힘
			print("문 닫힘")
			motor.rotate(Motor.RIGHT)
			time.sleep(0.5)
			motor.stop()

if __name__ == '__main__':
	try:
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(PIN['Motor_MT_N'], GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(PIN['Motor_MT_P'], GPIO.OUT, initial=GPIO.LOW)
		
		signalQueue = Queue()
		pid = os.fork()
		if pid == 0:
			doorQueue = Queue()
			pid = os.fork()
			if pid == 0:
				while True:
					signal = signalQueue.get()
					print("{} 신호가 들어와 전달 준비".format(signal))
					if signal is not None:
						doorQueue.put(signal)
			else:
				doorProcess(doorQueue)
		else:
			signalProcess(signalQueue)
	except Exception as e:
		print(e)
	finally:
		GPIO.cleanup()