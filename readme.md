#### HASS.Agent 分支恢复更新，建议去用HASS.Agent，此项目跑路了

#### Here’s a simple Python program to help Windows integrate with Home Assistant for hardware monitoring, remote control, and other functions.
***
## 功能
#### HomeAssistant端:
- 启动电脑 程序  
- 查看电脑 风扇/温度/功率/占用
- 音量调节
- 显示器 亮度/开/关 
- 查看电脑画面和摄像头
- 键盘快捷键联动
- 查看电脑 前台程序名称
#### Windows端:
- 订阅HA通知
- HA网页快捷启动(右Menu键)
 
### 软件截图(不保证最新)
<img src=".github\images\gui.png" alt="GUI Image" width="600"/>


### HA界面展示:
1.另类副屏:  
<img src=".github\images\Panel.jpg" alt="图片" width="450" height="200" />  
2.主页面:  
<img src=".github\images\image.png" alt="手机视图" height="500"/>


## TODO List
- [X] 键盘快捷键联动控制智能家具
- [ ] 优化代码(下次一定)

***
## 一.安装各项运行所需要的程序

- Python:3.12.7  
-  一个接入HA的MQTT服务器      
- 运行库，通过如下命令安装环境  
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
(1)启动 `gui.bat`  来打开gui界面，进入后先到设置配置各项参数，注意参数**需要按回车保存**  
(2)开启开关来启用需要的功能  
(3)点击启动后,程序会自动发送Discovery信息,此时回到HA中查看有无新设备  
- **监控数据项** 定时更新Aida64选定的信息  
<img src="img\QQ20250301-223512.png" alt="图片" width="200" height="600" />  

- **远程命令** 把需要运行的 程序/文件放入commands文件夹，重新运行程序，新的命令会自动同步文件到Ha  
py文件会自动导入，执行其中的fun函数，lnk快捷方式则直接打开  

- **Web监控** `http://127.0.0.1:5000/screenshot.jpg` `http://127.0.0.1:5000/video_feed` 两个路径对应两个功能，默认端口5000,画面需要手动作为监控接入HA，目前不支持自动添加到HA  

- **MQTT消息复制** 默认订阅 PC/messages 主题，将监听该主题的消息并以Toast消息显示  

- **侧边栏小部件** 默认按下键盘上的Menu菜单按键，快捷在屏幕右边20%区域显示HA窄条网页，再次按下隐藏  

- **键盘快捷键联动** 添加快捷键后,HA里会出现多个二元传感器，当快捷键按下时候，二元传感器会变 True 一秒钟  

- **前台应用状态反馈** 当切换前台应用时，自动发送当前应用的名称
### 3.设置自启动
打开程序主界面，点击 **自启动** ，程序将在开机时自动运行而不显示主界面，请提前配置好相关设置  
再按一次删除启动项


## 三.Tips
关于卡死：因为没写抓捕报错，也没写异常处理，如果卡死请到任务管理器结束所有python进程，重新打开程序吧   
关于发现: 目前设定自动运行后自动执行一次发现，以免设备出现“不可用”情况，但是电脑休眠后启动数据可能不再更新，等待修复TAT  
推荐软件:openrgb，支持Ha接入控制RGB灯光  

感谢大佬的开源库： https://github.com/gwy15/python_aida64  
让刚学py的我做出来个小工具（（
