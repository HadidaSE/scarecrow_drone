"""
Connection Service
Handles WiFi and SSH connection to the Intel Aero drone
"""
import subprocess
import platform
import threading
import json


class ConnectionService:
    """Manages WiFi and SSH connections to the drone"""

    _instance = None

    # Drone network settings
    DRONE_SSID = "IntelAero"  # WiFi network name of the drone
    DRONE_IP = "192.168.1.1"  # Drone IP address
    DRONE_SSH_USER = "root"
    DRONE_SCRIPT = "python stats.py"  # Script to run on drone

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ssh_connected = False
        self._ssh_process = None
        self._ssh_thread = None
        self._drone_connection = None  # Will be set externally

        # Latest drone data from stats.py
        self._drone_data = {
            "battery_percentage": None,
            "connected_status": False,
            "drone_id": None
        }

    def set_drone_connection(self, drone_connection):
        """Set reference to DroneConnection for updating status"""
        self._drone_connection = drone_connection

    def get_drone_data(self) -> dict:
        """Get latest drone data from stats.py"""
        return self._drone_data.copy()

    def check_wifi_connection(self) -> dict:
        """Check if connected to drone's WiFi network"""
        try:
            if platform.system() == "Windows":
                # Windows: use netsh to get current WiFi
                result = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                connected = self.DRONE_SSID in result.stdout
            else:
                # Linux: check iwconfig or nmcli
                result = subprocess.run(
                    ["iwconfig"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                connected = self.DRONE_SSID in result.stdout

            return {"connected": connected}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def ping_drone(self) -> bool:
        """Ping the drone to check if reachable"""
        try:
            param = "-n" if platform.system() == "Windows" else "-c"
            result = subprocess.run(
                ["ping", param, "1", self.DRONE_IP],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _run_ssh_command(self):
        """Run SSH command in background thread and read output"""
        try:
            # SSH command with required key algorithms for older drones
            ssh_command = [
                "ssh",
                "-o", "HostKeyAlgorithms=+ssh-rsa",
                "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
                "-o", "StrictHostKeyChecking=no",
                f"{self.DRONE_SSH_USER}@{self.DRONE_IP}",
                self.DRONE_SCRIPT
            ]

            self._ssh_process = subprocess.Popen(
                ssh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Read output line by line in real-time
            for line in self._ssh_process.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON from stats.py
                    data = json.loads(line)
                    self._drone_data = data

                    # Update DroneConnection status
                    if self._drone_connection:
                        self._drone_connection.update_status_from_ssh({
                            "is_connected": data.get("connected_status", False),
                            "battery_level": data.get("battery_percentage") or 0,
                            "drone_id": data.get("drone_id")
                        })

                except json.JSONDecodeError:
                    print(f"Invalid JSON from drone: {line}")

            # Process ended
            stderr = self._ssh_process.stderr.read()
            if self._ssh_process.returncode != 0 and stderr:
                print(f"SSH process ended with error: {stderr}")

        except Exception as e:
            print(f"SSH connection error: {e}")
        finally:
            self._ssh_connected = False
            self._ssh_process = None

    async def connect_ssh(self) -> dict:
        """Establish SSH connection to the drone and run stats.py"""
        # Check if already connected
        if self._ssh_connected and self._ssh_process:
            return {"success": True, "message": "Already connected"}

        # First check if we can reach the drone
        if not self.ping_drone():
            return {
                "success": False,
                "error": "Cannot reach drone. Make sure you're connected to the drone's WiFi."
            }

        try:
            # Start SSH in background thread
            self._ssh_thread = threading.Thread(target=self._run_ssh_command, daemon=True)
            self._ssh_thread.start()

            # Give it a moment to connect
            import time
            time.sleep(1)

            # Check if process started successfully
            if self._ssh_process and self._ssh_process.poll() is None:
                self._ssh_connected = True
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": "Failed to start SSH connection"
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def disconnect_ssh(self) -> dict:
        """Disconnect SSH connection"""
        if self._ssh_process:
            try:
                self._ssh_process.terminate()
                self._ssh_process.wait(timeout=5)
            except:
                self._ssh_process.kill()
            self._ssh_process = None

        self._ssh_connected = False
        self._drone_data = {
            "battery_percentage": None,
            "connected_status": False,
            "drone_id": None
        }
        return {"success": True}

    def get_connection_status(self) -> dict:
        """Get full connection status"""
        wifi_check = self.check_wifi_connection()
        wifi_connected = wifi_check.get("connected", False)

        # Check if SSH process is still running
        if self._ssh_process and self._ssh_process.poll() is not None:
            # Process ended
            self._ssh_connected = False
            self._ssh_process = None

        # Drone is ready if SSH connected and drone reports connected_status
        drone_ready = self._ssh_connected and self._drone_data.get("connected_status", False)

        return {
            "wifiConnected": wifi_connected,
            "sshConnected": self._ssh_connected,
            "droneReady": drone_ready
        }

    def is_ssh_connected(self) -> bool:
        """Check if SSH is connected"""
        return self._ssh_connected

    def run_drone_script(self, script: str) -> dict:
        """Run a script on the drone via SSH and return result"""
        if not self._ssh_connected:
            return {"success": False, "error": "Not connected to drone"}

        try:
            ssh_command = [
                "ssh",
                "-o", "HostKeyAlgorithms=+ssh-rsa",
                "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
                "-o", "StrictHostKeyChecking=no",
                f"{self.DRONE_SSH_USER}@{self.DRONE_IP}",
                f"python {script}"
            ]

            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr or "Script failed"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def return_home(self) -> dict:
        """Command drone to return to launch/starting position (RTL mode)"""
        return self.run_drone_script("return_home.py")

    def abort_mission(self) -> dict:
        """Emergency abort - terminate all current tasks and land immediately"""
        return self.run_drone_script("abort_mission.py")
