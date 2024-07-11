#include <ESP8266WiFi.h>

const char* ssid = "hello";  // 手机热点的SSID
const char* password = "12345678";  // 手机热点的密码

WiFiClient client;
const char* host = "192.168.86.132";  // 电脑的IP地址
const uint16_t port = 8080;  // 电脑上位机监听的端口

void setup() {
  Serial.begin(115200);  // 与OpenMV通信的串口速率
  WiFi.begin(ssid, password);
  
  // 连接到WiFi
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// 封装尝试连接到上位机的函数
void connectToHost() {
  Serial.println("Connecting to host...");
  if (client.connect(host, port)) {
    Serial.println("Connected to host");
  } else {
    Serial.println("Connection failed");
    delay(5000);  // 重试连接前的等待时间
  }
}

// 封装处理并发送响应到上位机的函数
void sendResponseToClient(WiFiClient &client, const String& response) {
  if (!response.isEmpty()) {
    client.println(response);  // 发送响应到上位机
  } else {
    client.println("No response from OpenMV");  // 如果无有效响应，发送无响应信息
  }
}

String waitForResponse(long timeoutDuration) {
  String response = "";
  long timeout = millis() + timeoutDuration;  // 设置一个超时时间，防止无限等待
  while (millis() < timeout) {
    if (Serial.available()) {
      char c = Serial.read();
      response += c;
      if (c == '\n') break;
    }
  }
  return response;
}

void loop() {
  // 尝试连接到上位机
  if (!client.connected()) {
    connectToHost();
  }
  
  // 处理从上位机接收到的数据
  if (client.available()) {
    String request = client.readStringUntil('\n');
    request.trim();  // 修整字符串，去除前后的空白
    
    if (!request.isEmpty()) {
      Serial.println(request);  // 发送请求到OpenMV
      String response = waitForResponse(5000);  // 等待来自OpenMV的响应
      
      sendResponseToClient(client, response);  // 处理并发送响应到上位机
      
      if (request == "e") {
        client.stop();  // 如果接收到退出命令，断开连接
        return;
      }
    }
  }
  
  delay(10);  // 延时以防止忙等待
}


