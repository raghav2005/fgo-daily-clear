import pyautogui as pag
import time
import subprocess
import os
import pytesseract
import mss
import mss.tools
from loguru import logger
from PIL import Image
from Quartz.CoreGraphics import (
    CGEventCreateScrollWheelEvent,
    kCGScrollEventUnitLine,
    kCGEventScrollWheel,
    kCGEventSourceStateCombinedSessionState,  # Use this instead of kCGEventSourceStateHID
    CGEventPost,
)


# msg_type: one of ["success", "error", "trace", "info", "warning", "critical", "debug"]
def log(msg, msg_type="success"):
    try:
        getattr(logger, msg_type)(msg)
    except Exception as e:
        logger.error(e)


GENERAL_LONG_SLEEP = 10
pag.PAUSE = 1


def capture_screenshot(region=None, output_path="screenshot.png"):
    with mss.mss() as sct:
        if region:  # capture a specific region or the whole screen
            screenshot = sct.grab(region)
        else:  # full screen
            screenshot = sct.grab(sct.monitors[0])

        # save to file
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)


# function to perform OCR on a screenshot and check for specific text
def check_text_in_image(image_path, search_text):
    # load the image
    img = Image.open(image_path)

    # use tesseract to extract text
    extracted_text = pytesseract.image_to_string(img)

    # check if the target text is in the extracted text
    if search_text in extracted_text:
        log(f"Found text: {search_text}", "success")
        return True

    else:
        log(f"Did not find text: {search_text}", "warning")
        return False


# function to find the bounding box of specific text in an image
def find_text_location(image_path, search_text):
    # load the image
    img = Image.open(image_path)
    # use Tesseract to get detailed information about the text in the image
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    log(data, "info")

    for i in range(len(data["text"])):
        # if the detected text matches the search text
        if search_text.lower() in data["text"][i].lower():
            x, y, w, h = (
                data["left"][i],
                data["top"][i],
                data["width"][i],
                data["height"][i],
            )
            log(
                f"Found text: {search_text} (at ({x}, {y}) with width: {w}, height: {h})",
                "success",
            )
            return (x, y, w, h)

    log(f"Did not find text: {search_text}", "warning")
    return None


# launch iphone mirroring app
def launch_iphone_mirroring():
    try:
        script = 'tell application "iphone Mirroring" to activate'
        subprocess.run(["osascript", "-e", script], check=True)

        log("iphone mirroring app launched.", "debug")
        time.sleep(1.5)

    except subprocess.CalledProcessError as e:
        log(f"failed to launch iphone mirroring app: {e}", "error")


# focus on the iphone mirroring window using applescript
def focus_iphone_mirroring_window():
    try:
        # Combine both AppleScript commands into a single script
        script = """
        tell application "System Events"
            tell process "iPhone Mirroring"
                set frontmost to true
                set visible to true
            end tell
        end tell
        """
        # Run the combined script
        subprocess.run(["osascript", "-e", script], check=True)

        log("iphone mirroring window focused and visible.", "debug")
        time.sleep(1.5)

    except subprocess.CalledProcessError as e:
        log(f"error focusing iphone mirroring window: {e}", "error")


# function to get the region of the iphone mirroring window
def get_iphone_mirroring_region():
    try:
        script = 'tell application "System Events" to tell process "iPhone Mirroring" to get {position, size} of front window'
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, check=True
        )

        win_bounds = result.stdout.strip().split(", ")

        if len(win_bounds) == 4:
            left, top, width, height = map(lambda x: abs(int(x)), win_bounds)
            log(
                f"iphone Mirroring window region: {(left, top + 30, width, height)}",
                "info",
            )

            return (left, top, width, height)

        else:
            log("failed to retrieve iphone mirroring window bounds", "error")
            return None

    except subprocess.CalledProcessError as e:
        log(f"error getting iphone mirroring window bounds: {e}", "error")
        return None


