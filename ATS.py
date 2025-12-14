from roboflowoak import RoboflowOak
from Adafruit_PCA9685 import PCA9685
import cv2
import time
import math

# --- PCA9685 Setup -----------------------------------------------
pwm = PCA9685(address=0x40, busnum=1)
pwm.set_pwm_freq(60)

# Servo pulse range
MIN_PULSE = 150
MAX_PULSE = 600
MID_PULSE = (MIN_PULSE + MAX_PULSE) // 2

# Channels
PAN_CHANNEL = 0
TILT_CHANNEL = 14

# Frame center target
CENTER_X = 256
CENTER_Y = 256

# --- Anti-Oscillation Settings -----------------------------------
KP_PAN = 0.03
KP_TILT = 0.03
KD_PAN = 0.02
KD_TILT = 0.02
DEADZONE = 25
MAX_STEP = 5

# Search mode settings
SEARCH_TIMEOUT = 1.0
SEARCH_STEP = 1
SEARCH_DELAY = 0.05

# Stationary detection settings
STATIONARY_TIME = 3.0
SCAN_MAX_TIME_PER_TARGET = 5.0

# Target recognition threshold (servo space)
POSITION_MATCH_THRESHOLD = 80

# Fire mode / lock-on settings
FIRE_LOCK_TIME = 5.0
DEAD_AREA_THRESHOLD = 0.60  # 60% of original area

# Current servo positions
pan_pulse = MID_PULSE
tilt_pulse = MID_PULSE

# Previous errors (for derivative)
prev_error_x = 0
prev_error_y = 0

# Search state
last_detection_time = time.time()
pan_direction = 1
tilt_direction = 1
last_search_step_time = 0

# Last movement direction (servo space)
last_step_x = 0.0
last_step_y = 0.0

# --- Target Management -------------------------------------------
class Target:
    def __init__(self, target_id):
        self.id = target_id
        self.saved_pan = None
        self.saved_tilt = None
        self.saved_width = None
        self.saved_height = None
        self.saved_area = None
        self.last_x = None
        self.last_y = None
        self.stationary_start_time = None
        self.is_saved = False
        self.last_seen_time = None
        self.is_dead = False  # NEW: Persistent dead flag
        self.fired_upon = False  # NEW: Track if fire lock completed on this target
        
    def update_position(self, x, y, width, height, current_pan, current_tilt):
        self.last_x = x
        self.last_y = y
        self.last_seen_time = time.time()
        
        # Check if stationary (within deadzone from center for 3 seconds)
        error_x = abs(x - CENTER_X)
        error_y = abs(y - CENTER_Y)
        
        if error_x <= DEADZONE and error_y <= DEADZONE:
            if self.stationary_start_time is None:
                self.stationary_start_time = time.time()
            elif time.time() - self.stationary_start_time >= STATIONARY_TIME:
                old_pan = self.saved_pan
                old_tilt = self.saved_tilt
                self.saved_pan = int(current_pan)
                self.saved_tilt = int(current_tilt)
                
                # Save width, height, and calculate area
                self.saved_width = width
                self.saved_height = height
                self.saved_area = width * height
                
                self.is_saved = True
                self.stationary_start_time = None

                if old_pan != self.saved_pan or old_tilt != self.saved_tilt:
                    print(f"? TARGET {self.id} position SAVED: pan={self.saved_pan}, tilt={self.saved_tilt}, area={self.saved_area:.1f}")
                return True
        else:
            self.stationary_start_time = None
        
        return False
    
    def check_if_dead(self, current_area):
        """Check if target should be marked as dead based on area reduction"""
        # Only check if we've fired upon this target and it's not already dead
        if not self.fired_upon or self.is_dead:
            return self.is_dead
        
        # Must have a saved area to compare against
        if self.saved_area is None or self.saved_area == 0:
            return False
        
        # Calculate area ratio
        area_ratio = current_area / self.saved_area
        
        # Mark as dead if area is 60% or less of original
        if area_ratio <= DEAD_AREA_THRESHOLD:
            self.is_dead = True
            print(f"!!! TARGET {self.id} MARKED AS DEAD - Area reduced to {area_ratio*100:.1f}% of original")
        
        return self.is_dead
    
    def mark_fired_upon(self):
        """Mark that fire lock was completed on this target"""
        if not self.fired_upon:
            self.fired_upon = True
            print(f">>> TARGET {self.id} FIRED UPON - monitoring for area reduction")
    
    def has_saved_position(self):
        return self.saved_pan is not None and self.saved_tilt is not None
    
    def get_stationary_progress(self):
        if self.stationary_start_time is None:
            return 0.0
        return time.time() - self.stationary_start_time
    
    def is_near_saved_position(self, current_pan, current_tilt):
        if not self.has_saved_position():
            return False
        
        pan_dist = abs(current_pan - self.saved_pan)
        tilt_dist = abs(current_tilt - self.saved_tilt)
        distance = math.sqrt(pan_dist**2 + tilt_dist**2)
        return distance < POSITION_MATCH_THRESHOLD

