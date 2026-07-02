import psutil

try:
    import GPUtil
except Exception:
    GPUtil = None


class SystemMonitor:

    def get_status(self):
        cpu = psutil.cpu_percent(interval=None)

        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        battery = psutil.sensors_battery()

        gpu_name = "RTX 5050"
        gpu_load = 0
        vram_used = 0
        vram_total = 0

        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_name = gpu.name
                    gpu_load = int(gpu.load * 100)
                    vram_used = round(gpu.memoryUsed / 1024, 1)
                    vram_total = round(gpu.memoryTotal / 1024, 1)
            except Exception:
                pass

        battery_percent = "N/A"
        charging = "Unknown"

        if battery:
            battery_percent = f"{int(battery.percent)}%"
            charging = "Charging" if battery.power_plugged else "Battery"

        vram_percent = 0
        if vram_total:
            vram_percent = int((vram_used / vram_total) * 100)

        return {
            "cpu": int(cpu),
            "ram": int(ram.percent),
            "ram_text": f"{round(ram.used / (1024 ** 3), 1)} / {round(ram.total / (1024 ** 3), 1)} GB",
            "disk": int(disk.percent),
            "disk_text": f"{round(disk.used / (1024 ** 3))} / {round(disk.total / (1024 ** 3))} GB",
            "gpu": gpu_load,
            "gpu_name": gpu_name,
            "vram": vram_percent,
            "vram_text": f"{vram_used} / {vram_total} GB" if vram_total else "N/A",
            "battery": battery_percent,
            "charging": charging,
        }