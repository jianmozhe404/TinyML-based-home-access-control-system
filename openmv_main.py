import sensor
import random
import os,tf,uos,gc,pyb,math
import machine
import time
import image
from pyb import LED,Pin,Timer
import json
from pyb import UART
current_time = [2024, 6, 15, 15 ,15, 20]

def set_up_openmv():
    sensor.reset()  # 初始化sensor
    sensor.set_contrast(1)

    # 设置相机的增益上限为16
    sensor.set_gainceiling(16)

    sensor.set_pixformat(sensor.GRAYSCALE)  # 设置图像色彩格式，有RGB565色彩图和GRAYSCALE灰度图两种
    sensor.set_framesize(sensor.QVGA)  # 设置图像像素大小 QVGA (320x240)

    #时钟设置
    global clock
    clock = time.clock()

    #阈值设置
    global THRESHOLD
    THRESHOLD = (19, 53, -52, 127, -78, 127)

    #全局变量设置
    global face_num,state_counter,uart3,uart1,red_led,photonum
    face_num=0
    uart3 = UART(3, 115200)
    uart1 = UART(1,9600)
    state_counter = 5
    photonum=0

    red_led = LED(1)

    # 日志数据结构
    global log_data

    log_data = {
        "motion_detect_count": 0,
        "face_detect_count": 0,
        "specific_face_times": [],

    }

def update_time(time_str):
    global current_time

    print(f"这是update开头的时间{current_time}")
    
    if current_time is None:
        return "Time not set"  # 提供一个默认的响应或错误消息
    
    try:
        gotted_time = [int(part) for part in time_str.split(' ')[0].split('-') + time_str.split(' ')[1].split(':')]
        if  gotted_time[4] >= current_time[4]:
            current_time = gotted_time
            print("Updated time: ", current_time)
            return current_time

           
    
    except ValueError as e:
        print("Error parsing time string:", e)
        return
    
'''
def process_uart():
    if uart3.any():
        data = uart3.read()
        #方便调试
        print(data)

        if data:
            time_str = data.decode().strip()
            if time_str.startswith("TIME:"):
                update_time(time_str[5:])
                #方便调试
                print(data)
'''

def process_uart():
    global current_time

    if current_time is None:
        return "Time not set"  # 提供一个默认的响应或错误消息

    print(f"这是uart开头的时间{current_time}")
    
    if uart3.any():
        data = uart3.read()
        print("Raw data:", data)  # Debugging

        if data:
            try:
                time_str = data.decode().strip()
                print("Decoded time string:", time_str)  # Debugging
                if time_str.startswith("TIME:") and len(time_str) > 5:
                    current_time = update_time(time_str[5:])
                    print(f"这是uart更新后的时间{current_time}")
                    
            except:
                pass        

def generate_log():
    log_str = "Daily Log:\n"
    log_str += "LOG:"+f"Motion detected: {log_data['motion_detect_count']} times\n"
    log_str += "LOG:"+f"Face detected: {log_data['face_detect_count']} times\n"
    log_str += "LOG:"+"Specific faces detected at:\n" + "\n"
    log_str += "LOG:"+ " ".join(log_data["specific_face_times"]) 
    log_str += "%"     #结束标志位
    return log_str

def send_log():
    log = generate_log()
    uart3.write(f"LOG:{log}")
    print("Log sent to ESP8266:\n" + log)

def check_time_and_send_log():
    global current_time

    if current_time is None:
        return "Time not set"  # 提供一个默认的响应或错误消息
    
    current_hour = current_time[3]
    current_minute = current_time[4]
    print(f"这是发送日志前的时间{current_time}")
    # 检查是否到达设定的日志发送时间，例如每天23:59
    if current_hour == 1 and current_minute >= 0:
        send_log()
        time.sleep(20)  # 避免重复发送日志


'''
def send_image_via_uart():
    
    img = sensor.snapshot()

    # 压缩图片并转换为字节流
    img_byte_stream = img.compress(quality=90)  # Adjust quality as needed
    
    # 发送图片数据大小，确保上位机知道应该接收多少数据
    size = img_byte_stream.size()
    uart3.write(bytearray([size >> 24 & 0xFF, size >> 16 & 0xFF, size >> 8 & 0xFF, size & 0xFF]))
    
    # 分块发送图片数据
    for i in range(0, size, 256):
        uart3.write(img_byte_stream[i:i+256])
        time.sleep(50)  # 适当延时以避免发送过快

    print("Image sent via UART.")

def send_image_via_uart():
    
    print("hello")
    img = sensor.snapshot()

    # 压缩图片并转换为字节流
    img_byte_stream = img.compress(quality=90)  # Adjust quality as needed
    
    print("hi")
    # 发送图片数据大小，确保上位机知道应该接收多少数据
    size = img_byte_stream.size()
    uart3.write(bytearray([size >> 24 & 0xFF, size >> 16 & 0xFF, size >> 8 & 0xFF, size & 0xFF]))
    
    print(img_byte_stream)
    # 分块发送图片数据
    for i in range(0, size, 256):
        chunk = img_byte_stream[i:i+256]
        
        if not isinstance(chunk, (bytearray, bytes)):
            chunk = bytearray(chunk)  # 确保传递的是bytearray或bytes
        uart3.write(chunk)
        print(chunk)
        time.sleep(50)  # 适当延时以避免发送过快

    print("Image sent via UART.")
    time.sleep(50)

'''
#@log_event("motion_detect")
def motion_detection():

    red_led.on()
    time.sleep_ms(500)
    red_led.off()

    count = 0
    while True:
        clock.tick()
        previous_image = sensor.snapshot()
        current_image = sensor.snapshot()
        difference_image = current_image.difference(previous_image)
        stats = difference_image.statistics()

       
        process_uart()     #获取时间
        check_time_and_send_log()     #检查时间和发送日志

        #检测差异量,大于阈值则为运动
        if stats[5] > 20:
            print('something moved')
            count += 1
            
            blobs = difference_image.find_blobs([THRESHOLD], invert=False, x_stride=10, y_stride=10, area_threshold=300, merge=True)
            for blob in blobs:
                difference_image.draw_rectangle(blob.rect())
        else:
            print('nothing happened')
            count = 0

        if count >= 10:
            log_data["motion_detect_count"] += 1
            data = bytearray([0x76, 0x61, 0x30, 0x2E, 0x76, 0x61, 0x6C, 0x3D, 0x31, 0xFF, 0xFF, 0xFF])
            uart1.write(data)
            return