# Target storage (1-indexed)
targets = [None, Target(1), Target(2), Target(3)]

# --- Mode Management ---------------------------------------------
MODE_AUTO = "AUTO"
MODE_MANUAL_1 = "MANUAL_1"
MODE_MANUAL_2 = "MANUAL_2"
MODE_MANUAL_3 = "MANUAL_3"
MODE_SCAN = "SCAN"

current_mode = MODE_SCAN
current_tracking_target = None
searching_for_target_id = None

# Scan mode state
scan_target_start_time = None
scan_targets_visited = set()

# Fire mode state
fire_mode = False
fire_lock_start_time = None
fire_locked = False
previous_fire_locked = False  # NEW: Track fire lock state changes


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def pd_step(error, prev_error, kp, kd, max_step):
    p_term = kp * error
    d_term = kd * (error - prev_error)
    step = p_term + d_term
    return clamp(step, -max_step, max_step)


def search_for_target():
    global pan_pulse, tilt_pulse, pan_direction, tilt_direction, last_search_step_time

    now = time.time()
    if now - last_search_step_time < SEARCH_DELAY:
        return

    last_search_step_time = now
    pan_pulse += SEARCH_STEP * pan_direction

    if pan_pulse >= MAX_PULSE:
        pan_pulse = MAX_PULSE
        pan_direction = -1
        tilt_pulse += SEARCH_STEP * tilt_direction * 5
    elif pan_pulse <= MIN_PULSE:
        pan_pulse = MIN_PULSE
        pan_direction = 1
        tilt_pulse += SEARCH_STEP * tilt_direction * 5

    if tilt_pulse >= MAX_PULSE:
        tilt_pulse = MAX_PULSE
        tilt_direction = -1
    elif tilt_pulse <= MIN_PULSE:
        tilt_pulse = MIN_PULSE
        tilt_direction = 1

    pwm.set_pwm(PAN_CHANNEL, 0, int(pan_pulse))
    pwm.set_pwm(TILT_CHANNEL, 0, int(tilt_pulse))


def move_to_saved_position(target):
    global pan_pulse, tilt_pulse
    
    if target.has_saved_position():
        pan_pulse = target.saved_pan
        tilt_pulse = target.saved_tilt
        pwm.set_pwm(PAN_CHANNEL, 0, int(pan_pulse))
        pwm.set_pwm(TILT_CHANNEL, 0, int(tilt_pulse))
        print(f"Moving to TARGET {target.id} saved position: pan={pan_pulse}, tilt={tilt_pulse}")
        time.sleep(0.3)
        return True
    return False


def get_next_available_target_id():
    for i in range(1, 4):
        if not targets[i].has_saved_position():
            return i
    return None


def identify_target_from_position(current_pan, current_tilt):
    for i in range(1, 4):
        if targets[i].is_near_saved_position(current_pan, current_tilt):
            return i
    return None


def track_target(prediction, target_id):
    global pan_pulse, tilt_pulse, prev_error_x, prev_error_y, last_step_x, last_step_y, last_detection_time
    
    last_detection_time = time.time()
    
    error_x = prediction.x - CENTER_X
    error_y = prediction.y - CENTER_Y
    
    step_x = 0.0
    step_y = 0.0
    
    if abs(error_x) > DEADZONE:
        step_x = pd_step(error_x, prev_error_x, KP_PAN, KD_PAN, MAX_STEP)
        pan_pulse -= step_x
        last_step_x = step_x
    
    if abs(error_y) > DEADZONE:
        step_y = pd_step(error_y, prev_error_y, KP_TILT, KD_TILT, MAX_STEP)
        tilt_pulse += step_y
        last_step_y = step_y
    
    prev_error_x = error_x
    prev_error_y = error_y
    
    pan_pulse = clamp(pan_pulse, MIN_PULSE, MAX_PULSE)
    tilt_pulse = clamp(tilt_pulse, MIN_PULSE, MAX_PULSE)
    
    pwm.set_pwm(PAN_CHANNEL, 0, int(pan_pulse))
    pwm.set_pwm(TILT_CHANNEL, 0, int(tilt_pulse))
    
    target = targets[target_id]
    position_saved = target.update_position(prediction.x, prediction.y, prediction.width, prediction.height, pan_pulse, tilt_pulse)
    
    current_area = prediction.width * prediction.height
    
    return position_saved, error_x, error_y, current_area