def main():
    # launch and focus the iphone mirroring app
    launch_iphone_mirroring()
    focus_iphone_mirroring_window()

    region = get_iphone_mirroring_region()
    left, top, width, height = region

    # click on search button
    pag.moveTo((region[0] + region[2]) // 2, (region[1] + region[3]) * 0.85)
    pag.click()

    # open fgo
    pag.write("fate/go", interval=0.05)
    pag.press("enter")
    log("fate/go entered into search bar.", "debug")

    region = get_iphone_mirroring_region()
    left, top, width, height = region

    # click for first loading screen
    found = False
    while not found:
        capture_screenshot(
            region={"top": top, "left": left, "width": width, "height": height},
            output_path="img/screenshots/first_tap_on_open.png",
        )
        found = check_text_in_image(
            "img/screenshots/first_tap_on_open.png", "Please Tap the Screen"
        )
        time.sleep(1)
    pag.moveTo((region[0] + region[2]) // 2, (region[1] + region[3]) // 2)
    pag.click()

    # click for second loading screen
    time.sleep(GENERAL_LONG_SLEEP)
    pag.click()
    time.sleep(GENERAL_LONG_SLEEP)

    # in case friend popup comes up
    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/potential_friend_popup.png",
    )
    if check_text_in_image(
        "img/screenshots/potential_friend_popup.png", "Friend Points"
    ) or check_text_in_image(
        "img/screenshots/potential_friend_popup.png", "Most used Servant"
    ):
        bbox = find_text_location("img/screenshots/potential_friend_popup.png", "Close")
        if bbox:
            x, y, width, height = bbox
            log(
                f"Bounding box for 'Close': x={x}, y={y}, width={width}, height={height}"
            )
            pag.moveTo(region[0] + x, region[1] + y)
        else:
            pag.moveTo((region[0] + region[2]) * 0.3, (region[1] + region[3]) * 0.85)
        pag.click()
        time.sleep(GENERAL_LONG_SLEEP)
    
    # in case news shows up
    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/potential_news.png",
    )
    if check_text_in_image(
        "img/screenshots/potential_news.png", "News"
    ) or check_text_in_image(
        "img/screenshots/potential_news.png", "Maintenance"
    ) or check_text_in_image(
        "img/screenshots/potential_news.png", "Issues"
    ) or check_text_in_image(
        "img/screenshots/potential_news.png", "Facebook"
    ) or check_text_in_image(
        "img/screenshots/potential_news.png", "X (Twitter)"
    ):
        pag.moveTo((region[0] + region[2]) * 0.885, (region[1] + region[3]) * 0.24)
        pag.click()
        time.sleep(GENERAL_LONG_SLEEP)

    # in case of any close buttons
    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/potential_close_btns.png",
    )
    loc_close_happened = False
   
    try:
        loc_close = pag.locateCenterOnScreen("img/screenshots/close_btn.png", confidence=0.8)
        loc_close_exists = True
    except pag.ImageNotFoundException:
        loc_close_exists = False

    while loc_close_exists or check_text_in_image("img/screenshots/potential_close_btns.png", "Close"):
        loc_close_happened = True
        if loc_close_exists:
            pag.moveTo(loc_close.x, loc_close.y)
            pag.click()
        else:
            bbox = find_text_location(
                "img/screenshots/potential_close_btns.png", "Close"
            )
            if bbox:
                x, y, width, height = bbox
                log(
                    f"Bounding box for 'Close': x={x}, y={y}, width={width}, height={height}"
                )
                pag.moveTo(region[0] + x, region[1] + y)
            else:
                pag.moveTo((region[0] + region[2]) * 0.5, (region[1] + region[3]) * 0.835)
            pag.click()

        try:
            loc_close = pag.locateCenterOnScreen("img/screenshots/close_btn.png", confidence=0.8)
            loc_close_exists = True
        except pag.ImageNotFoundException:
            loc_close_exists = False

    if loc_close_happened:
        time.sleep(GENERAL_LONG_SLEEP)

    # drag scroll bar to top of screen
    pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.35)
    pag.click()
    pag.dragTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.3, button="left")
    
    # open Chaldea Gate menu
    try:
        loc_chaldea_gate = pag.locateCenterOnScreen("img/screenshots/chaldea_gate.png", confidence=0.8)
        pag.moveTo(loc_chaldea_gate.x // 2, loc_chaldea_gate.y // 2)
        pag.click()
    except pag.ImageNotFoundException:
        capture_screenshot(
            region={"top": top, "left": left, "width": width, "height": height},
            output_path="img/screenshots/fgo_in_game_homescreen.png",
        )
        bbox = find_text_location(
            "img/screenshots/fgo_in_game_homescreen.png", "Chaldea Gate"
        )
        if bbox:
            x, y, width, height = bbox
            log(
                f"Bounding box for 'Chaldea Gate': x={x}, y={y}, width={width}, height={height}"
            )
            pag.moveTo(region[0] + x, region[1] + y)
        else:
            pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.61) # NOTE: won't work if event - change 0.61 to something higher
        pag.click()
    
    # open Daily Quests menu
    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/chaldea_gate_menu.png",
    )
    bbox = find_text_location("img/screenshots/chaldea_gate_menu.png", "Daily Quests")
    if bbox:
        x, y, width, height = bbox
        log(
            f"Bounding box for 'Daily Quests': x={x}, y={y}, width={width}, height={height}"
        )
        pag.moveTo(region[0] + x, region[1] + y)
    else:
        pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.4)
    pag.click()

    # drag scroll bar to top of screen
    pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.35)
    pag.click()
    pag.dragTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.3, button="left")
    
    # scroll to find Extreme QP quest
    curr_y = (region[1] + region[3]) * 0.3
    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/daily_quests_menu.png",
    )
    bbox = find_text_location(
        "img/screenshots/daily_quests_menu.png", "Enter the Treasure Vault - Extreme"
    )
    if bbox:
        x, y, width, height = bbox
        log(
            f"Bounding box for 'Enter the Treasure Valut - Extreme': x={x}, y={y}, width={width}, height={height}"
        )
        pag.moveTo(region[0] + x, region[1] + y)
    else:
        while not bbox:
            if curr_y >= ((region[1] + region[3]) * 0.835):
                break

            curr_y += (region[1] + region[3]) * 0.05
            pag.dragTo((region[0] + region[2]) * 0.925, curr_y, button="left")
            
            capture_screenshot(
                region={"top": top, "left": left, "width": width, "height": height},
                output_path="img/screenshots/daily_quests_menu.png",
            )
            bbox = find_text_location(
                "img/screenshots/daily_quests_menu.png", "Enter the Treasure Vault - Extreme"
            )

        if bbox:
            x, y, width, height = bbox
            log(
                f"Bounding box for 'Enter the Treasure Vault - Extreme': x={x}, y={y}, width={width}, height={height}"
            )
            pag.moveTo(region[0] + x, region[1] + y)
        else:
            pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.835)
            pag.click()

            # click on QP Extreme quest
            pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.4)
            pag.click()

    time.sleep(GENERAL_LONG_SLEEP)

    # switch to caster class
    loc = pag.locateCenterOnScreen("img/screenshots/friend_support_caster_class.png", confidence=0.8)
    pag.moveTo(loc.x // 2, loc.y // 2)
    pag.click()

    # make sure at top of list
    pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.4)
    pag.click()

    # find end of scrollbar if need to scroll
    loc = pag.locateOnScreen("img/screenshots/friend_support_scrollbar.png", confidence=0.8)
    curr_y = (loc.top + loc.height) // 2
    pag.moveTo((loc.left + (loc.width / 2)) // 2, curr_y)

    found = False
    while not found:
        try:
            # select castoria
            loc_support = pag.locateCenterOnScreen("img/screenshots/friend_support_altria_caster.png", confidence=0.8)
            pag.moveTo(loc_support.x // 2, loc_support.y // 2)
            pag.click()
            found = True
        except pag.ImageNotFoundException:
            # scroll to next supports
            curr_y += loc.height // 4
            pag.dragTo((region[0] + region[2]) * 0.925, curr_y, button="left", duration=0.5)


if __name__ == "__main__":
    main()


### GOOD CODES TO HAVE:

# capture_screenshot(
#     region={"top": top, "left": left, "width": width, "height": height},
#     output_path="img/screenshots/ss.png",
# )
