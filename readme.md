## 功能
（设备类型空调）小爱远程关机，运行一些命令
（设备类型灯）调节显示器亮度，关闭显示器
Homeassistant远程执行电脑命令
调取Aida64数据监控，并通过MQTT反馈到HomeAssistant
电脑屏幕和摄像头远程查看

## TODO List
GUI支持远程执行自定义命令，列如启动程序，设备管理等等

## 1.安装各项运行所需要的程序
pyhon的库
Homeassistant的MQTT服务器
Nodered(用于处理流程)
巴法云MQTT(小爱同学支持)
Aida64(读取数据并共享给程序)

## 2.启动程序

### 1.运行Aida64
并到选项里打开内存共享，并勾选需要共享的数据

![图片](https://img2.moeblog.vip/images/vO74.png "图片")

目前不支持文本数据监控，不支持电压（懒
支持 占用/速率/温度/功率

### 2.运行python程序
启动gui.py来打开gui界面，进入后先到设置配置各项参数

设备信息监控：第一次需要进行设备发现，不出意外HA里可以看到各项监控数据项
发现成功后执行发送数据，测试是否能读取反馈数据
![图片](https://img2.moeblog.vip/images/vZ5X.png "图片")

远程命令：本质是订阅MQTT消息并执行相应命令，需要手动配置HA发送MQTT消息
默认Topic: dzkz005
默认显示器亮度调节Topic: monitor002

Web监控：/screenshot.jpg /video_feed 两个路径对应两个功能，默认端口5000

## 3.米家绑定巴法云账号
绑定后同步设备，小爱就能控制了

## 4.配置NodeRed节点
见nodered.txt，请根据实际情况修改内容

## 5.Tips
推荐软件，openrgb，支持Ha接入控制RGB

感谢大佬的开源库： https://github.com/gwy15/python_aida64  
让刚学py的我做出来个小工具（（
