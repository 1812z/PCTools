## 功能
HA中控制电脑开启指定可执行文件  
HA中查看电脑硬件温度占用等  
电脑屏幕和摄像头网页查看  
~~订阅MQTT主题自动复制内容到剪贴板~~(没啥用)  
快捷键打开HA侧边栏(默认右ctrl)    
快捷键接入HA智能联动
### HA界面展示:
1.另类副屏:  
<img src="https://img2.moeblog.vip/images/vrJD.jpg" alt="图片" width="450" height="200" />  
2.主页面:  
[![vt5u.md.png](https://img2.moeblog.vip/images/vt5u.md.png)](https://img.moeblog.vip/image/vt5u)  
## TODO List
键盘快捷键联动控制智能家具

## 一.安装各项运行所需要的程序
#### 部分功能用不到可以不安装  
- Python环境:3.12.7  
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
启动gui.bat 来打开gui界面，进入后先到设置配置各项参数，注意参数需要按回车保存  
开启开关来启动需要的功能  
第一次需要进行设备发现，不出意外HA里可以看到各项  
- 监控数据项: 发现成功后执行发送数据，测试是否能读取反馈数据  
<img src="https://img2.moeblog.vip/images/vZ5X.png" alt="图片" width="350" height="490" />  

- 远程命令：把需要运行的 程序/文件放入commands文件夹，运行实体发现，程序会自动同步文件到Ha  
如果后续需要新增或者删除文件，复制到文件夹后重新启动程序即可  
py文件会自动导入，执行其中的fun函数，lnk快捷方式则直接打开  

- Web监控：http://127.0.0.1:5000/screenshot.jpg http://127.0.0.1:5000/video_feed 两个路径对应两个功能，默认端口5000,画面需要手动作为监控接入HA，目前不支持自动添加到HA  

- MQTT消息复制: 默认订阅 PC/messages 主题，将监听该主题的消息并以Toast消息显示  

- 侧边栏小部件: 默认按下键盘上的Menu菜单按键，快捷在屏幕右边20%区域显示HA窄条网页，再次按下隐藏  

- 键盘快捷键联动HA: 添加快捷键后,HA里会出现多个二元传感器，当快捷键按下时候，二元传感器会变 True 一秒钟  

### 3.设置自启动
打开程序主界面/设置，打开"开机自启"，程序将在开机时自动运行而不显示主界面，请提前配置好相关设置  


## 三.Tips
关于卡死：因为没写抓捕报错，也没写异常处理，如果卡死请到任务管理器结束所有python进程，重新打开程序吧  
关于发现: 目前设定自动运行后自动执行一次发现，以免设备出现“不可用”情况，但是电脑休眠后启动数据可能不再更新，等待修复TAT  
推荐软件:openrgb，支持Ha接入控制RGB灯光  

感谢大佬的开源库： https://github.com/gwy15/python_aida64  
让刚学py的我做出来个小工具（（
