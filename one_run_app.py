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


SCRIPT_TIMEOUT = 10
SCRIPT_RETRY_DELAY = 2
SCRIPT_MAX_RETRIES = 3
GENERAL_LONG_SLEEP = 10
# pag.PAUSE = 1
img_prefix = "img/screenshots/"


def capture_screenshot(region=None, output_path="screenshot.png"):
    with mss.mss() as sct:
        if region:  # capture a specific region or the whole screen
            screenshot = sct.grab(region)
        else:  # full screen
            screenshot = sct.grab(sct.monitors[0])

        # save to file
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)


def delete_file(file_path):
    try:
        os.remove(file_path)
    except Exception as e:
        log(f"failed to delete file: {file_path} - {e}", "error")


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


def run_applescript(script, timeout=SCRIPT_TIMEOUT):
    try:
        subprocess.run(["osascript", "-e", script], timeout=timeout, check=True)
        return True
    except subprocess.TimeoutExpired:
        log("AppleScript execution timed out.", "error")
        return False
    except subprocess.CalledProcessError as e:
        log(f"AppleScript execution failed: {e}", "error")
        return False


def call_applescript(
    script,
    success_msg,
    error_msg,
    timeout=SCRIPT_TIMEOUT,
    retries=SCRIPT_MAX_RETRIES,
    delay=SCRIPT_RETRY_DELAY,
):
    for retry in range(retries):
        success = run_applescript(script, timeout)
        if success:
            log(success_msg, "success")
            return
        else:
            log(f"attempt {retry + 1}: {error_msg}", "warning")
            time.sleep(delay)

    if not success:
        log("failed final attempt.", "error")


# launch iphone mirroring app
def launch_iphone_mirroring():
    script = 'tell application "iPhone Mirroring" to activate'
    call_applescript(
        script,
        "iphone mirroring app launched.",
        "failed to launch iphone mirroring app.",
    )


# focus on the iphone mirroring window using applescript
def focus_iphone_mirroring_window():
    script = """
    tell application "System Events"
        tell process "iPhone Mirroring"
            set frontmost to true
            set visible to true
        end tell
    end tell
    """
    call_applescript(
        script,
        "iphone mirroring window focused and visible.",
        "failed to focus iphone mirroring window.",
    )


def move_iphone_mirroring_window():
    script = """
    tell application "System Events"
        set position of first window of application process "iPhone Mirroring" to {0, 0}
    end tell
    """
    call_applescript(
        script,
        "iphone mirroring window moved to top-left corner.",
        "failed to move iphone mirroring window.",
    )


def open_iphone_spotlight():
    script = """
    tell application "System Events"
        keystroke "3" using {command down}
    end tell
    """
    call_applescript(
        script, "opened spotlight search.", "Failed to open spotlight search."
    )


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


def general_skill_speedup(region):
    pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.55)
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

    target_selectable = False
    try:
        loc = pag.locateCenterOnScreen(
            "img/screenshots/skill_select_servant_close_btn.png", confidence=0.8
        )
        target_selectable = True
    except:
        capture_screenshot(
            region={"top": top, "left": left, "width": width, "height": height},
            output_path="img/screenshots/skill_target_selectable_screen.png",
        )
        search_word_result = check_text_in_image(
            "img/screenshots/skill_target_selectable_screen.png", "Select Target"
        )
        delete_file("img/screenshots/skill_target_selectable_screen.png")
        if search_word_result:
            target_selectable = True

    if target_selectable:
        pag.moveTo(
            (region[0] + region[2]) * (0.3 + (0.2 * (servant_select_num - 1))),
            (region[1] + region[3]) * 0.625,
        )
        pag.click()

    general_skill_speedup(region)
    wait_for_battle_menu(general_fields)


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

    target_selectable = False
    try:
        loc = pag.locateCenterOnScreen(
            "img/screenshots/skill_select_servant_close_btn.png", confidence=0.8
        )
        target_selectable = True
    except:
        capture_screenshot(
            region={"top": top, "left": left, "width": width, "height": height},
            output_path="img/screenshots/skill_target_selectable_screen.png",
        )
        search_word_result = check_text_in_image(
            "img/screenshots/skill_target_selectable_screen.png", "Select Target"
        )
        delete_file("img/screenshots/skill_target_selectable_screen.png")
        if search_word_result:
            target_selectable = True

    if target_selectable:
        pag.moveTo(
            (region[0] + region[2]) * (0.3 + (0.2 * (servant_select_num - 1))),
            (region[1] + region[3]) * 0.625,
        )
        pag.click()

    general_skill_speedup(region)
    wait_for_battle_menu(general_fields)


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
    general_fields,
    img_path,
    text_loc_word,
    harcoded_screen_percentages,
    search_words=[],
):
    region = general_fields["region"]
    left, top, width, height = (
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path=img_path,
    )

    if search_words == []:
        bbox = find_text_location(img_path, text_loc_word)
        delete_file(img_path)
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

    search_word_results = [
        check_text_in_image(img_path, search_word) for search_word in search_words
    ]

    if True in search_word_results:
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
            loc_battle_menu = pag.locateCenterOnScreen(loc_img_path, confidence=0.8)
            found = True

            log(f"found screen: {search_text}", "success")
            time.sleep(1)
            return
        except pag.ImageNotFoundException:
            capture_screenshot(
                region={"top": top, "left": left, "width": width, "height": height},
                output_path=ss_img_path,
            )
            found = check_text_in_image(ss_img_path, search_text)
            delete_file(ss_img_path)

            if found:
                log(f"found text: {search_text}", "success")
                time.sleep(1)
                return
        time.sleep(0.25)


