import socket
import time
from datetime import datetime
import threading
import os

# ESP8266的IP地址和端口号
esp_ip = '192.168.230.233'  # ESP8266的实际IP地址  192.168.230.233
computer_ip = '192.168.230.132'
time_port = 8080
log_port = 10000
image_port = 9000

'''
局域网连接情况介绍:
1. 使用手机热点模拟家庭WiFi
2. esp8266和上位机连接到手机热点
3. esp8266和上位机通过局域网下分配的ip地址寻址和连接
'''

def send_command(command, port):
    try:
        # 创建一个新的套接字
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # 连接到指定IP地址和端口的服务器
        client_socket.connect((esp_ip, port))
        
        # 打印正在发送的命令和端口信息
        print(f"Sending command to port {port}: {command}")
        
        # 将命令发送到服务器，命令以换行符结尾
        client_socket.sendall((command + '\n').encode())
        
        # 关闭套接字连接
        client_socket.close()
        
    except Exception as e:
        # 如果出现异常，打印错误信息
        print(f"Error: {e}")

        

def get_current_time():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return current_time

def send_time_periodically(interval):
    while True:
        current_time = get_current_time()
        send_command(f"TIME:{current_time}", time_port)
        time.sleep(interval)
'''
def receive_logs():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', log_port))
    server_socket.listen(1)
    print(f"Listening for logs on port {log_port}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        data = client_socket.recv(4096).decode()
        if data.startswith("LOG:"):
            save_log(data[4:])
            save_log("\n")
        print(f"Received log: {data}")

        client_socket.close()
'''
def receive_logs():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', log_port))
    server_socket.listen(1)
    print(f"Listening for logs on port {log_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        
        # 初始化接收数据的缓冲区
        full_data = b''
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            full_data += data
        
        # 尝试解码数据
        try:
            decoded_data = full_data.decode('utf-8')
            if decoded_data.startswith("LOG:"):
                save_log(decoded_data[4:])
            print(f"Received log: {decoded_data}")
        except UnicodeDecodeError:
            print("Received non-UTF-8 data")

        client_socket.close()

def save_log(log_data):
    date_str = datetime.now().strftime('%Y-%m-%d')
    log_dir = os.path.join('log', date_str)
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"log_{date_str}.txt")
    with open(log_file_path, 'a') as log_file:
        log_file.write(log_data + '\n')
    print(f"Log saved to {log_file_path}")
'''
def save_image(image_data):
    date_str = datetime.now().strftime('%Y-%m-%d')
    image_dir = os.path.join('image', date_str)
    os.makedirs(image_dir, exist_ok=True)
    image_file_path = os.path.join(image_dir, f"image_{date_str}.jpg")
    with open(image_file_path, 'wb') as image_file:
        image_file.write(image_data)
    print(f"Image saved to {image_file_path}")

def receive_images():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', image_port))
    server_socket.listen(1)
    print(f"Listening for images on port {image_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        data = client_socket.recv(4096)
        if data.startswith(b"IMG:"):
            save_image(data[4:])
        client_socket.close()

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")

            image_data = b''
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break  # No more data, close the connection
                image_data += data

                # Check if we have received the complete image
                if image_data.startswith(b"IMG:") and image_data.endswith(b"END"):
                    save_image(image_data[4:-3])  # Skip "IMG:" at start and "END" at end
                    image_data = b''  # Reset for the next image
    
            client_socket.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()


def receive_status():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('192.168.230.132', status_port))
    server_socket.listen(1)
    print(f"Listening for status messages on port {status_port}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        data = client_socket.recv(4096).decode()
        print(f"Received status: {data}")
        client_socket.close()
'''

def main():

    interval = 10 # 设置时间间隔为10秒
    
    #启动发送时间的线程
    time_thread = threading.Thread(target=send_time_periodically, args=(interval,))
    time_thread.start()
    
    # 启动接收日志的线程
    log_thread = threading.Thread(target=receive_logs)
    log_thread.start()
    '''
    log_message = threading.Thread(target=send_log_me)
    log_message.start
    
    
    # 启动接收图片的线程
    image_thread = threading.Thread(target=receive_images)
    image_thread.start()
    
    
    # 启动接收状态信息的线程
    status_thread = threading.Thread(target=receive_status)
    status_thread.start()
    '''

    # 等待所有线程完成
    time_thread.join()
    log_thread.join()
    #log_message.join()
    #image_thread.join()
    #status_thread.join()

if __name__ == "__main__":
    main()