def update_fire_lock_state(error_x, error_y):
    """
    Maintain fire_lock_start_time and fire_locked.
    Condition for counting: fire_mode ON, tracking target, and target inside DEADZONE.
    """
    global fire_lock_start_time, fire_locked, previous_fire_locked
    
    previous_fire_locked = fire_locked
    
    if not fire_mode or current_tracking_target is None:
        fire_lock_start_time = None
        fire_locked = False
        return
    
    centered = abs(error_x) <= DEADZONE and abs(error_y) <= DEADZONE
    
    if centered:
        if fire_lock_start_time is None:
            fire_lock_start_time = time.time()
            fire_locked = False
        else:
            elapsed = time.time() - fire_lock_start_time
            if elapsed >= FIRE_LOCK_TIME:
                fire_locked = True
                # NEW: Mark target as fired upon when lock completes
                if not previous_fire_locked and current_tracking_target:
                    targets[current_tracking_target].mark_fired_upon()
    else:
        fire_lock_start_time = None
        fire_locked = False


def get_fire_countdown():
    """
    Returns remaining seconds (int) before fire_lock completes, or None if not counting.
    """
    if not fire_mode or current_tracking_target is None or fire_lock_start_time is None:
        return None
    elapsed = time.time() - fire_lock_start_time
    remaining = FIRE_LOCK_TIME - elapsed
    if remaining < 0:
        remaining = 0
    return int(remaining + 0.99)


