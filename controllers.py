import hid
import XInput
from typing import List, Dict, Optional

class HapticController:
    """Base class for all haptic controllers."""
    def __init__(self):
        self.connected = False
        self.device = None

    def connect(self) -> bool:
        raise NotImplementedError

    def send_rumble(self, left_motor: float, right_motor: float):
        """Send rumble values (0.0 to 1.0) to the controller."""
        raise NotImplementedError

    def stop(self):
        self.send_rumble(0.0, 0.0)

    def disconnect(self):
        self.stop()
        self.connected = False

class PSHapticController(HapticController):
    """Handles PlayStation 4 and 5 controllers via HID."""
    SONY_VID = 0x054C
    PIDS = {
        "DS4_V1": 0x05C4,
        "DS4_V2": 0x09CC,
        "DUALSENSE": 0x0CE6,
        "DUALSENSE_EDGE": 0x0DF2
    }

    def __init__(self):
        super().__init__()
        self.pid = None

    def find_controllers(self) -> List[Dict]:
        try:
            controllers = []
            for info in hid.enumerate(self.SONY_VID, 0):
                pid = info.get("product_id", 0)
                if pid in self.PIDS.values():
                    controllers.append({
                        "path": info["path"],
                        "pid": pid,
                        "name": info.get("product_string", "PlayStation Controller"),
                        "interface": info.get("interface_number", -1)
                    })
            return controllers
        except Exception as e:
            print(f"Error finding PS controllers: {e}")
            return []

    def connect(self, controller_info: Optional[Dict] = None) -> bool:
        if controller_info is None:
            controllers = self.find_controllers()
            if not controllers:
                return False
            controller_info = controllers[0]

        try:
            self.device = hid.device()
            self.device.open_path(controller_info["path"])
            self.device.set_nonblocking(True)
            self.pid = controller_info["pid"]
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to PS controller: {e}")
            return False

    def send_rumble(self, left_motor: float, right_motor: float):
        if not self.connected or not self.device:
            return

        try:
            left = int(max(0.0, min(1.0, left_motor)) * 255)
            right = int(max(0.0, min(1.0, right_motor)) * 255)

            if self.pid in [self.PIDS["DUALSENSE"], self.PIDS["DUALSENSE_EDGE"]]:
                report = bytearray(48)
                report[0] = 0x02
                report[1] = 0xFC
                report[3] = right
                report[4] = left
            else:
                report = bytearray(32)
                report[0] = 0x05
                report[1] = 0xFF
                report[4] = right
                report[5] = left
            self.device.write(report)
        except Exception as e:
            print(f"PS Rumble Error: {e}")
            self.connected = False

    def disconnect(self):
        self.stop()
        if self.device:
            try:
                self.device.close()
            except:
                pass
        self.connected = False

class XboxHapticController(HapticController):
    """Handles Xbox controllers via XInput."""
    def __init__(self):
        super().__init__()
        self.controller_index = 0

    def connect(self, index: int = 0) -> bool:
        self.controller_index = index
        # XInput doesn't have a "connect" in the same way HID does
        # We just check if a controller is connected
        try:
            # Check if the controller is connected
            state = XInput.get_state(self.controller_index)
            self.connected = True
            return True
        except Exception:
            # If get_state fails, it's likely not connected
            self.connected = False
            return False

    def send_rumble(self, left_motor: float, right_motor: float):
        if not self.connected:
            return

        try:
            # XInput expects 0-65535 for rumble
            left = int(max(0.0, min(1.0, left_motor)) * 65535)
            right = int(max(0.0, min(1.0, right_motor)) * 65535)
            XInput.set_vibration(self.controller_index, left, right)
        except Exception as e:
            print(f"Xbox Rumble Error: {e}")
            self.connected = False

def get_all_controllers():
    """Detects all connected supported controllers."""
    results = []

    # Check PS controllers
    ps = PSHapticController()
    for i, ctrl in enumerate(ps.find_controllers()):
        results.append({
            "id": f"ps_{i}",
            "name": ctrl["name"],
            "type": "ps",
            "info": ctrl
        })

    # Check Xbox controllers (usually 4 slots)
    for i in range(4):
        xbox = XboxHapticController()
        if xbox.connect(i):
            results.append({
                "id": f"xbox_{i}",
                "name": f"Xbox Controller {i}",
                "type": "xbox",
                "info": i
            })

    return results