def launch_fgo():
    # launch and focus the iphone mirroring app
    launch_iphone_mirroring()
    focus_iphone_mirroring_window()
    move_iphone_mirroring_window()
    focus_iphone_mirroring_window()

    region = get_iphone_mirroring_region()
    left, top, width, height = region
    general_fields = {
        "region": region,
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }

    # # get phone's home screen (while waiting for iphone mirroring app to load phone screen)
    # capture_screenshot(
    #     region={"top": top + (height * 0.8), "left": left + (width * 0.1), "width": (width * ((1 - 0.1) - 0.1)), "height": (height * 0.05)},
    #     output_path="img/screenshots/ss.png",
    # )

    # wait for iphone's home screen to load
    found_home_screen = False
    while not found_home_screen:
        try:
            loc_battle_menu = pag.locateCenterOnScreen(
                "img/screenshots/phone_home_screen.png", confidence=0.8
            )
            found_home_screen = True
            log(f"found home screen", "success")
        except pag.ImageNotFoundException:
            log("did not find home screen", "warning")

    # open fgo
    open_iphone_spotlight()
    wait_for_screen(
        general_fields,
        "img/screenshots/spotlight_search_icon.png",
        "img/screenshots/spotlight_search_icon_found.png",
        "Search",
    )
    pag.write("fate/go", interval=0.05)
    pag.press("enter")
    log("fate/go opened.", "success")
    time.sleep(2)

    region = get_iphone_mirroring_region()
    left, top, width, height = region
    general_fields = {
        "region": region,
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }

    return general_fields


