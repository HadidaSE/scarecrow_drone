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

    # Set to True to simulate drone connection without actual hardware
    MOCK_MODE = False

    # Drone network settings
    DRONE_SSID_PREFIX = "CR_AP"  # WiFi network name prefix of the drone
    DRONE_IP = "192.168.1.1"  # Drone IP address
    DRONE_SSH_USER = "root"
    DRONE_SCRIPT = "python stats.py"  # Script to run on drone

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            print(f"[ConnectionService] Creating new instance: {id(cls._instance)}")
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ssh_connected = False
        self._ssh_process = None
        self._ssh_thread = None
        self._drone_connection = None  # Will be set externally
        self._wifi_fail_count = 0  # Track consecutive WiFi check failures
        self._wifi_fail_threshold = 5  # Disconnect SSH only after this many failures

        # Latest drone data from stats.py
        self._drone_data = {
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
        # Mock mode - always return connected
        if self.MOCK_MODE:
            return {"connected": True}

        try:
            if platform.system() == "Windows":
                # Windows: use netsh to get current WiFi
                result = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                connected = self.DRONE_SSID_PREFIX in result.stdout
            else:
                # Linux: check iwconfig or nmcli
                result = subprocess.run(
                    ["iwconfig"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                connected = self.DRONE_SSID_PREFIX in result.stdout

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
            # Don't reset _ssh_connected here - we're using simplified connect now
            self._ssh_process = None

    async def connect_ssh(self) -> dict:
        """Establish SSH connection to the drone"""
        # Check if already connected
        if self._ssh_connected:
            return {"success": True, "message": "Already connected"}

        # Mock mode - simulate successful connection
        if self.MOCK_MODE:
            self._ssh_connected = True
            self._drone_data = {
                "connected_status": True,
                "drone_id": 1
            }
            print(f"[MOCK] SSH connected")
            return {"success": True}

        # First check if we can reach the drone
        if not self.ping_drone():
            return {
                "success": False,
                "error": "Cannot reach drone. Make sure you're connected to the drone's WiFi."
            }

        try:
            # Test SSH connection with a simple command
            ssh_command = [
                "ssh",
                "-o", "HostKeyAlgorithms=+ssh-rsa",
                "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                f"{self.DRONE_SSH_USER}@{self.DRONE_IP}",
                "echo connected"
            ]

            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and "connected" in result.stdout:
                self._ssh_connected = True
                self._drone_data = {
                    "connected_status": True,
                    "drone_id": 1
                }
                print(f"[ConnectionService] SSH connected, instance {id(self)}, _ssh_connected={self._ssh_connected}")
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": result.stderr or "SSH connection failed"
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "SSH connection timed out"}
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
            "connected_status": False,
            "drone_id": None
        }
        return {"success": True}

    def get_connection_status(self) -> dict:
        """Get full connection status"""
        # Mock mode - always return fully connected
        if self.MOCK_MODE:
            return {
                "wifiConnected": True,
                "sshConnected": True,
                "droneReady": True
            }

        wifi_check = self.check_wifi_connection()
        wifi_connected = wifi_check.get("connected", False)

        # Track consecutive WiFi failures - only disconnect after threshold
        if self._ssh_connected:
            if not wifi_connected:
                self._wifi_fail_count += 1
                print(f"[ConnectionService] WiFi check failed ({self._wifi_fail_count}/{self._wifi_fail_threshold})")

                if self._wifi_fail_count >= self._wifi_fail_threshold:
                    print(f"[ConnectionService] WiFi failed {self._wifi_fail_threshold} times, disconnecting SSH")
                    self._ssh_connected = False
                    self._wifi_fail_count = 0
                    self._drone_data = {
                        "connected_status": False,
                        "drone_id": None
                    }
            else:
                # WiFi is connected, reset fail counter
                if self._wifi_fail_count > 0:
                    print(f"[ConnectionService] WiFi recovered, resetting fail counter")
                self._wifi_fail_count = 0

        # Drone is ready if SSH connected (simplified - we verified SSH works)
        drone_ready = self._ssh_connected

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

        # Mock mode - simulate successful script execution
        if self.MOCK_MODE:
            print(f"[MOCK] Running drone script: {script}")
            return {"success": True, "output": f"[MOCK] {script} executed successfully"}

        try:
            ssh_command = [
                "ssh",
                "-o", "HostKeyAlgorithms=+ssh-rsa",
                "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
                "-o", "StrictHostKeyChecking=no",
                f"{self.DRONE_SSH_USER}@{self.DRONE_IP}",
                f"cd /home/root/drone_scripts && python {script}"
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

    def start_flight(self) -> dict:
        """Start autonomous flight - takeoff, hover, RTL"""
        # Flight takes longer, use extended timeout
        if not self._ssh_connected:
            return {"success": False, "error": "Not connected to drone"}

        if self.MOCK_MODE:
            print(f"[MOCK] Starting flight")
            return {"success": True, "output": "[MOCK] Flight started"}

        try:
            ssh_command = [
                "ssh",
                "-o", "HostKeyAlgorithms=+ssh-rsa",
                "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
                "-o", "StrictHostKeyChecking=no",
                f"{self.DRONE_SSH_USER}@{self.DRONE_IP}",
                "cd /home/root/drone_scripts && python start_flight.py"
            ]

            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for full flight
            )

            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr or "Flight failed"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Flight timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def start_video_stream(self) -> dict:
        """Start video stream from drone to PC"""
        print("\n=== STARTING VIDEO STREAM ===")
        print(f"SSH Connected: {self._ssh_connected}")
        
        if not self._ssh_connected:
            print("[ERROR] Cannot start stream - SSH not connected!")
            return {"success": False, "error": "Not connected to drone"}

        if self.MOCK_MODE:
            print(f"[MOCK] Starting video stream")
            return {"success": True, "output": "[MOCK] Video stream started"}

        try:
            print(f"[INFO] Executing SSH command to start stream on drone...")
            print(f"[INFO] Drone IP: {self.DRONE_IP}")
            print(f"[INFO] Stream script: ~/drone_scripts/start_stream98.sh")

            # Run the stream script in the background (using nohup)
            # This allows the SSH command to return while the stream continues
            ssh_command = [
                "ssh",
                "-o", "HostKeyAlgorithms=+ssh-rsa",
                "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
                "-o", "StrictHostKeyChecking=no",
                f"{self.DRONE_SSH_USER}@{self.DRONE_IP}",
                "cd ~/drone_scripts && nohup bash start_stream98.sh > /dev/null 2>&1 &"
            ]
            
            print(f"[INFO] SSH Command: {' '.join(ssh_command)}")

            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"[INFO] SSH command returned with code: {result.returncode}")
            if result.stdout:
                print(f"[INFO] STDOUT: {result.stdout}")
            if result.stderr:
                print(f"[INFO] STDERR: {result.stderr}")

            if result.returncode == 0:
                print("[SUCCESS] Video stream command sent successfully!")
                print("[INFO] Stream should now be active on drone, sending to 192.168.1.2:5000")
                print("=== VIDEO STREAM STARTED ===")
                return {"success": True, "output": "Video stream started"}
            else:
                print(f"[ERROR] Stream failed to start! Return code: {result.returncode}")
                return {"success": False, "error": result.stderr or "Stream failed to start"}

        except subprocess.TimeoutExpired:
            print("[ERROR] Stream command timed out!")
            return {"success": False, "error": "Stream command timed out"}
        except Exception as e:
            print(f"[ERROR] Exception starting stream: {str(e)}")
            return {"success": False, "error": str(e)}

    def stop_video_stream(self) -> dict:
        """Stop video stream from drone"""
        print("\n=== STOPPING VIDEO STREAM ===")
        
        if not self._ssh_connected:
            print("[ERROR] Cannot stop stream - SSH not connected!")
            return {"success": False, "error": "Not connected to drone"}

        if self.MOCK_MODE:
            print(f"[MOCK] Stopping video stream")
            return {"success": True, "output": "[MOCK] Video stream stopped"}

        try:
            print(f"[INFO] Killing gst-launch-1.0 process on drone...")
            # Kill gst-launch-1.0 process running the stream
            ssh_command = [
                "ssh",
                "-o", "HostKeyAlgorithms=+ssh-rsa",
                "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
                "-o", "StrictHostKeyChecking=no",
                f"{self.DRONE_SSH_USER}@{self.DRONE_IP}",
                "pkill -f gst-launch-1.0"
            ]

            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"[INFO] Kill command returned with code: {result.returncode}")
            print("[SUCCESS] Video stream stopped")
            print("=== VIDEO STREAM STOPPED ===")

            # pkill returns 0 if process was found and killed
            return {"success": True, "output": "Video stream stopped"}

        except subprocess.TimeoutExpired:
            print("[ERROR] Stop command timed out!")
            return {"success": False, "error": "Stop command timed out"}
        except Exception as e:
            print(f"[ERROR] Exception stopping stream: {str(e)}")
            return {"success": False, "error": str(e)}

    def return_home(self) -> dict:
        """Command drone to return to launch/starting position (RTL mode)"""
        return self.run_drone_script("return_home.py")

    def abort_mission(self) -> dict:
        """Emergency abort - terminate all current tasks and land immediately"""
        return self.run_drone_script("abort_mission.py")