def draw_target_info(frame, predictions, last_error_x, last_error_y):
    # Crosshair and deadzone
    cv2.line(frame, (CENTER_X - 20, CENTER_Y), (CENTER_X + 20, CENTER_Y), (0, 255, 0), 2)
    cv2.line(frame, (CENTER_X, CENTER_Y - 20), (CENTER_X, CENTER_Y + 20), (0, 255, 0), 2)
    cv2.circle(frame, (CENTER_X, CENTER_Y), DEADZONE, (0, 255, 0), 1)
    
    # Mode
    mode_text = f"Mode: {current_mode}"
    cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Fire mode indicator (top-center)
    if fire_mode:
        text = "FIRE"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        x = frame.shape[1] // 2 - tw // 2
        y = 30
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    
    # Currently tracked target
    if current_tracking_target:
        target_text = f"Tracking: TARGET {current_tracking_target}"
        cv2.putText(frame, target_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Saved targets info (LEFT SIDE) - NEW: Show DEAD status
    y_offset = 90
    any_saved = any(targets[i].has_saved_position() for i in range(1, 4))
    if any_saved:
        for i in range(1, 4):
            target = targets[i]
            if target.has_saved_position():
                dead_status = " [DEAD]" if target.is_dead else ""
                status_text = f"T{i}: SAVED{dead_status} (pan={target.saved_pan}, tilt={target.saved_tilt})"
                color = (0, 0, 255) if target.is_dead else (0, 255, 0)
                cv2.putText(frame, status_text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                y_offset += 25
    
    # Fire countdown (top-right)
    countdown = get_fire_countdown()
    if countdown is not None:
        text = f"{countdown}s"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        x = frame.shape[1] - tw - 10
        y = 30
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    # NEW: Display "DEAD" at bottom center if currently tracked target is dead
    if current_tracking_target and targets[current_tracking_target].is_dead:
        text = "DEAD"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 2.0
        thickness = 4
        (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
        x = frame.shape[1] // 2 - tw // 2
        y = frame.shape[0] - 30
        cv2.putText(frame, text, (x, y), font, font_scale, (0, 0, 255), thickness)
    
    # Draw detections
    for prediction in predictions:
        x, y = int(prediction.x), int(prediction.y)
        w, h = int(prediction.width), int(prediction.height)
        x1 = x - w // 2
        y1 = y - h // 2
        x2 = x + w // 2
        y2 = y + h // 2
        
        is_tracked = current_tracking_target is not None
        
        # Box color: red if fire_locked, else yellow if tracked, else blue
        if is_tracked and fire_locked:
            color = (0, 0, 255)
        elif is_tracked:
            color = (0, 255, 255)
        else:
            color = (255, 0, 0)
        thickness = 3 if is_tracked else 2
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        
        if is_tracked:
            label = f"TARGET {current_tracking_target}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10),
                          (x1 + label_size[0] + 10, y1), color, -1)
            cv2.putText(frame, label, (x1 + 5, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            
            # Stationary progress
            target = targets[current_tracking_target]
            progress = target.get_stationary_progress()

            if progress > 0 and not target.has_saved_position():
                progress_text = f"Still: {progress:.1f}s/{STATIONARY_TIME}s"
                cv2.putText(frame, progress_text, (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        cv2.circle(frame, (x, y), 5, color, -1)
    
    return frame


# --- RoboflowOak Setup -------------------------------------------
rf = RoboflowOak(
    model="waterbottledetection-roa31",
    confidence=0.94,
    overlap=0.5,
    version="4",
    api_key="WhkhgsS4zdmDm2iZ4UBb",
    rgb=True,
    depth=False,
    device=None,
    blocking=True
)

pwm.set_pwm(PAN_CHANNEL, 0, MID_PULSE)
pwm.set_pwm(TILT_CHANNEL, 0, MID_PULSE)
time.sleep(0.5)

print("=" * 60)
print("WATER BOTTLE TRACKER - Multi-Target System")
print("=" * 60)
print("Controls:")
print("  1,2,3  - Track specific target")
print("  T      - SCAN mode")
print("  A      - AUTO mode")
print("  F      - Toggle FIRE mode")
print("  Q      - Quit")
print("=" * 60)
print("? Starting in SCAN mode")

# --- Main Loop ---------------------------------------------------
last_error_x = 0
last_error_y = 0

while True:
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('1'):
        current_mode = MODE_MANUAL_1
        searching_for_target_id = 1
        current_tracking_target = None
        fire_lock_start_time = None
        fire_locked = False
        if not move_to_saved_position(targets[1]):
            print("? Searching for TARGET 1...")
    elif key == ord('2'):
        current_mode = MODE_MANUAL_2
        searching_for_target_id = 2
        current_tracking_target = None
        fire_lock_start_time = None
        fire_locked = False
        if not move_to_saved_position(targets[2]):
            print("? Searching for TARGET 2...")
    elif key == ord('3'):
        current_mode = MODE_MANUAL_3
        searching_for_target_id = 3
        current_tracking_target = None
        fire_lock_start_time = None
        fire_locked = False
        if not move_to_saved_position(targets[3]):
            print("? Searching for TARGET 3...")
    elif key == ord('t'):
        current_mode = MODE_SCAN
        current_tracking_target = None
        searching_for_target_id = None
        scan_target_start_time = None
        scan_targets_visited.clear()
        fire_lock_start_time = None
        fire_locked = False
        print("? Entering SCAN mode")
    elif key == ord('a'):
        current_mode = MODE_AUTO
        current_tracking_target = None
        searching_for_target_id = None
        fire_lock_start_time = None
        fire_locked = False
        print("? AUTO mode")
    elif key == ord('f'):
        fire_mode = not fire_mode
        fire_lock_start_time = None
        fire_locked = False
        print(f"? FIRE mode {'ON' if fire_mode else 'OFF'}")
    
    result, frame, raw_frame, depth = rf.detect()
    predictions = result["predictions"]
    
    # --- SCAN MODE ---
    if current_mode == MODE_SCAN:
        if predictions:
            p = predictions[0]
            if current_tracking_target is None:
                matched_target_id = identify_target_from_position(pan_pulse, tilt_pulse)
                if matched_target_id and matched_target_id not in scan_targets_visited:
                    current_tracking_target = matched_target_id
                    scan_target_start_time = time.time()
                    scan_targets_visited.add(matched_target_id)
                    print(f"SCAN: Re-found TARGET {matched_target_id}")
                elif matched_target_id and matched_target_id in scan_targets_visited:
                    search_for_target()
                else:
                    next_id = get_next_available_target_id()
                    if next_id is not None:
                        current_tracking_target = next_id
                        scan_target_start_time = time.time()
                        scan_targets_visited.add(next_id)
                        print(f"SCAN: New TARGET {next_id}")
                    else:
                        search_for_target()
            if current_tracking_target:
                position_saved, err_x, err_y, current_area = track_target(p, current_tracking_target)
                last_error_x, last_error_y = err_x, err_y
                target = targets[current_tracking_target]
                
                # NEW: Check if target is dead
                target.check_if_dead(current_area)
                
                progress = target.get_stationary_progress()
                time_on_target = time.time() - scan_target_start_time if scan_target_start_time else 0
                print(f"SCAN T{current_tracking_target} | Error: ({err_x:+.0f},{err_y:+.0f}) | Still: {progress:.1f}s | Time: {time_on_target:.1f}s")
                if position_saved or time_on_target >= SCAN_MAX_TIME_PER_TARGET:
                    current_tracking_target = None
                    scan_target_start_time = None
                    fire_lock_start_time = None
                    fire_locked = False
        else:
            search_for_target()
            current_tracking_target = None
            fire_lock_start_time = None
            fire_locked = False
    
    # --- MANUAL MODE ---
    elif current_mode in [MODE_MANUAL_1, MODE_MANUAL_2, MODE_MANUAL_3]:
        target_id = int(current_mode[-1])
        if predictions:
            if searching_for_target_id == target_id:
                current_tracking_target = target_id
                searching_for_target_id = None
                fire_lock_start_time = None
                fire_locked = False
                print(f"? Found TARGET {target_id}")
            if current_tracking_target == target_id:
                p = predictions[0]
                position_saved, err_x, err_y, current_area = track_target(p, target_id)
                last_error_x, last_error_y = err_x, err_y
                target = targets[target_id]
                
                # NEW: Check if target is dead
                target.check_if_dead(current_area)
                
                progress = target.get_stationary_progress()
                print(f"MANUAL T{target_id} | Error: ({err_x:+.0f},{err_y:+.0f}) | {'Still' if progress>0 else 'Moving'}")
        else:
            time_since_detection = time.time() - last_detection_time
            if time_since_detection >= SEARCH_TIMEOUT:
                if last_step_x > 0: pan_direction = -1
                elif last_step_x < 0: pan_direction = 1
                if last_step_y > 0: tilt_direction = 1
                elif last_step_y < 0: tilt_direction = -1
                search_for_target()
            fire_lock_start_time = None
            fire_locked = False
    
    # --- AUTO MODE ---
    else:
        if predictions:
            if current_tracking_target is None:
                matched_target_id = identify_target_from_position(pan_pulse, tilt_pulse)
                if matched_target_id:
                    current_tracking_target = matched_target_id
                    print(f"AUTO: Re-found TARGET {matched_target_id}")
                else:
                    next_id = get_next_available_target_id()
                    if next_id is not None:
                        current_tracking_target = next_id
                        print(f"AUTO: Assigned TARGET {next_id}")
                    else:
                        current_tracking_target = 1
            p = predictions[0]
            position_saved, err_x, err_y, current_area = track_target(p, current_tracking_target)
            last_error_x, last_error_y = err_x, err_y
            target = targets[current_tracking_target]
            
            # NEW: Check if target is dead
            target.check_if_dead(current_area)
            
            progress = target.get_stationary_progress()
            print(f"AUTO T{current_tracking_target} | Error: ({err_x:+.0f},{err_y:+.0f}) | {'Still' if progress>0 else 'Moving'}")
        else:
            time_since_detection = time.time() - last_detection_time
            if time_since_detection >= SEARCH_TIMEOUT:
                if last_step_x > 0: pan_direction = -1
                elif last_step_x < 0: pan_direction = 1
                if last_step_y > 0: tilt_direction = 1
                elif last_step_y < 0: tilt_direction = -1
                search_for_target()
            fire_lock_start_time = None
            fire_locked = False
    
    # Update fire lock state after latest tracking error
    update_fire_lock_state(last_error_x, last_error_y)
    
    # Draw HUD
    frame = draw_target_info(frame, predictions, last_error_x, last_error_y)
    cv2.imshow("frame", frame)

cv2.destroyAllWindows()
