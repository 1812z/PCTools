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
- Python环境:3.12.4  
- 必选: pyhon 相关库, Homeassistant MQTT加载项      
通过如下命令安装环境  
 `pip install -r .\requirements.txt`  
- 电脑信息监控: 依赖Aida64(读取数据并共享给程序)   
- 显示器亮度调节: 依赖[Twinkle tray](https://github.com/xanderfrangos/twinkle-tray/releases)

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

- Web监控：http://127.0.0.1:5000/screenshot.jpg http://127.0.0.1:5000/video_feed 两个路径对应两个功能，默认端口5000,画面需要手动作为监控接入HA，目前不支持自动添加到HA
### 3.设置自启动
打开程序主界面/设置，打开"开机自启"，程序将在开机时自动运行而不显示主界面，请提前配置好相关设置


## 五.Tips
关于卡死：因为没写抓捕报错，如果卡死请到任务管理器结束所有python进程，重新打开程序
关于发现: 目前设定自动运行后自动执行一次发现，以免设备出现“不可用”情况  
推荐软件:openrgb，支持Ha接入控制RGB灯光  

感谢大佬的开源库： https://github.com/gwy15/python_aida64  
让刚学py的我做出来个小工具（（
