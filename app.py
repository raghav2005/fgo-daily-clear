import pyautogui as pag
import time
import subprocess
import os
import pytesseract
import mss
import mss.tools
import random
from loguru import logger
from PIL import Image
from Quartz.CoreGraphics import (
    CGEventCreateScrollWheelEvent,
    kCGScrollEventUnitLine,
    kCGEventScrollWheel,
    kCGEventSourceStateCombinedSessionState,  # Use this instead of kCGEventSourceStateHID
    CGEventPost,
    CGEventCreateMouseEvent,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventLeftMouseDragged,
    kCGEventMouseMoved,
    kCGMouseButtonLeft,
    kCGHIDEventTap,
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


# def mouse_event(event_type, x, y):
#     event = CGEventCreateMouseEvent(None, event_type, (x, y), kCGMouseButtonLeft)
#     CGEventPost(kCGHIDEventTap, event)


# def force_click(x, y, hold_duration=0.5):
#     """
#     Simulates a 'force click' by holding down the left mouse button for a specific duration.

#     Args:
#         x (int): X-coordinate for the click.
#         y (int): Y-coordinate for the click.
#         hold_duration (float): Time in seconds to hold the click.
#     """
#     # Simulate left mouse button down
#     mouse_event(kCGEventLeftMouseDown, x, y)

#     # Hold the click for the specified duration
#     time.sleep(hold_duration)

#     # Simulate left mouse button up
#     mouse_event(kCGEventLeftMouseUp, x, y)
#     log(f"Force click performed at ({x}, {y}) with duration {hold_duration}s", "info")


# def simulate_touch_drag(x, y, duration=0.5):
#     mouse_event(kCGEventLeftMouseDown, x, y)
#     time.sleep(duration)
#     mouse_event(kCGEventLeftMouseDragged, x + 1, y + 1)  # Small drag
#     mouse_event(kCGEventLeftMouseUp, x, y)


# launch iphone mirroring app
def launch_iphone_mirroring():
    try:
        script = 'tell application "iPhone Mirroring" to activate'
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
                f"iphone mirroring window region: {(left, top + 30, width, height)}",
                "info",
            )

            return (left, top, width, height)

        else:
            log("failed to retrieve iphone mirroring window bounds", "error")
            return None

    except subprocess.CalledProcessError as e:
        log(f"error getting iphone mirroring window bounds: {e}", "error")
        return None


def switch_party(region, party_num):
    pag.moveTo(
        (region[0] + region[2]) * (0.428 + (0.01575 * (party_num - 1))),
        (region[1] + region[3]) * 0.255,
    )
    pag.click()


