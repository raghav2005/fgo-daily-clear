import pyautogui
import time
import subprocess
import os
import logging
import pygetwindow as gw

# Set up logging
logging.basicConfig(filename='fgo_automation.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

IMAGE_DIR = 'img/'  # Relative directory for image files
LIVE_SCREENSHOT_DIR = 'screenshots/'  # Directory to store live screenshots

# Ensure screenshot directory exists
if not os.path.exists(LIVE_SCREENSHOT_DIR):
    os.makedirs(LIVE_SCREENSHOT_DIR)

# Function to capture a live screenshot for comparison
def capture_live_screenshot(filename="live_screenshot.png"):
    live_screenshot_path = os.path.join(LIVE_SCREENSHOT_DIR, filename)
    pyautogui.screenshot(live_screenshot_path)
    logging.info(f"Captured live screenshot: {live_screenshot_path}")
    return live_screenshot_path

# Function to switch to the iPhone Mirroring app using AppleScript
def switch_to_app(app_name):
    try:
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        time.sleep(2)  # Give some time for the app to come into focus
        logging.info(f"Switched to {app_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error switching to {app_name}: {e}")
        print(f"Error switching to {app_name}: {e}")

# Function to bring iPhone Mirroring app into focus by clicking on it
def focus_iphone_mirroring():
    logging.info("Ensuring iPhone Mirroring app is in focus.")
    # Move mouse to the top-left corner where the iPhone Mirroring app is usually located
    # This is just a safety click, as we will use pygetwindow to handle focus
    pyautogui.moveTo(100, 100)  # Adjust based on your screen setup if necessary
    pyautogui.click()
    time.sleep(1)  # Wait for focus to change

# Function to locate an image on screen and click it within a region
def click_image(image_name, confidence=0.8, region=None):
    image_path = os.path.join(IMAGE_DIR, image_name)  # Full path to the image
    try:
        logging.info(f"Looking for image: {image_name} with confidence: {confidence}")
        location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence, region=region)
        if location:
            pyautogui.click(location)
            logging.info(f"Found and clicked image: {image_name}")
            time.sleep(1)
        else:
            logging.warning(f"Image {image_name} not found with confidence {confidence}")
            capture_live_screenshot(f"missing_{image_name}")
    except pyautogui.ImageNotFoundException:
        logging.error(f"Image {image_name} could not be located on the screen.")
        capture_live_screenshot(f"missing_{image_name}")
        print(f"Image {image_name} could not be located on the screen.")

# Function to get the bounding box (region) of the iPhone Mirroring window using pygetwindow
def get_iphone_mirroring_region():
    try:
        windows = gw.getWindowsWithTitle("iPhone Mirroring")  # Adjust the title based on your window's name
        if windows:
            window = windows[0]
            if not window.isMinimized:  # Ensure the window is not minimized
                logging.info(f"Found iPhone Mirroring window at ({window.left}, {window.top}) with size ({window.width}, {window.height})")
                return (window.left, window.top, window.width, window.height)
            else:
                logging.warning("iPhone Mirroring window is minimized.")
                return None
        else:
            logging.warning("iPhone Mirroring window not found.")
            return None
    except Exception as e:
        logging.error(f"Error getting iPhone Mirroring window region: {e}")
        return None

# Step 1: Switch to iPhone Mirroring app and ensure focus
switch_to_app("iPhone Mirroring")
focus_iphone_mirroring()

# Step 2: Add delay for screen transition and search for 'Chaldea Gate'
time.sleep(2)

# Step 3: Get the region where the iPhone Mirroring app is located using pygetwindow
mirroring_region = get_iphone_mirroring_region()

if mirroring_region:
    # Step 4: Click on 'Chaldea Gate' within the iPhone Mirroring app region
    click_image('chaldea_gate.png', region=mirroring_region)

    # Step 5: Add delay before searching for 'Dailies'
    time.sleep(2)

    # Step 6: Click on 'Dailies' within the region
    click_image('daily_quests.png', region=mirroring_region)

    # Step 7: Scroll down and locate '40AP QP quest'
    for _ in range(10):
        location = pyautogui.locateCenterOnScreen(os.path.join(IMAGE_DIR, 'extreme_ap_quest.png'), confidence=0.6, region=mirroring_region)
        if location:
            logging.info("Found 40AP QP quest.")
            break
        pyautogui.scroll(-500)  # Scroll down
        time.sleep(1)  # Wait for the scroll effect

    # Step 8: Click on '40AP QP quest'
    click_image('extreme_ap_quest.png', region=mirroring_region)

    # Capture final screenshot after script completion
    capture_live_screenshot("final_state.png")
else:
    logging.error("iPhone Mirroring window region could not be found. Exiting...")
    print("iPhone Mirroring window region could not be found. Exiting...")
