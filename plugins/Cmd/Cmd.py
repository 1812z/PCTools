import subprocess

class Cmd:
    def __init__(self, core):
        self.core = core

        self.config = [{
                'name': 'CMD命令',
                'entity_type': 'text',
                'entity_id': 'Cmd',
                'icon': 'mdi:powershell'
            },
            {
                'name': 'PowerShell命令',
                'entity_type': 'text',
                'entity_id': 'PowerShell',
                'icon': 'mdi:powershell'
            }
        ]

    def handle_mqtt(self, key, data):
        if key == 'Cmd':
            result = subprocess.run(
                data,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            self.core.log.info(f"CMD命令:{data} 执行状态: {result.returncode} 结果\r:{result.stdout}")
        elif key == 'PowerShell':
            result = subprocess.run(
                ["powershell", "-Command", data],
                capture_output=True,
                text=True
            )
            self.core.log.info(f"PowerShell命令:{data} 运行结果: {result.stdout}")