def get_to_fgo_home_screen(general_fields):
    region, left, top, width, height = (
        general_fields["region"],
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    # TODO: consider data update screen

    # check for first loading screen
    first_loading_screen_found = False
    while not first_loading_screen_found:
        capture_screenshot(
            region={"top": top, "left": left, "width": width, "height": height},
            output_path="img/screenshots/first_tap_on_open.png",
        )
        first_loading_screen_found = check_text_in_image(
            "img/screenshots/first_tap_on_open.png", "Please Tap the Screen"
        )
        delete_file("img/screenshots/first_tap_on_open.png")

        if not first_loading_screen_found:
            # check for cache clear screen
            try:
                loc_not_clear_cache = pag.locateCenterOnScreen(
                    "img/screenshots/clear_cache_prompt.png", confidence=0.8
                )
                log("found clear cache prompt", "info")

                # don't clear cache
                loc_not_clear_cache = pag.locateCenterOnScreen(
                    "img/screenshots/no_clear_cache_btn.png", confidence=0.8
                )
                pag.moveTo(loc_not_clear_cache.x // 2, loc_not_clear_cache.y // 2)
                pag.click()

                log("clicked no for clearing cache", "info")
            except pag.ImageNotFoundException:
                pass

            # check for video playback intro
            try:
                loc_skip_video = pag.locateCenterOnScreen(
                    "img/screenshots/skip_video_playback_intro.png", confidence=0.8
                )
                log("found skip video playback intro", "info")

                pag.moveTo(loc_skip_video.x // 2, loc_skip_video.y // 2)
                pag.click()

                log("clicked skip video playback intro", "info")
            except pag.ImageNotFoundException:
                pass

    # click for first loading screen
    pag.moveTo((region[0] + region[2]) // 2, (region[1] + region[3]) // 2)
    pag.click()
    log("clicked first loading screen", "info")

    # wait for second loading screen
    wait_for_screen(
        general_fields,
        "img/screenshots/criware_logo.png",
        "img/screenshots/second_loading_screen_found.png",
        "Data Transfer",
    )
    time.sleep(1)
    pag.click()
    log("clicked second loading screen", "info")


def friend_popup_handler(general_fields):
    action_text(
        general_fields,
        "img/screenshots/potential_friend_popup.png",
        "Close",
        [0.3, 0.85],
        ["Friend Points", "Most used Servant"],
    )


def news_popup_handler(general_fields):
    region, left, top, width, height = (
        general_fields["region"],
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/potential_news.png",
    )
    search_words = ["Maintenance", "Issues", "Facebook", "X (Twitter)"]
    search_words_results = [
        check_text_in_image("img/screenshots/potential_news.png", search_word)
        for search_word in search_words
    ]
    delete_file("img/screenshots/potential_news.png")
    if True in search_words_results:
        pag.moveTo((region[0] + region[2]) * 0.885, (region[1] + region[3]) * 0.24)
        pag.click()


def other_popups_handler(general_fields):
    region, left, top, width, height = (
        general_fields["region"],
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/potential_close_btns.png",
    )

    try:
        loc_close = pag.locateCenterOnScreen(
            "img/screenshots/close_btn.png", confidence=0.8
        )
        loc_close_exists = True
    except pag.ImageNotFoundException:
        loc_close_exists = False

    while loc_close_exists or check_text_in_image(
        "img/screenshots/potential_close_btns.png", "Close"
    ):
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
                pag.moveTo(
                    (region[0] + region[2]) * 0.5, (region[1] + region[3]) * 0.835
                )
            delete_file("img/screenshots/potential_close_btns.png")
            pag.click()

        try:
            loc_close = pag.locateCenterOnScreen(
                "img/screenshots/close_btn.png", confidence=0.8
            )
            loc_close_exists = True
        except pag.ImageNotFoundException:
            loc_close_exists = False


def handle_all_popups(general_fields):
    fgo_home_screen_found = False
    while not fgo_home_screen_found:
        try:
            loc_fgo_home_screen = pag.locateCenterOnScreen(
                "img/screenshots/news_btn.png", confidence=0.8
            )  # NOTE: might need to change this to be chaldea gate instead of back news btn
            fgo_home_screen_found = True
            log("found fgo home screen", "success")

        except pag.ImageNotFoundException:
            # in case friend popup comes up
            friend_popup_handler(general_fields)

            # in case news shows up
            news_popup_handler(general_fields)

            # in case of any close buttons
            other_popups_handler(general_fields)


# drag scroll bar to top of screen
def drag_scrollbar_to_top_quest_selection(region):
    pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.35)
    pag.click()
    pag.dragTo(
        (region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.3, button="left"
    )


def open_chaldea_gate_menu(general_fields):
    region = general_fields["region"]
    left, top, width, height = (
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    drag_scrollbar_to_top_quest_selection(region)
    wait_for_screen(
        general_fields,
        "img/screenshots/chaldea_gate_banner.png",
        "img/screenshots/fgo_in_game_homescreen.png",
        "Chaldea Gate",
    )

    # open Chaldea Gate menu
    try:
        loc_chaldea_gate = pag.locateCenterOnScreen(
            "img/screenshots/chaldea_gate_banner.png", confidence=0.8
        )
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
            pag.moveTo(
                (region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.61
            )  # NOTE: won't work if event - change 0.61 to something higher

        delete_file("img/screenshots/fgo_in_game_homescreen.png")
        pag.click()
        time.sleep(1)


def open_daily_quests_menu(general_fields):
    region = general_fields["region"]
    left, top, width, height = (
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    drag_scrollbar_to_top_quest_selection(region)
    wait_for_screen(
        general_fields,
        "img/screenshots/daily_quests_banner.png",
        "img/screenshots/chaldea_gate_menu.png",
        "Daily Quests",
    )

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

    delete_file("img/screenshots/chaldea_gate_menu.png")
    pag.click()
    time.sleep(1)


def open_extreme_qp_quest(general_fields):
    region = general_fields["region"]
    left, top, width, height = (
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    try:
        loc = pag.locateOnScreen(
            "img/screenshots/daily_quests_scrollbar.png", confidence=0.8
        )
        curr_y = (loc.top + loc.height) // 2
        pag.moveTo((loc.left + (loc.width / 2)) // 2, curr_y)
    except pag.ImageNotFoundException:
        curr_y = (region[1] + region[3]) // 2

    # move scrollbar to bottom of screen for extreme QP quest
    # pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.8375)
    # pag.click()

    found = False
    while not found:
        try:
            loc_extreme_qp_quest = pag.locateCenterOnScreen(
                "img/screenshots/enter_the_treasure_vault_extreme_banner.png",
                confidence=0.8,
            )
            pag.moveTo(loc_extreme_qp_quest.x // 2, loc_extreme_qp_quest.y // 2)
            pag.click()
            found = True

            log(f"found screen: extreme QP quest", "success")
            time.sleep(1)
            return
        except pag.ImageNotFoundException:
            capture_screenshot(
                region={"top": top, "left": left, "width": width, "height": height},
                output_path="img/screenshots/daily_quests_menu.png",
            )
            found = check_text_in_image(
                "img/screenshots/daily_quests_menu.png", "Vault - Extreme"
            )
            delete_file("img/screenshots/daily_quests_menu.png")

            if found:
                log(f"found text: {search_text}", "success")
                time.sleep(1)
            else:
                if curr_y < (region[1] + region[3]) * 0.875:
                    curr_y += loc.height // 4
                    pag.dragTo(
                        (region[0] + region[2]) * 0.925,
                        curr_y,
                        button="left",
                        duration=0.5,
                    )

                else:
                    pag.moveTo(
                        (region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.4
                    )
                    pag.click()
                    time.sleep(1)
                    return

        time.sleep(0.25)

    # open Extreme QP quest
    capture_screenshot(
        region={"top": top, "left": left, "width": width, "height": height},
        output_path="img/screenshots/daily_quests_menu.png",
    )
    bbox = find_text_location(
        "img/screenshots/daily_quests_menu.png",
        "Enter the Treasure Vault - Extreme",
    )
    if bbox:
        x, y, width, height = bbox
        log(
            f"Bounding box for 'Enter the Treasure Vault - Extreme': x={x}, y={y}, width={width}, height={height}"
        )
        pag.moveTo(region[0] + x, region[1] + y)
    else:
        # click on QP Extreme quest
        pag.moveTo((region[0] + region[2]) * 0.7, (region[1] + region[3]) * 0.4)
        pag.click()

    delete_file("img/screenshots/daily_quests_menu.png")
    time.sleep(1)


def choose_support_class(class_name="caster"):
    try:
        if class_name == "caster":
            loc = pag.locateCenterOnScreen(
                "img/screenshots/friend_support_caster_class.png", confidence=0.8
            )
        pag.moveTo(loc.x // 2, loc.y // 2)
        pag.click()

        log("selected caster class", "success")

    except pag.ImageNotFoundException:
        log(f"failed to select {class_name} class", "error")


# make sure at top of support list
def drag_scrollbar_to_top_support_selection(region):
    pag.moveTo((region[0] + region[2]) * 0.925, (region[1] + region[3]) * 0.4)
    pag.click()


def select_support_servant(region, support_img_path):
    # find end of scrollbar if need to scroll
    try:
        loc = pag.locateOnScreen(
            "img/screenshots/friend_support_scrollbar.png", confidence=0.8
        )
        curr_y = (loc.top + loc.height) // 2
        pag.moveTo((loc.left + (loc.width / 2)) // 2, curr_y)
    except pag.ImageNotFoundException:
        pass

    found = False
    while not found:
        try:
            # select castoria
            loc_support = pag.locateCenterOnScreen(support_img_path, confidence=0.8)
            pag.moveTo(loc_support.x // 2, loc_support.y // 2)
            pag.click()
            found = True
        except pag.ImageNotFoundException:
            # scroll to next supports
            curr_y += loc.height // 4
            pag.dragTo(
                (region[0] + region[2]) * 0.925, curr_y, button="left", duration=0.5
            )


# go back to support servant screen and go through process again - required to click start quest
def go_back_to_support_selection(region):
    try:
        loc_return = pag.locateCenterOnScreen(
            "img/screenshots/party_screen_return_btn.png", confidence=0.8
        )
        pag.moveTo(loc_return.x // 2, loc_return.y // 2)
        pag.click()
    except pag.ImageNotFoundException:
        pag.moveTo((region[0] + region[2]) * 0.125, (region[1] + region[3]) * 0.25)
        pag.click()


def start_quest(general_fields):
    try:
        loc_start_quest = pag.locateCenterOnScreen(
            "img/screenshots/start_quest.png", confidence=0.8
        )
        pag.moveTo(loc_start_quest.x // 2, loc_start_quest.y // 2)
        pag.click()
        pag.click()
    except pag.ImageNotFoundException:
        action_text(
            general_fields,
            "img/screenshots/start_quest_screen.png",
            "Start Quest",
            [0.88, 0.9],
        )


# wait for battle screen to load
def wait_for_battle_menu(general_fields, turn_num=2):
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
                "img/screenshots/battle_screen_menu_btn.png", confidence=0.8
            )
            found = True
            log(f"found battle menu", "success")
            return
        except pag.ImageNotFoundException:
            log(f"did not find battle menu", "warning")
            time.sleep(0.25)

    if turn_num == 1:
        time.sleep(4)
    else:
        time.sleep(1)


def open_attack_options(region):
    # click on attack
    pag.moveTo((region[0] + region[2]) * 0.845, (region[1] + region[3]) * 0.865)
    pag.click()
    time.sleep(1)


def choose_random_face_cards(region, number_of_cards=2):
    old_random = 0
    for i in range(2):
        new_random = random.randint(1, 5)

        while new_random == old_random:
            new_random = random.randint(1, 5)

        face_card_click(region, new_random)
        old_random = new_random


def main():
    # general_fields = launch_fgo()
    # get_to_fgo_home_screen(general_fields)
    # handle_all_popups(general_fields)

    ### START TESTING
    launch_iphone_mirroring()
    focus_iphone_mirroring_window()
    move_iphone_mirroring_window()
    focus_iphone_mirroring_window()

    region = get_iphone_mirroring_region()
    left, top, width, height = region
    general_fields = {
        "region": region,
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }
    ### END TESTING

    region, left, top, width, height = (
        general_fields["region"],
        general_fields["left"],
        general_fields["top"],
        general_fields["width"],
        general_fields["height"],
    )

    open_chaldea_gate_menu(general_fields)
    open_daily_quests_menu(general_fields)
    open_extreme_qp_quest(general_fields)

    wait_for_screen(
        general_fields,
        "img/screenshots/select_support_menu.png",
        "img/screenshots/select_support_menu_found.png",
        "Select Support",
    )

    # switch to caster class
    choose_support_class("caster")
    drag_scrollbar_to_top_support_selection(region)
    select_support_servant(region, "img/screenshots/friend_support_altria_caster.png")
    start_quest(general_fields)

    # switch to party VIII - QP farming party
    switch_party(region, 8)
    go_back_to_support_selection(region)

    wait_for_screen(
        general_fields,
        "img/screenshots/friend_support_scrollbar.png",
        "img/screenshots/friend_support_scrollbar_found.png",
        "Select Support",
    )
    select_support_servant(region, "img/screenshots/friend_support_altria_caster.png")

    # Turn 1 (for battle)
    wait_for_battle_menu(general_fields, 1)

    time.sleep(1)
    general_skill_speedup(region)

    # NOTE: SKILL CLICKS FOR EXTREME QP W/ 2x CASTORIA + DA VINCI (RIDER) (Da Vinci (Rider) is in slot 2)
    skill_click(general_fields, 1, 1)
    skill_click(general_fields, 1, 2, 2)
    skill_click(general_fields, 1, 3, 2)
    skill_click(general_fields, 2, 1)
    skill_click(general_fields, 3, 1)
    skill_click(general_fields, 3, 2, 2)
    skill_click(general_fields, 3, 3, 2)
    master_skill_click(general_fields, 3, 2)

    # click on attack, then NP skill click, then face cards click (random for now)
    # NOTE: for face card selecting frontend (when being made), maybe give users a list such that they can set the priority for turn order (obviously including NP), but if none selected, then just randomize the face card selection (but not NP)

    open_attack_options(region)
    np_card_click(region, 2)
    choose_random_face_cards(region, 2)

    time.sleep(1)
    general_skill_speedup(region)

    # Turn 2
    wait_for_battle_menu(general_fields, 2)

    open_attack_options(region)
    np_card_click(region, 2)
    choose_random_face_cards(region, 2)

    time.sleep(1)
    general_skill_speedup(region)

    # Turn 3
    wait_for_battle_menu(general_fields, 3)

    skill_click(general_fields, 2, 2)
    skill_click(general_fields, 2, 3)
    master_skill_click(general_fields, 1, 2)

    open_attack_options(region)

    np_order = [2, 1, 3]
    for np in np_order:
        np_card_click(region, np)

    time.sleep(1)
    general_skill_speedup(region)

    # wait for servant bond screen
    wait_for_screen(
        general_fields,
        "img/screenshots/servant_bond_after_battle.png",
        "img/screenshots/servant_bond_screen_found.png",
        "Servant Bond",
    )
    pag.moveTo((region[0] + region[2]) * 0.5, (region[1] + region[3]) * 0.5)
    pag.click()

    # wait for master exp and mystic code exp screen
    wait_for_screen(
        general_fields,
        "img/screenshots/double_triangle_master_mystic_exp.png",
        "img/screenshots/master_mystic_exp_screen_found.png",
        "Master EXP",
    )
    pag.moveTo((region[0] + region[2]) * 0.5, (region[1] + region[3]) * 0.5)
    pag.click()

    # next after items dropped received
    wait_for_screen(
        general_fields,
        "img/screenshots/next_items_dropped_btn.png",
        "img/screenshots/items_dropped_next_btn_found.png",
        "QP Gained",
    )
    try:
        loc_next_btn = pag.locateCenterOnScreen(
            "img/screenshots/next_items_dropped_btn.png", confidence=0.8
        )
        pag.moveTo(loc_next_btn.x // 2, loc_next_btn.y // 2)
        pag.click()
    except pag.ImageNotFoundException:
        action_text(
            general_fields,
            "img/screenshots/next_items_dropped_btn.png",
            "Next",
            [0.8, 0.9],
        )

    # NOTE: need to do text analysis to see how much AP and store - potentially in a variable and using apples?

    # repeat quest
    wait_for_screen(
        general_fields,
        "img/screenshots/repeat_quest_btn.png",
        "img/screenshots/repeat_quest_btn_found.png",
        "AP Required",
    )
    # NOTE: this would need to be altered to close depending on how many runs - also add apples selection feature
    try:
        loc_repeat_quest = pag.locateCenterOnScreen(
            "img/screenshots/repeat_quest_btn.png", confidence=0.8
        )
        pag.moveTo(loc_repeat_quest.x // 2, loc_repeat_quest.y // 2)
        pag.click()
    except pag.ImageNotFoundException:
        action_text(
            general_fields,
            "img/screenshots/repeat_quest_btn.png",
            "Repeat",
            [0.625, 0.82],
        )


if __name__ == "__main__":
    main()

    # launch_iphone_mirroring()
    # focus_iphone_mirroring_window()
    # move_iphone_mirroring_window()
    # focus_iphone_mirroring_window()

    # region = get_iphone_mirroring_region()
    # left, top, width, height = region
    # general_fields = {
    #     "region": region,
    #     "left": left,
    #     "top": top,
    #     "width": width,
    #     "height": height,
    # }

    # capture_screenshot(
    #     region={"top": top, "left": left, "width": width, "height": height},
    #     output_path="img/screenshots/ss.png",
    # )
