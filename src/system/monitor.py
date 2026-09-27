import psutil
import platform
import subprocess
import json
import threading

try:
    import GPUtil
except Exception:
    GPUtil = None


STATIC_SPECS = None
STATIC_SPECS_LOADING = False


class SystemMonitor:

    def __init__(self):
        global STATIC_SPECS, STATIC_SPECS_LOADING

        if STATIC_SPECS is None:
            self.cpu_name = platform.processor().strip() or "CPU"
            STATIC_SPECS = {
                "manufacturer": "LENOVO",
                "model": "IdeaPad Pro 5 16IAH10",
                "machine_type": "83JM",
                "ram_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
                "cpu_name": self.cpu_name,
                "cpu_cores": psutil.cpu_count(logical=False) or "N/A",
                "cpu_threads": psutil.cpu_count(logical=True) or "N/A",
                "cpu_max_clock_mhz": "N/A",
                "gpus": [],
                "disks": [],
            }
            STATIC_SPECS_LOADING = True
            threading.Thread(
                target=self.load_static_specs_background,
                daemon=True
            ).start()
        else:
            self.cpu_name = STATIC_SPECS.get("cpu_name", "CPU")

        self.specs = STATIC_SPECS

    def load_static_specs_background(self):
        global STATIC_SPECS, STATIC_SPECS_LOADING

        try:
            detailed_specs = self.get_static_specs()
            STATIC_SPECS.update(detailed_specs)
            self.cpu_name = STATIC_SPECS.get("cpu_name", self.cpu_name)
        finally:
            STATIC_SPECS_LOADING = False

    def run_powershell(self, command, timeout=4):
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                command
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return result.stdout.strip()

    def get_powershell_json(self, command, default):
        try:
            output = self.run_powershell(
                f"{command} | ConvertTo-Json -Compress",
                timeout=5
            )

            if output:
                return json.loads(output)
        except Exception:
            pass

        return default

    def get_cpu_name(self):
        try:
            name = self.run_powershell("(Get-CimInstance Win32_Processor).Name")

            if name:
                return " ".join(name.split())
        except Exception:
            pass

        name = platform.processor().strip()

        if name:
            return " ".join(name.split())

        return "CPU"

    def get_static_specs(self):
        computer = self.get_powershell_json(
            "Get-CimInstance Win32_ComputerSystem | "
            "Select-Object Manufacturer,Model,TotalPhysicalMemory",
            {}
        )
        product = self.get_powershell_json(
            "Get-CimInstance Win32_ComputerSystemProduct | "
            "Select-Object Name,Version,Vendor",
            {}
        )
        processor = self.get_powershell_json(
            "Get-CimInstance Win32_Processor | "
            "Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed",
            {}
        )
        video = self.get_powershell_json(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,AdapterRAM",
            []
        )
        disks = self.get_powershell_json(
            "Get-PhysicalDisk | Select-Object FriendlyName,Size,MediaType",
            []
        )

        if isinstance(video, dict):
            video = [video]

        if isinstance(disks, dict):
            disks = [disks]

        total_memory = int(computer.get("TotalPhysicalMemory") or 0)
        ram_total_gb = round(total_memory / (1024 ** 3), 1) if total_memory else 0
        manufacturer = computer.get("Manufacturer", "Unknown")
        model = product.get("Version") or computer.get("Model", "Unknown")

        return {
            "manufacturer": manufacturer,
            "model": model,
            "machine_type": computer.get("Model", product.get("Name", "Unknown")),
            "ram_total_gb": ram_total_gb,
            "cpu_name": processor.get("Name", self.cpu_name),
            "cpu_cores": processor.get("NumberOfCores", "N/A"),
            "cpu_threads": processor.get("NumberOfLogicalProcessors", "N/A"),
            "cpu_max_clock_mhz": processor.get("MaxClockSpeed", "N/A"),
            "gpus": video,
            "disks": disks,
        }

    def get_cpu_temperature(self):
        return None

    def get_nvidia_temperature(self):
        try:
            output = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=3
            ).stdout.strip().splitlines()

            if output:
                return int(float(output[0].strip()))
        except Exception:
            pass

        return None

    def get_status(self):
        cpu = psutil.cpu_percent(interval=None)

        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        battery = psutil.sensors_battery()

        gpu_name = "RTX 5050"
        gpu_load = 0
        vram_used = 0
        vram_total = 0
        gpu_temp = None

        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_name = gpu.name
                    gpu_load = int(gpu.load * 100)
                    vram_used = round(gpu.memoryUsed / 1024, 1)
                    vram_total = round(gpu.memoryTotal / 1024, 1)
                    gpu_temp = getattr(gpu, "temperature", None)
                    if gpu_temp is not None:
                        gpu_temp = int(round(float(gpu_temp)))
            except Exception:
                pass

        if gpu_temp is None:
            gpu_temp = self.get_nvidia_temperature()

        cpu_temp = self.get_cpu_temperature()

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
            "cpu_name": self.cpu_name,
            "cpu_temp": cpu_temp,
            "cpu_temp_text": f"{cpu_temp} °C" if cpu_temp is not None else "",
            "ram": int(ram.percent),
            "ram_text": f"{round(ram.used / (1024 ** 3), 1)} / {round(ram.total / (1024 ** 3), 1)} GB",
            "disk": int(disk.percent),
            "disk_text": f"{round(disk.used / (1024 ** 3))} / {round(disk.total / (1024 ** 3))} GB",
            "gpu": gpu_load,
            "gpu_name": gpu_name,
            "gpu_temp": gpu_temp,
            "gpu_temp_text": f"{gpu_temp} °C" if gpu_temp is not None else "",
            "vram": vram_percent,
            "vram_text": f"{vram_used} / {vram_total} GB" if vram_total else "N/A",
            "battery": battery_percent,
            "charging": charging,
            "specs": self.specs,
        }
