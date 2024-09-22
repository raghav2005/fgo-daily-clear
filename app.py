import pyautogui as pag
import time
import subprocess
from loguru import logger
import os
from Quartz.CoreGraphics import (
    CGEventCreateScrollWheelEvent,
    kCGScrollEventUnitLine,
    kCGEventScrollWheel,
    kCGEventSourceStateCombinedSessionState,  # Use this instead of kCGEventSourceStateHID
    CGEventPost
)

# msg_type: one of ["success", "error", "trace", "info", "warning", "critical", "debug"]
def log(msg, msg_type="success"):
    try:
        getattr(logger, msg_type)(msg)
    except Exception as e:
        logger.error(e)


pag.PAUSE = 1.5
        
        
# launch iphone mirroring app
def launch_iphone_mirroring():
    try:
        script = 'tell application "iPhone Mirroring" to activate'
        subprocess.run(['osascript', '-e', script], check=True)

        log("iphone mirroring app launched.", "debug")
        time.sleep(1.5)
        
    except subprocess.CalledProcessError as e:
        log(f"failed to launch iphone mirroring app: {e}", "error")

# focus on the iphone mirroring window using applescript
def focus_iphone_mirroring_window():
    try:
        # Combine both AppleScript commands into a single script
        script = '''
        tell application "System Events"
            tell process "iPhone Mirroring"
                set frontmost to true
                set visible to true
            end tell
        end tell
        '''
        # Run the combined script
        subprocess.run(['osascript', '-e', script], check=True)

        log("iphone mirroring window focused and visible.", "debug")
        time.sleep(1.5)

    except subprocess.CalledProcessError as e:
        log(f"error focusing iphone mirroring window: {e}", "error")

# function to get the region of the iphone mirroring window
def get_iphone_mirroring_region():
    try:
        script = 'tell application "System Events" to tell process "iPhone Mirroring" to get {position, size} of front window'
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)

        win_bounds = result.stdout.strip().split(", ")

        if len(win_bounds) == 4:
            left, top, width, height = map(lambda x: abs(int(x)), win_bounds)
            log(f"iPhone Mirroring window region: {(left, top + 30, width, height)}", "info")

            return (left, top, width, height)

        else:
            log("failed to retrieve iphone mirroring window bounds", "error")
            return None
        
    except subprocess.CalledProcessError as e:
        log(f"error getting iphone mirroring window bounds: {e}", "error")
        return None

# # function to scroll (simulate 2-finger swipe up) in the center of the iphone mirroring window
# def perform_two_finger_swipe():
#     log("performing two-finger swipe.", "debug")

#     region = get_iphone_mirroring_region()

#     if region:
#         left, top, width, height = region
#         center_x = left + width // 2
#         center_y = top + height // 2
#         log(f"Scrolling at center: ({center_x}, {center_y})", "debug")

#         # move to the center of the window and perform a scroll
#         pag.moveTo(center_x, center_y, duration=0.5)
#     #     # pag.scroll(-500)  # negative scroll value for scrolling up
#     #     # log("scroll performed (simulated two-finger swipe up).", "info")
#     #     time.sleep(1.5)
#     # else:
#     #     log("unable to get iPhone Mirroring window region for scrolling.", "error")

#         time.sleep(1.5)
#         log("performing scroll using Quartz.", "debug")

#         # Create a scroll event, -10 is the value to scroll up (positive scrolls down)
#         scroll_event = CGEventCreateScrollWheelEvent(
#             kCGEventSourceStateCombinedSessionState,  # event source
#             kCGScrollEventUnitLine,  # scrolling in "lines" rather than "pixels"
#             1,  # 1 represents a vertical scroll
#             -10  # Negative scrolls up, positive scrolls down
#         )

#         # Post the event to the system
#         CGEventPost(kCGEventScrollWheel, scroll_event)
#         log("scroll performed using Quartz.", "info")
#         time.sleep(1.5)

# # click the search button and search for fate/go
# def search_and_open_fate_go():
#     log("searching for fate/go using the search function.", "debug")

#     search_button_path = 'img/search_button.png'  # make sure this screenshot is provided
#     if not os.path.exists(search_button_path):
#         log(f"search button image '{search_button_path}' not found.", "error")
#         return False

#     try:
#         # get the iphone mirroring window region
#         region = get_iphone_mirroring_region()

#         if region:

#             pag.screenshot(region=region).save('img/ss.png')
            
#             # locate and click the search button only within the iphone mirroring app region
#             search_button_location = pag.locateCenterOnScreen(search_button_path, region=region, confidence=0.8)
#             log(f"search_button_location: {search_button_location}", "debug")

#             if search_button_location:
#                 log(search_button_location, "debug")
#                 pag.moveTo(search_button_location, duration=0.5)
#                 pag.click(search_button_location)  # click on the search button
#                 log("search button found and clicked.", "info")
#                 time.sleep(1.5)  # give time for the search field to appear

#                 # type "fate/go"
#                 pag.write('fate/go', interval=0.1)
#                 pag.press('enter')
#                 log("fate/go entered into search bar.", "info")
#                 time.sleep(5)  # wait for search results

#                 # now locate and click on the fate/go result
#                 game_icon_path = 'img/fgo_game_icon.png'  # reuse the fgo game icon image
#                 icon_location = pag.locateCenterOnScreen(game_icon_path, region=region, confidence=0.7)
#                 if icon_location:
#                     pag.click(icon_location)  # click on the game icon in the search results
#                     log("fate/go game icon found in search results and clicked.", "info")
#                     time.sleep(2)  # wait for the game to launch
#                     return True
#                 else:
#                     log("fate/go game icon not found in search results.", "warning")
#                     return False
#             else:
#                 log("search button not found within the defined region.", "warning")
#                 return False
#         else:
#             log("unable to define iphone mirroring window region.", "error")
#             return False
#     except Exception as e:
#         log(f"error during search and open for fate/go: {e}", "error")
#         return False

# main function to run the automation
def main():
    # step 1: launch and focus the iphone mirroring app
    launch_iphone_mirroring()
    focus_iphone_mirroring_window()

    region = get_iphone_mirroring_region()
    # pag.screenshot(region=region).save('img/ss.png')
    # pag.screenshot(region=(20, 576, 256, 42)).save('img/search_button.png')
    # r = None
    # while r is None:
    #     try:
    #         r = pag.locateCenterOnScreen('img/search_button.png', confidence=0.7, region=region, grayscale=True)
    #         if r is not None:
    #             log(f"Image found at location: {r}", "info")
                
    #     except pag.ImageNotFoundException:
    #         log("Image not found. Retrying...", "info")
    #         time.sleep(1)  # Optional: Add a short delay between retries
            
    # log(f"final r: {r}", "info")
    # pag.moveTo(r.x, r.y)

    # 607-624, (312x694) - Jash
    # 585-608, (300x668) - Raghav

    # x, y, w, h
    pag.moveTo((region[0] + region[2]) // 2, (region[1] + region[3]) * 0.85)

    # log("attempting opening search menu", "debug")
    # perform_two_finger_swipe()
    # log("opened search menu", "debug")
    
    # # step 2: open the fate/go game by clicking the icon
    # log("attempting to search for fate/go.", "info")
    # if search_and_open_fate_go():
    #     log("fate/go successfully opened via search.", "info")
    # else:
    #     log("failed to open fate/go.", "error")

if __name__ == "__main__":
    main()
