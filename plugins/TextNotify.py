from plyer import notification

class TextNotify:
    def __init__(self, core):
        self.core = core

        self.config = [
            {
                'name': 'Toast通知',
                'entity_type': 'text',
                'entity_id': 'TextNotify',
                'icon': 'mdi:message'
            }
        ]

    def handle_mqtt(self, topic, data):
        self.core.log.info(f"订阅通知: {data}")
        self.core.show_toast("消息通知", data)