#@log_event("face_detection")
def face_detection():

    red_led.on()
    time.sleep_ms(500)
    red_led.off()

    face_detected_count = 0

    #加载人脸模型
    face_cascade = image.HaarCascade("frontalface", stage=25)

    while True:

        process_uart()     #获取时间

        # 更新FPS时钟
        clock.tick()

        # 拍摄图片并返回img
        img = sensor.snapshot()

        # 寻找人脸对象
        objects = img.find_features(face_cascade, threshold=0.75, scale_factor=1.25)

        # 用矩形将人脸画出来
        for r in objects:
            face_detected_count += 1
            img.draw_rectangle(r)
            print(r)
        
        if face_detected_count >= 5:
            log_data["face_detect_count"] += 1
            data = bytearray([0x76, 0x61, 0x31, 0x2E, 0x76, 0x61, 0x6C, 0x3D, 0x31, 0xFF, 0xFF, 0xFF])
            uart1.write(data)
            return 0


def specific_face_recognition():

    red_led.on()
    time.sleep_ms(500)
    red_led.off()

    global current_time
    print(f"这是特定人脸识别前的时间{current_time}")
    std1_count = 0
    std2_count = 0
    face_num = 0
    detection_count = 0

    net = None
    labels = None
    min_confidence = 0.5
    
    try:
        # 加载模型，如果加载后至少有64K的空闲内存，则将模型文件分配在堆上
        net = tf.load("trained.tflite", load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))
    except Exception as e:
        raise Exception('加载 "trained.tflite" 失败，请确认 .tflite 和 labels.txt 文件已复制到存储设备上? (' + str(e) + ')')

    try:
        # 加载标签
        labels = [line.rstrip('\n') for line in open("labels.txt")]
    except Exception as e:
        raise Exception('加载 "labels.txt" 失败，请确认 .tflite 和 labels.txt 文件已复制到存储设备上? (' + str(e) + ')')

    clock = time.clock()
    while True:
        
        process_uart()     #获取时间
        
        clock.tick()
        img = sensor.snapshot()

        detection_count += 1
        for i, detection_list in enumerate(net.detect(img, thresholds=[(math.ceil(min_confidence * 255), 255)])):
            if i == 0:
                continue  # 跳过背景类
            if len(detection_list) == 0:
                continue  # 该类没有检测到对象

            if labels[i] == '1':
                std1_count += 1
                std2_count = 0
                face_num += 1
                if std1_count >= 40:
                    print("同学一")
                    
                    data = bytearray([0x76, 0x61, 0x32, 0x2E, 0x76, 0x61, 0x6C, 0x3D, 0x31, 0xFF, 0xFF, 0xFF])
                    uart1.write(data)
                    
                    log_data["specific_face_times"].append(f"{'STD 1'} at {current_time[3]} {current_time[4]}" + "\n")
                    return
            elif labels[i] == '2':
                std1_count = 0
                std2_count += 1
                face_num += 1
                if std2_count >= 10:
                    print("同学二")
                    print(f"这是检测前的时间{current_time}")
                    data = bytearray([0x76, 0x61, 0x32, 0x2E, 0x76, 0x61, 0x6C, 0x3D, 0x32, 0xFF, 0xFF, 0xFF])
                    uart1.write(data)
                    
                    log_data["specific_face_times"].append(f"{"STD 2"} at {current_time[3]} {current_time[4]}"+ "\n")
                    return
            elif detection_count >= 200:
                print("陌生人")
                
                data = bytearray([0x76, 0x61, 0x32, 0x2E, 0x76, 0x61, 0x6C, 0x3D, 0x33, 0xFF, 0xFF, 0xFF])
                uart1.write(data)
                log_data["specific_face_times"].append(f"{"stranger"} at {current_time[3]} {current_time[4]}"+ "\n")
                sensor.snapshot().save("/photo%s-%s/%s.pgm" % current_time[1],current_time[2],photonum)

                return
        
            print(std1_count, std2_count, face_num, detection_count)
        check_time_and_send_log()     #检查时间和发送日志
        

set_up_openmv()

while(True):
    
    if state_counter==5 or state_counter==0:
        if state_counter==0:
            state_counter=5
        motion_detection()
    if state_counter==3:
        state_counter=5
        break
    if state_counter==0:
        state_counter=5
        continue
    if state_counter==5 or state_counter==1:
        if state_counter==1:
            state_counter=5
        face_detection()
    if state_counter==3:
        state_counter=5
        break
    if state_counter==0 or state_counter==1:
        if state_counter==0:
            state_counter=5
        continue
    if state_counter==5 or state_counter==2:
        if state_counter==2:
            state_counter=5
        specific_face_recognition()
    if state_counter==3:
        state_counter=5
        break
    if state_counter==0 or state_counter==1 or state_counter==2:
        if state_counter==0:
            state_counter=5
        continue
    
    photonum += 1
    #send_image_via_uart()
    time.sleep_ms(10000)






