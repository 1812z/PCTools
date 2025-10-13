import ctypes
import json
import os
import webview
import screeninfo
import keyboard

window_show = False


class Api:
    def close_window(self):
        global window_show
        window.hide()
        window_show = False


def get_scaling_factor():
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        dc = user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
        user32.ReleaseDC(0, dc)
        scaling_factor = dpi / 96.0  # 96 DPI是默认值
        return scaling_factor
    except Exception as e:
        print(f"获取DPI缩放因子失败: {e}")
        return 1.0  # 默认缩放因子


def inject_js(window):
    # 注入的 JavaScript 代码，用于添加关闭按钮和刷新按钮，使用相对单位
    js_code = """ 
    (function() {
        // 获取设备像素比
        var dpr = window.devicePixelRatio || 1;

        // 按钮的大小和位置相对于视口大小
        var buttonSize = 6; // 3vw
        var closeButtonTop = 1; // 1vh
        var closeButtonRight = 1; // 1vw
        var refreshButtonRightOffset = 8; // 5vw

        // 检查是否已经存在关闭按钮，避免重复添加
        if (!document.getElementById('custom-close-button')) {
            var closeButton = document.createElement('button');
            closeButton.id = 'custom-close-button';
            closeButton.innerHTML = 'X';
            closeButton.style.position = 'fixed';
            closeButton.style.top = closeButtonTop + 'vh';
            closeButton.style.right = closeButtonRight + 'vw';
            closeButton.style.zIndex = '9999';
            closeButton.style.backgroundColor = '#f44336';
            closeButton.style.color = '#fff';
            closeButton.style.border = 'none';
            closeButton.style.borderRadius = '50%';
            closeButton.style.width = buttonSize + 'vw';
            closeButton.style.height = buttonSize + 'vw';
            closeButton.style.cursor = 'pointer';
            closeButton.style.fontSize = (buttonSize * 0.6) + 'vw';
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
            refreshButton.style.top = closeButtonTop + 'vh';
            refreshButton.style.right = refreshButtonRightOffset + 'vw';  // 刷新按钮靠近关闭按钮左侧
            refreshButton.style.zIndex = '9999';
            refreshButton.style.backgroundColor = '#4CAF50';
            refreshButton.style.color = '#fff';
            refreshButton.style.border = 'none';
            refreshButton.style.borderRadius = '50%';
            refreshButton.style.width = buttonSize + 'vw';
            refreshButton.style.height = buttonSize + 'vw';
            refreshButton.style.cursor = 'pointer';
            refreshButton.style.fontSize = (buttonSize * 0.6) + 'vw';
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
    global window_show
    if window_show:
        window.hide()
        window_show = False
    else:
        window.on_top = True
        window_show = True
        window.show()


def load_config():
    """加载或创建配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    default_config = {
        "enabled": True,
        "settings": {
            "Widget_select_key": "menu",
            "Widget_url": "https://bing.com"
        }
    }

    try:
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config

        with open(config_path, 'r') as f:
            config = json.load(f)

            # 确保所有设置项都存在
            for key, value in default_config['settings'].items():
                if key not in config['settings']:
                    config['settings'][key] = value

            return config

    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return default_config


def main():
    global select_key
    config = load_config()

    select_key = config['settings'].get("Widget_select_key", "menu")
    url = config['settings'].get("Widget_url", "https://bing.com")

    keyboard.add_hotkey(select_key, lambda h=select_key: command(h), suppress=False)

    api = Api()
    global window
    global window_show

    # 屏幕宽度和高度
    screen = screeninfo.get_monitors()[0]
    scaling_factor = get_scaling_factor()

    # 窗口宽度和高度
    width = int(screen.width * 0.20 / scaling_factor)  # 20% 的屏幕宽度
    height = int(screen.height * scaling_factor)

    # 窗口位置
    x = int(screen.width - width * scaling_factor)
    y = 0

    window = webview.create_window(
        'WebView',
        url,
        frameless=True,
        js_api=api,
        width=width,
        height=height,
        x=x,
        y=y
    )

    window.events.loaded += lambda: inject_js(window)

    window.hidden = True
    window.easy_drag = False
    webview.start(private_mode=False)


if __name__ == '__main__':
    main()
