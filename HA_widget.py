import json
import webview
import screeninfo
import keyboard

window_show = False


class Api:
    def close_window(self):
        global window_show
        window.hide()
        window_show = False



def inject_js(window):
    # 注入的 JavaScript 代码，用于添加关闭按钮
    js_code = """ 
    (function() {
        // 检查是否已经存在关闭按钮，避免重复添加
        if (!document.getElementById('custom-close-button')) {
            var closeButton = document.createElement('button');
            closeButton.id = 'custom-close-button';
            closeButton.innerHTML = 'X';
            closeButton.style.position = 'fixed';
            closeButton.style.top = '10px';
            closeButton.style.right = '10px';
            closeButton.style.zIndex = '9999';
            closeButton.style.backgroundColor = '#f44336';
            closeButton.style.color = '#fff';
            closeButton.style.border = 'none';
            closeButton.style.borderRadius = '50%';
            closeButton.style.width = '30px';
            closeButton.style.height = '30px';
            closeButton.style.cursor = 'pointer';
            closeButton.style.fontSize = '16px';
            closeButton.style.fontWeight = 'bold';
            closeButton.onclick = function() {
                pywebview.api.close_window();  // 保持原先关闭窗口功能
            };
            document.body.appendChild(closeButton);
        }

        // 检查是否已经存在刷新按钮，避免重复添加
        if (!document.getElementById('custom-refresh-button')) {
            var refreshButton = document.createElement('button');
            refreshButton.id = 'custom-refresh-button';
            refreshButton.innerHTML = '⟳';  // 刷新按钮图标
            refreshButton.style.position = 'fixed';
            refreshButton.style.top = '10px';
            refreshButton.style.right = '50px';  // 刷新按钮靠近关闭按钮左侧
            refreshButton.style.zIndex = '9999';
            refreshButton.style.backgroundColor = '#4CAF50';
            refreshButton.style.color = '#fff';
            refreshButton.style.border = 'none';
            refreshButton.style.borderRadius = '50%';
            refreshButton.style.width = '30px';
            refreshButton.style.height = '30px';
            refreshButton.style.cursor = 'pointer';
            refreshButton.style.fontSize = '16px';
            refreshButton.style.fontWeight = 'bold';
            refreshButton.onclick = function() {
                location.reload();  // 点击刷新按钮时刷新页面
            };
            document.body.appendChild(refreshButton);
        }
    })();
    """

    try:
        window.evaluate_js(js_code)
    except Exception as e:
        print(f"注入 JavaScript 失败: {e}")


def command(h):
    print("触发了快捷键:", h)
    global window_show
    if window_show == True:
        window.hide()
        window_show = False
    else:
        window.on_top = True
        window_show = True
        window.show()

def main():
    global select_key
    with open('config.json', 'r') as file:
        json_data = json.load(file)
        select_key = json_data.get("select_key")
        if not(select_key):
           select_key = 'menu'
        keyboard.add_hotkey(select_key, lambda h=select_key: command(h),suppress=True)
        
        url = json_data.get("url")

    api = Api()
    global window
    global window_show
    # 获取屏幕宽度和高度
    screen = screeninfo.get_monitors()[0]
    width = int(screen.width * 0.20)  # 20% 的屏幕宽度
    height = screen.height

    window = webview.create_window(
        'WebView',
        url,
        frameless=True,
        js_api=api,
        width=width,
        height=height,
        x=screen.width - width,
        y=0
    )

    window.events.loaded += lambda: inject_js(window)

    window.hidden=True
    window.easy_drag=False
    webview.start(private_mode=False)


if __name__ == '__main__':
    main()
