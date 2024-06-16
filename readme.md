## 功能
Homeassistant远程运行可执行文件
调取Aida64数据监控，并通过MQTT反馈到HomeAssistant
电脑屏幕和摄像头网页查看
### HA界面展示:
1.另类副屏:  
<img src="https://img2.moeblog.vip/images/vrJD.jpg" alt="图片" width="450" height="200" />  
2.主页面:  
[![vt5u.md.png](https://img2.moeblog.vip/images/vt5u.md.png)](https://img.moeblog.vip/image/vt5u)  
## TODO List
无，开始摸鱼

## 一.安装各项运行所需要的程序
#### 部分功能用不到可以不安装  
- 必选: pyhon 相关库, Homeassistant MQTT加载项      
通过如下命令安装环境  
 `pip install -r .\requirements.txt`  
- 监控反馈: Aida64(读取数据并共享给程序)   
- 远程命令: Twinkle tray(控制显示器亮度)   

## 二.启动程序

### 1.运行Aida64
并到选项里打开内存共享，并勾选需要共享的数据

![图片](https://img2.moeblog.vip/images/vO74.png "图片")

目前不支持文本数据监控，不支持电压（懒
支持 占用/速率/温度/功率

### 2.运行python程序
启动gui.bat 来打开gui界面，进入后先到设置配置各项参数  
开启开关来启动需要的功能  
第一次需要进行设备发现，不出意外HA里可以看到各项  
- 监控数据项: 发现成功后执行发送数据，测试是否能读取反馈数据  
<img src="https://img2.moeblog.vip/images/vZ5X.png" alt="图片" width="350" height="490" />  
- 远程命令：把需要运行的 程序/文件(建议用快捷方式),放入commands文件夹，运行实体发现，程序会自动同步文件到Ha  
如果后续需要新增或者删除文件，重新启动程序即可

- Web监控：/screenshot.jpg /video_feed 两个路径对应两个功能，默认端口5000
### 3.设置自启动
1.GUi里的设置自动运行打开后，运行程序会自动启动服务而不显示主页面  
2.使用Windows的任务计划程序，添加自启动，启动程序“C:\Users\i\AppData\Local\Microsoft\WindowsApps\pythonw.exe”，参数填写脚本gui.py位置，起始填写脚本目录。
## 三.同步到巴法云
目前程序不在内置巴法云订阅，请到Ha中安装集成 https://github.com/larry-wong/bemfa  
该集成可一键同步实体到米家  

## 四.配置NodeRed节点
目前程序不再依赖Nodered  
如果需要联动，见nodered.txt，仅供参考  

## 五.Tips
关于发现: 目前设定自动运行后自动执行一次发现，以免设备出现“不可用”情况  
推荐软件:openrgb，支持Ha接入控制RGB灯光  

感谢大佬的开源库： https://github.com/gwy15/python_aida64  
让刚学py的我做出来个小工具（（
