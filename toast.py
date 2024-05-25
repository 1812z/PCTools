from win10toast import WindowsToaster, Toast

def send_notification(info):
    toaster = WindowsToaster('Python')
    new_toast = Toast()
    new_toast.text_fields = [info]
    new_toast.on_activated = lambda _: print('Toast clicked!')
    toaster.show_toast(new_toast)
