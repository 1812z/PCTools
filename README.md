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
1.另类副屏(页面示例见example/dashboard.txt):  
<img src=".github\images\1743859715274.jpg" alt="图片" width="400" height="250" />  
2.主页面:  
<img src=".github\images\image.png" alt="手机视图" height="500"/>


## TODO List
- [X] 键盘快捷键联动控制智能家具
- [X] 优化代码 ~~(下次一定)~~ *不许下次一定!*

***
## 一.安装各项运行所需要的程序
### 1.Python环境
方法一:下载releases内打包好的压缩包，内置运行环境
方法二:下载source code，手动配置好
- Python:3.12.9
- 运行库，通过如下命令安装环境  
 `pip install -r .\requirements.txt`  
### 2.依赖
-  一个接入HA的MQTT服务器      
- 电脑信息监控: 依赖Aida64(读取数据并共享给程序)   
- 显示器亮度调节: 依赖[Twinkle tray](https://github.com/xanderfrangos/twinkle-tray/releases)

## 二.启动程序

### 1.配置依赖程序
(1)启动Aida64并到选项里打开内存共享，并勾选需要共享的数据，支持 占用/速率/温度/功率/电压 等实体，部分实体会自动添加图标
> [!TIP]
> 新增/修改 传感器，请手动删除HA/MQTT内整个设备

![图片](https://img2.moeblog.vip/images/vO74.png "图片")

(2)启动Twinkle tray，确保能正常读取显示器信息，如不支持请关闭设置里的显示器功能


### 2.运行python程序
(1)启动 `打开GUI.bat`  来打开gui界面，进入后先到设置配置各项参数，注意参数**需要按回车保存**  
(2)开启开关来启用需要的功能  
(3)点击启动后,程序会自动发送Discovery信息,此时回到HA的MQTT集成中查看有无新设备  

- **监控数据项** 定时更新Aida64选定的信息  
<img src="img\QQ20250301-223512.png" alt="图片" width="200" height="600" />  

- **远程命令** 把需要运行的 程序/文件放入commands文件夹，重新运行程序，新的命令会自动同步文件到Ha  
py文件会自动导入，执行其中的fun函数，lnk快捷方式则直接打开  

- **Web监控** 
屏幕截图: `http://127.0.0.1:5000/screenshot.jpg` 
电脑摄像头: `http://127.0.0.1:5000/video_feed`
实时画面: `http://127.0.0.1:5000/screen` 
画面需要手动作为视频流接入HA，目前不支持自动添加到HA(MQTT视频流性能差)  

- **MQTT消息复制** 默认订阅 PC/messages 主题，将监听该主题的消息并以Toast消息显示  

- **侧边栏小部件** 默认按下键盘上的Menu菜单按键，快捷在屏幕右边20%区域显示HA窄条网页，再次按下隐藏  

- **键盘快捷键联动** 添加快捷键后,HA里会出现多个二元传感器，当快捷键按下时候，二元传感器会变 True 一秒钟  

- **前台应用状态反馈** 当切换前台应用时，自动发送当前应用的名称

- **显示器控制** 通过`Twinkle tray`实现多显示器亮度控制，支持HA开关显示器，自定义DDC/CI命令
### 3.设置自启动
打开程序主界面，点击 **自启动** ，程序将在开机时自动运行而不显示主界面，请提前配置好相关设置  
再按一次删除启动项


## 三.Tips
推荐软件:openrgb，支持Ha接入控制RGB灯光  

感谢大佬的开源库： https://github.com/gwy15/python_aida64  
让刚学py的我做出来个小工具（（
