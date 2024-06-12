## 功能
Homeassistant远程运行可执行文件
调取Aida64数据监控，并通过MQTT反馈到HomeAssistant
电脑屏幕和摄像头网页查看

## TODO List
GUI支持远程执行自定义命令，列如启动程序，设备管理等等

## 1.安装各项运行所需要的程序
pyhon 相关库    
Homeassistant MQTT加载项  
Aida64(读取数据并共享给程序)  

## 2.启动程序

### 1.运行Aida64
并到选项里打开内存共享，并勾选需要共享的数据

![图片](https://img2.moeblog.vip/images/vO74.png "图片")

目前不支持文本数据监控，不支持电压（懒
支持 占用/速率/温度/功率

### 2.运行python程序
启动gui.bat 来打开gui界面，进入后先到设置配置各项参数  
设备信息监控：第一次需要进行设备发现，不出意外HA里可以看到各项监控数据项  
发现成功后执行发送数据，测试是否能读取反馈数据  
![图片](https://img2.moeblog.vip/images/vZ5X.png "图片")

远程命令：把需要运行的 程序/文件(建议用快捷方式),放入commands文件夹，运行实体发现，程序会自动同步文件到Ha  
如果后续需要新增或者删除文件，建议在Ha中删除该设备重新运行发现

Web监控：/screenshot.jpg /video_feed 两个路径对应两个功能，默认端口5000

## 3.米家绑定巴法云账号
绑定后同步设备，小爱就能控制了

## 4.配置NodeRed节点
见nodered.txt，请根据实际情况修改内容

## 5.Tips
推荐软件，openrgb，支持Ha接入控制RGB

感谢大佬的开源库： https://github.com/gwy15/python_aida64  
让刚学py的我做出来个小工具（（
