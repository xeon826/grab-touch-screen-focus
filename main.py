import subprocess
import threading
import time
from evdev import InputDevice, categorize, ecodes, list_devices
from Xlib import X, display

def find_device_by_name(device_name):
    """Search for and return an input device by its name."""
    for device_path in list_devices():
        device = InputDevice(device_path)
        if device_name in device.name:
            return device
    raise ValueError(f"No device found with name {device_name}")

# Set up display for window management
disp = display.Display()

def get_active_window():
    """ Retrieve the currently active window and its details. """
    window = disp.get_input_focus().focus
    wm_class = window.get_wm_class()
    wm_name = window.get_wm_name()
    return window, wm_name, wm_class

def activate_window(window):
    """ Set focus to the specified window. """
    window.set_input_focus(X.RevertToParent, X.CurrentTime)
    window.configure(stack_mode=X.Above)

def get_mouse_position():
    """Get the current mouse position using xdotool."""
    result = subprocess.run(["xdotool", "getmouselocation", "--shell"], capture_output=True, text=True)
    if result.returncode == 0:
        data = result.stdout.splitlines()
        x = int(data[0].split('=')[1])
        y = int(data[1].split('=')[1])
        return x, y
    return None, None

def move_mouse(x, y):
    """Move the mouse to the specified coordinates using xdotool."""
    subprocess.run(["xdotool", "mousemove", str(x), str(y)])

# Initialize the device by name
device_name = "Melfas LGDisplay Incell Touch"
try:
    device = find_device_by_name(device_name)
except ValueError as e:
    print(e)
    exit(1)

# Global variables to track mouse position
tracked_mouse_x = None
tracked_mouse_y = None
stop_tracking = False

def track_mouse_position(interval=0.5):
    """Continuously track the mouse position at a specified interval (in seconds)."""
    global tracked_mouse_x, tracked_mouse_y, stop_tracking
    while not stop_tracking:
        tracked_mouse_x, tracked_mouse_y = get_mouse_position()
        time.sleep(interval)

# Start a thread to track the mouse position
tracking_thread = threading.Thread(target=track_mouse_position)
tracking_thread.start()

# Main loop to listen for touch events
last_focused_window = None
last_focused_window_name = None
last_focused_window_class = None
saved_mouse_x = None
saved_mouse_y = None

try:
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            if key_event.keystate == key_event.key_down:
                # On touch start
                if last_focused_window is None:  # Only save the position once
                    last_focused_window, last_focused_window_name, last_focused_window_class = get_active_window()
                    # Save the tracked mouse position at the moment the touch starts
                    saved_mouse_x, saved_mouse_y = tracked_mouse_x, tracked_mouse_y
                    print(f"Touch started, last focused window: {last_focused_window_name} [{last_focused_window_class}]")
                    print(f"Saving mouse position: x={saved_mouse_x}, y={saved_mouse_y}")
            elif key_event.keystate == key_event.key_up:
                # On touch end
                current_window, current_window_name, current_window_class = get_active_window()
                print(f"Touch ended, current window: {current_window_name} [{current_window_class}]")
                print(f"Touch on Melfas detected, refocusing last window: {last_focused_window_name} [{last_focused_window_class}]")
                activate_window(last_focused_window)
                if saved_mouse_x is not None and saved_mouse_y is not None:
                    print(f"Restoring mouse position to: x={saved_mouse_x}, y={saved_mouse_y}")
                    move_mouse(saved_mouse_x, saved_mouse_y)
                # Reset saved window and position after restoring focus and mouse
                last_focused_window = None
                saved_mouse_x = None
                saved_mouse_y = None
except KeyboardInterrupt:
    print("Exiting script.")
    stop_tracking = True
    tracking_thread.join()

