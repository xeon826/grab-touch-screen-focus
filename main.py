import subprocess
from evdev import InputDevice, categorize, ecodes
from Xlib import X, display

# Set up the event device
event_device_path = "/dev/input/event28"  # Update to your device path
device = InputDevice(event_device_path)

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

# Main loop
last_focused_window = None
last_focused_window_name = None
last_focused_window_class = None

try:
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            if key_event.keystate == key_event.key_down:
                # On touch start
                last_focused_window, last_focused_window_name, last_focused_window_class = get_active_window()
                print(f"Touch started, last focused window: {last_focused_window_name} [{last_focused_window_class}]")
                activate_window(last_focused_window)
            elif key_event.keystate == key_event.key_up:
                # On touch end
                current_window, current_window_name, current_window_class = get_active_window()
                print(f"Touch ended, current window: {current_window_name} [{current_window_class}]")
                if "Google Chrome" in current_window_class:
                    print(f"Touch on Chrome detected, refocusing last window: {last_focused_window_name} [{last_focused_window_class}]")
                    activate_window(last_focused_window)
except KeyboardInterrupt:
    print("Exiting script.")