def skill_click(general_fields, servant_num, skill_num, servant_select_num=2):
    region = general_fields["region"]
    left, top, width, height = (
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    pag.moveTo(
        (region[0] + region[2])
        * (0.085 + (0.2 * (servant_num - 1)) + (0.055 * (skill_num - 1))),
        (region[1] + region[3]) * 0.8075,
    )
    pag.click()
    time.sleep(1)

    target_selectable = False
    try:
        loc = pag.locateCenterOnScreen("img/screenshots/skill_select_servant_close_btn.png", confidence=0.8)
        target_selectable = True
    except:
        capture_screenshot(
            region={"top": top, "left": left, "width": width, "height": height},
            output_path="img/screenshots/skill_target_selectable_screen.png",
        )
        search_words = ["Select", "Target", "Select Target"]
        search_words_results = [
            check_text_in_image(
                "img/screenshots/skill_target_selectable_screen.png", search_word
            )
            for search_word in search_words
        ]
        if True in search_words_results:
            target_selectable = True

    if target_selectable:
        pag.moveTo((region[0] + region[2]) * (0.3 + (0.2 * (servant_select_num - 1))), (region[1] + region[3]) * 0.625)
        pag.click()

    wait_for_screen(general_fields, "img/screenshots/battle_screen_menu_btn.png", "img/screenshots/battle_screen_menu_btn_found.png", "Battle Menu")
    time.sleep(1)


def master_skill_click(general_fields, skill_num, servant_select_num=2):
    region = general_fields["region"]
    left, top, width, height = (
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    try:
        loc_master_skill = pag.locateCenterOnScreen(
            "img/screenshots/master_skill_btn.png", confidence=0.8
        )
        pag.moveTo(loc_master_skill.x // 2, loc_master_skill.y // 2)
    except pag.ImageNotFoundException:
        pag.moveTo((region[0] + region[2]) * 0.895, (region[1] + region[3]) * 0.55)
    pag.click()

    pag.moveTo(
        (region[0] + region[2]) * (0.715 + (0.055 * (skill_num - 1))),
        (region[1] + region[3]) * 0.54,
    )
    pag.click()
    time.sleep(1)

    target_selectable = False
    try:
        loc = pag.locateCenterOnScreen("img/screenshots/skill_select_servant_close_btn.png", confidence=0.8)
        target_selectable = True
    except:
        capture_screenshot(
            region={"top": top, "left": left, "width": width, "height": height},
            output_path="img/screenshots/skill_target_selectable_screen.png",
        )
        search_words = ["Select", "Target", "Select Target"]
        search_words_results = [
            check_text_in_image(
                "img/screenshots/skill_target_selectable_screen.png", search_word
            )
            for search_word in search_words
        ]
        if True in search_words_results:
            target_selectable = True

    if target_selectable:
        pag.moveTo((region[0] + region[2]) * (0.3 + (0.2 * (servant_select_num - 1))), (region[1] + region[3]) * 0.625)
        pag.click()

    wait_for_screen(general_fields, "img/screenshots/battle_screen_menu_btn.png", "img/screenshots/battle_screen_menu_btn_found.png", "Battle Menu")
    time.sleep(1)


def np_card_click(region, servant_num):
    pag.moveTo(
        (region[0] + region[2]) * (0.355 + (0.145 * (servant_num - 1))),
        (region[1] + region[3]) * 0.4,
    )
    pag.click()


def face_card_click(region, face_card_num):
    pag.moveTo(
        (region[0] + region[2]) * (0.18 + (0.16 * (face_card_num - 1))),
        (region[1] + region[3]) * 0.725,
    )
    pag.click()


def action_text(
    general_fields, img_path, text_loc_word, harcoded_screen_percentages, search_words = []):
    region = general_fields["region"]
    left, top, width, height = general_fields["left"], general_fields["top"], general_fields["width"], general_fields["height"]

    # in case friend popup comes up
    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path=img_path,
    )

    if search_words == []:
        bbox = find_text_location(img_path, text_loc_word)
        if bbox:
            x, y, width, height = bbox
            log(
                f"Bounding box for '{text_loc_word}': x={x}, y={y}, width={width}, height={height}"
            )
            pag.moveTo(region[0] + x, region[1] + y)
        else:
            pag.moveTo(
                (region[0] + region[2]) * harcoded_screen_percentages[0],
                (region[1] + region[3]) * harcoded_screen_percentages[1],
            )
        pag.click()
        time.sleep(GENERAL_LONG_SLEEP)

        return

    search_word_results = [check_text_in_image(img_path, search_word) for search_word in search_words]

    if True in search_word_results:
        bbox = find_text_location(img_path, text_loc_word)
        if bbox:
            x, y, width, height = bbox
            log(
                f"Bounding box for '{text_loc_word}': x={x}, y={y}, width={width}, height={height}"
            )
            pag.moveTo(region[0] + x, region[1] + y)
        else:
            pag.moveTo((region[0] + region[2]) * harcoded_screen_percentages[0], (region[1] + region[3]) * harcoded_screen_percentages[1])
        pag.click()
        time.sleep(GENERAL_LONG_SLEEP)


def wait_for_screen(general_fields, loc_img_path, ss_img_path, search_text):
    region = general_fields["region"]
    left, top, width, height = (
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    found = False
    while not found:
        try:
            loc_battle_menu = pag.locateCenterOnScreen(
                loc_img_path, confidence=0.8
            )
            found = True
        except pag.ImageNotFoundException:
            capture_screenshot(
                region={"top": top, "left": left, "width": width, "height": height},
                output_path=ss_img_path,
            )
            found = check_text_in_image(
                ss_img_path, search_text
            )
        time.sleep(1)


def main():
    # launch and focus the iphone mirroring app
    launch_iphone_mirroring()
    focus_iphone_mirroring_window()

    region = get_iphone_mirroring_region()
    left, top, width, height = region
    general_fields = {"region": region, "left": left, "top": top, "width": width, "height": height}

    # # click on search button
    # pag.moveTo((region[0] + region[2]) // 2, (region[1] + region[3]) * 0.85)
    # pag.click()

    # # open fgo
    # pag.write("fate/go", interval=0.05)
    # pag.press("enter")
    # log("fate/go entered into search bar.", "debug")

    # region = get_iphone_mirroring_region()
    # left, top, width, height = region
    # general_fields = {"region": region, "left": left, "top": top, "width": width, "height": height}

    # ### ALL OF THIS SHOULD BE WHILE WAITING FOR FIRST LOADING SCREEN AND THEN SECOND LOADING SCREEN
    # # in case of data update
    # #TODO: click on begin data update

    # # in case of video playback intro
    # try:
    #     loc_skip_video = pag.locateCenterOnScreen("img/screenshots/skip_video_playback_intro.png", confidence=0.8)
    #     pag.moveTo(loc_skip_video.x // 2, loc_skip_video.y // 2)
    #     pag.click()
    # except pag.ImageNotFoundException:
    #     pass
    # ###

    # # click for first loading screen
    # found = False
    # while not found:
    #     capture_screenshot(
    #         region={"top": top, "left": left, "width": width, "height": height},
    #         output_path="img/screenshots/first_tap_on_open.png",
    #     )
    #     found = check_text_in_image(
    #         "img/screenshots/first_tap_on_open.png", "Please Tap the Screen"
    #     )
    #     time.sleep(1)
    # pag.moveTo((region[0] + region[2]) // 2, (region[1] + region[3]) // 2)
    # pag.click()

    # # click for second loading screen
    # time.sleep(GENERAL_LONG_SLEEP)
    # pag.click()
    # time.sleep(GENERAL_LONG_SLEEP)

    # # in case friend popup comes up
    # action_text(general_fields, "img/screenshots/potential_friend_popup.png", "Close", [0.3, 0.85], ["Friend Points", "Most used Servant"])

    # # in case news shows up
    # capture_screenshot(
    #     region={"top": top, "left": left, "width": width, "height": height},
    #     output_path="img/screenshots/potential_news.png",
    # )
    # search_words = ["News", "Maintenance", "Issues", "Facebook", "X (Twitter)"]
    # search_words_results = [check_text_in_image("img/screenshots/potential_news.png", search_word) for search_word in search_words]
    # if True in search_words_results:
    #     pag.moveTo((region[0] + region[2]) * 0.885, (region[1] + region[3]) * 0.24)
    #     pag.click()
    #     time.sleep(GENERAL_LONG_SLEEP)

    # # in case of any close buttons
    # capture_screenshot(
    #     region={"top": top, "left": left, "width": width, "height": height},
    #     output_path="img/screenshots/potential_close_btns.png",
    # )
    # loc_close_happened = False

    # try:
    #     loc_close = pag.locateCenterOnScreen("img/screenshots/close_btn.png", confidence=0.8)
    #     loc_close_exists = True
    # except pag.ImageNotFoundException:
    #     loc_close_exists = False

    # while loc_close_exists or check_text_in_image("img/screenshots/potential_close_btns.png", "Close"):
    #     loc_close_happened = True
    #     if loc_close_exists:
    #         pag.moveTo(loc_close.x, loc_close.y)
    #         pag.click()
    #     else:
    #         bbox = find_text_location(
    #             "img/screenshots/potential_close_btns.png", "Close"
    #         )
    #         if bbox:
    #             x, y, width, height = bbox
    #             log(
    #                 f"Bounding box for 'Close': x={x}, y={y}, width={width}, height={height}"
    #             )
    #             pag.moveTo(region[0] + x, region[1] + y)
    #         else:
    #             pag.moveTo((region[0] + region[2]) * 0.5, (region[1] + region[3]) * 0.835)
    #         pag.click()

    #     try:
    #         loc_close = pag.locateCenterOnScreen("img/screenshots/close_btn.png", confidence=0.8)
    #         loc_close_exists = True
    #     except pag.ImageNotFoundException:
    #         loc_close_exists = False

    # if loc_close_happened:
    #     time.sleep(GENERAL_LONG_SLEEP)

    # # drag scroll bar to top of screen
    # pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.35)
    # pag.click()
    # pag.dragTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.3, button="left")

    # # open Chaldea Gate menu
    # try:
    #     loc_chaldea_gate = pag.locateCenterOnScreen("img/screenshots/chaldea_gate.png", confidence=0.8)
    #     pag.moveTo(loc_chaldea_gate.x // 2, loc_chaldea_gate.y // 2)
    #     pag.click()
    # except pag.ImageNotFoundException:
    #     capture_screenshot(
    #         region={"top": top, "left": left, "width": width, "height": height},
    #         output_path="img/screenshots/fgo_in_game_homescreen.png",
    #     )
    #     bbox = find_text_location(
    #         "img/screenshots/fgo_in_game_homescreen.png", "Chaldea Gate"
    #     )
    #     if bbox:
    #         x, y, width, height = bbox
    #         log(
    #             f"Bounding box for 'Chaldea Gate': x={x}, y={y}, width={width}, height={height}"
    #         )
    #         pag.moveTo(region[0] + x, region[1] + y)
    #     else:
    #         pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.61) # NOTE: won't work if event - change 0.61 to something higher
    #     pag.click()

    # # open Daily Quests menu
    # capture_screenshot(
    #     region={"top": top, "left": left, "width": width, "height": height},
    #     output_path="img/screenshots/chaldea_gate_menu.png",
    # )
    # bbox = find_text_location("img/screenshots/chaldea_gate_menu.png", "Daily Quests")
    # if bbox:
    #     x, y, width, height = bbox
    #     log(
    #         f"Bounding box for 'Daily Quests': x={x}, y={y}, width={width}, height={height}"
    #     )
    #     pag.moveTo(region[0] + x, region[1] + y)
    # else:
    #     pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.4)
    # pag.click()

    # # drag scroll bar to top of screen
    # pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.35)
    # pag.click()
    # pag.dragTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.3, button="left")

    # # scroll to find Extreme QP quest
    # curr_y = (region[1] + region[3]) * 0.3
    # capture_screenshot(
    #     region={"top": top, "left": left, "width": width, "height": height},
    #     output_path="img/screenshots/daily_quests_menu.png",
    # )
    # bbox = find_text_location(
    #     "img/screenshots/daily_quests_menu.png", "Enter the Treasure Vault - Extreme"
    # )
    # if bbox:
    #     x, y, width, height = bbox
    #     log(
    #         f"Bounding box for 'Enter the Treasure Valut - Extreme': x={x}, y={y}, width={width}, height={height}"
    #     )
    #     pag.moveTo(region[0] + x, region[1] + y)
    # else:
    #     while not bbox:
    #         if curr_y >= ((region[1] + region[3]) * 0.835):
    #             break

    #         curr_y += (region[1] + region[3]) * 0.05
    #         pag.dragTo((region[0] + region[2]) * 0.925, curr_y, button="left")

    #         capture_screenshot(
    #             region={"top": top, "left": left, "width": width, "height": height},
    #             output_path="img/screenshots/daily_quests_menu.png",
    #         )
    #         bbox = find_text_location(
    #             "img/screenshots/daily_quests_menu.png", "Enter the Treasure Vault - Extreme"
    #         )

    #     if bbox:
    #         x, y, width, height = bbox
    #         log(
    #             f"Bounding box for 'Enter the Treasure Vault - Extreme': x={x}, y={y}, width={width}, height={height}"
    #         )
    #         pag.moveTo(region[0] + x, region[1] + y)
    #     else:
    #         pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.835)
    #         pag.click()

    #         # click on QP Extreme quest
    #         pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.4)
    #         pag.click()

    # time.sleep(GENERAL_LONG_SLEEP)

    # # switch to caster class
    # loc = pag.locateCenterOnScreen("img/screenshots/friend_support_caster_class.png", confidence=0.8)
    # pag.moveTo(loc.x // 2, loc.y // 2)
    # pag.click()

    # # make sure at top of list
    # pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.4)
    # pag.click()

    # # find end of scrollbar if need to scroll
    # loc = pag.locateOnScreen("img/screenshots/friend_support_scrollbar.png", confidence=0.8)
    # curr_y = (loc.top + loc.height) // 2
    # pag.moveTo((loc.left + (loc.width / 2)) // 2, curr_y)

    # found = False
    # while not found:
    #     try:
    #         # select castoria
    #         loc_support = pag.locateCenterOnScreen("img/screenshots/friend_support_altria_caster.png", confidence=0.8)
    #         pag.moveTo(loc_support.x // 2, loc_support.y // 2)
    #         pag.click()
    #         found = True
    #     except pag.ImageNotFoundException:
    #         # scroll to next supports
    #         curr_y += loc.height // 4
    #         pag.dragTo((region[0] + region[2]) * 0.925, curr_y, button="left", duration=0.5)

    # # switch to party VIII - QP farming party
    # switch_party(region, 8)

    # # go back to support servant screen and go through process again - required to click start quest
    # try:
    #     loc_return = pag.locateCenterOnScreen("img/screenshots/party_screen_return_btn.png", confidence=0.8)
    #     pag.moveTo(loc_return.x // 2, loc_return.y // 2)
    #     pag.click()
    # except pag.ImageNotFoundException:
    #     pag.moveTo((region[0] + region[2]) * 0.125, (region[1] + region[3]) * 0.25)
    #     pag.click()

    # # find end of scrollbar if need to scroll
    # loc = pag.locateOnScreen(
    #     "img/screenshots/friend_support_scrollbar.png", confidence=0.8
    # )
    # curr_y = (loc.top + loc.height) // 2
    # pag.moveTo((loc.left + (loc.width / 2)) // 2, curr_y)

    # found = False
    # while not found:
    #     try:
    #         # select castoria
    #         loc_support = pag.locateCenterOnScreen(
    #             "img/screenshots/friend_support_altria_caster.png", confidence=0.8
    #         )
    #         pag.moveTo(loc_support.x // 2, loc_support.y // 2)
    #         pag.click()
    #         found = True
    #     except pag.ImageNotFoundException:
    #         # scroll to next supports
    #         curr_y += loc.height // 4
    #         pag.dragTo(
    #             (region[0] + region[2]) * 0.925, curr_y, button="left", duration=0.5
    #         )

    # # start quest
    # try:
    #     loc_start_quest = pag.locateCenterOnScreen("img/screenshots/start_quest.png", confidence=0.8)
    #     pag.moveTo(loc_start_quest.x // 2, loc_start_quest.y // 2)
    #     pag.click()
    # except pag.ImageNotFoundException:
    #     action_text(general_fields, "img/screenshots/start_quest.png", "Start Quest", [0.88, 0.9])

    # # Turn 1
    # # wait for battle screen to load
    # wait_for_screen(general_fields, "img/screenshots/battle_screen_menu_btn.png", "img/screenshots/battle_screen_menu_btn_found.png", "Battle Menu")

    # # NOTE: SKILL CLICKS FOR EXTREME QP W/ 2x CASTORIA + DA VINCI (RIDER) (Da Vinci (Rider) is in slot 2)
    # skill_click(general_fields, 1, 1)
    # skill_click(general_fields, 1, 2, 2)
    # skill_click(general_fields, 1, 3, 2)
    # skill_click(general_fields, 2, 1)
    # skill_click(general_fields, 3, 1)
    # skill_click(general_fields, 3, 2, 2)
    # skill_click(general_fields, 3, 3, 2)
    # master_skill_click(general_fields, 3, 2)

    # # click on attack, then NP skill click, then face cards click (random for now)
    # # NOTE: for face card selecting frontend (when being made), maybe give users a list such that they can set the priority for turn order (obviously including NP), but if none selected, then just randomize the face card selection (but not NP)

    # # click on attack
    # pag.moveTo((region[0] + region[2]) * 0.845, (region[1] + region[3]) * 0.865)
    # pag.click()

    # np_card_click(region, 2)

    # old_random = 0
    # for i in range(2):
    #     new_random = random.randint(1, 5)

    #     while new_random == old_random:
    #         new_random = random.randint(1, 5)

    #     face_card_click(region, new_random)
    #     old_random = new_random

    # # Turn 2
    # wait_for_screen(general_fields, "img/screenshots/battle_screen_menu_btn.png", "img/screenshots/battle_screen_menu_btn_found.png", "Battle Menu")

    # pag.moveTo((region[0] + region[2]) * 0.845, (region[1] + region[3]) * 0.865)
    # pag.click()

    # np_card_click(region, 2)

    # old_random = 0
    # for i in range(2):
    #     new_random = random.randint(1, 5)

    #     while new_random == old_random:
    #         new_random = random.randint(1, 5)

    #     face_card_click(region, new_random)
    #     old_random = new_random

    # # Turn 3
    # wait_for_screen(general_fields, "img/screenshots/battle_screen_menu_btn.png", "img/screenshots/battle_screen_menu_btn_found.png", "Battle Menu")

    # skill_click(general_fields, 2, 2)
    # skill_click(general_fields, 2, 3)
    # master_skill_click(general_fields, 1, 2)

    # pag.moveTo((region[0] + region[2]) * 0.845, (region[1] + region[3]) * 0.865)
    # pag.click()

    # np_order = [2, 1, 3]
    # for np in np_order:
    #     np_card_click(region, np)

    # # wait for servant bond screen
    # wait_for_screen(general_fields, "img/screenshots/servant_bond_after_battle.png", "img/screenshots/servant_bond_screen_found.png", "Servant Bond")
    # pag.moveTo((region[0] + region[2]) * 0.5, (region[1] + region[3]) * 0.5)
    # pag.click()

    # # wait for master exp and mystic code exp screen
    # wait_for_screen(general_fields, "img/screenshots/double_triangle_master_mystic_exp.png", "img/screenshots/master_mystic_exp_screen_found.png", "Master EXP")
    # pag.moveTo((region[0] + region[2]) * 0.5, (region[1] + region[3]) * 0.5)
    # pag.click()

    # # next after items dropped received
    # wait_for_screen(
    #     general_fields,
    #     "img/screenshots/next_items_dropped_btn.png",
    #     "img/screenshots/items_dropped_next_btn_found.png",
    #     "QP Gained",
    # )
    # try:
    #     loc_start_quest = pag.locateCenterOnScreen("img/screenshots/next_items_dropped_btn.png", confidence=0.8)
    #     pag.moveTo(loc_start_quest.x // 2, loc_start_quest.y // 2)
    #     pag.click()
    # except pag.ImageNotFoundException:
    #     action_text(general_fields, "img/screenshots/next_items_dropped_btn.png", "Next", [0.8, 0.9])


if __name__ == "__main__":
    main()


### GOOD CODES TO HAVE:

# capture_screenshot(
#     region={"top": top, "left": left, "width": width, "height": height},
#     output_path="img/screenshots/ss.png",
# )
