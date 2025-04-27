from plyer import notification


def show_toast(self, title, message,timeout = 5):
    '''
    显示 toast 消息
    '''
    notification.notify(
        title=title,
        message=message,
        app_name='PCTools',
        timeout=timeout
    )


