## 功能
（设备类型空调）小爱远程关机，启动run.bat脚本
（设备类型灯）调节显示器亮度，关闭显示器，但无法实现打开
调取Aida64数据监控
## 1.修改MQTT服务器信息

修改你的巴法云订阅和密钥，并创建相应topic
Ha里安装mqtt加载项，账户密码就是Ha的账户密码

## 2.启动程序

### 1.运行Aida64
并到选项里打开内存共享，并勾选需要共享的数据

![图片](https://img2.moeblog.vip/images/vO74.png "图片")

目前不支持文本数据监控，不支持电压（懒
支持 占用/速率/温度/功率

### 2.运行python程序
可以直接python打开main.pyw，也可以搭配任务计划使用
推荐搭配参数w,来隐藏窗口

库下载链接
https://github.com/gwy15/python_aida64

其中第一次需要进行设备发现，如果发现失败请手动改config.json里的discovery为1再次进行发现
发现成功后到HA里的MQTT中即可查看设备
![图片](https://img2.moeblog.vip/images/vZ5X.png "图片")


## 3.米家绑定巴法云账号
绑定后同步设备，小爱就能控制了

## 4.配置NodeRed节点
见nodered.txt
