import pyautogui
import time
import subprocess
# import pygetwindow as gw
from loguru import logger
import os

# msg_type: one of ["success", "error", "trace", "info", "warning", "critical", "debug"]
def log(msg, msg_type="success"):
    try:
        getattr(logger, msg_type)(msg)
    except Exception as e:
        logger.error(e)

# launch iphone mirroring app
def launch_iphone_mirroring():
    try:
        script = '''
        tell application "iPhone Mirroring"
            activate
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        log("iphone mirroring app launched.", "info")
        time.sleep(3)  # give time for the app to come into focus
    except subprocess.CalledProcessError as e:
        log(f"failed to launch iphone mirroring app: {e}", "error")

# focus on the iphone mirroring window using applescript
def focus_iphone_mirroring_window():
    try:
        script = '''
        tell application "System Events"
            set frontmost of process "iPhone Mirroring" to true
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        log("iphone mirroring window focused.", "info")
        time.sleep(2)  # give time for the system to bring the window into focus
    except subprocess.CalledProcessError as e:
        log(f"error focusing iphone mirroring window: {e}", "error")

# click on the fate/go game icon
def open_fate_go():
    log("attempting to open fate/go.", "info")
    # assuming the game icon is visible on the iphone screen through mirroring
    game_icon_path = 'img/fgo_game_icon.png'  # ensure the screenshot of the fgo game icon is here
    if not os.path.exists(game_icon_path):
        log(f"game icon image '{game_icon_path}' not found.", "error")
        return False

    try:
        # locate the fate/go game icon on the mirrored screen
        icon_location = pyautogui.locateCenterOnScreen(game_icon_path, confidence=0.7)
        if icon_location:
            pyautogui.click(icon_location)  # click on the game icon
            log("fate/go game icon found and clicked.", "info")
            time.sleep(2)  # wait for the game to launch
            return True
        else:
            log("fate/go game icon not found on the mirrored screen.", "warning")
            return False
    except Exception as e:
        log(f"error clicking fate/go game icon: {e}", "error")
        return False

# click the search button and search for fate/go
def search_and_open_fate_go():
    log("searching for fate/go using the search function.", "info")
    search_button_path = 'img/search_button.png'  # make sure this screenshot is provided
    if not os.path.exists(search_button_path):
        log(f"search button image '{search_button_path}' not found.", "error")
        return False

    try:
        # locate and click the search button
        search_button_location = pyautogui.locateCenterOnScreen(search_button_path, confidence=0.8)
        if search_button_location:
            pyautogui.click(search_button_location)  # click on the search button
            log("search button found and clicked.", "info")
            time.sleep(1)  # give time for the search field to appear

            # type "fate/go"
            pyautogui.write('fate/go', interval=0.1)
            pyautogui.press('enter')
            time.sleep(2)  # wait for search results

            # now locate and click on the fate/go result
            game_icon_path = 'img/fgo_game_icon.png'  # reuse the fgo game icon image
            icon_location = pyautogui.locateCenterOnScreen(game_icon_path, confidence=0.7)
            if icon_location:
                pyautogui.click(icon_location)  # click on the game icon in the search results
                log("fate/go game icon found in search results and clicked.", "info")
                time.sleep(2)  # wait for the game to launch
                return True
            else:
                log("fate/go game icon not found in search results.", "warning")
                return False
        else:
            log("search button not found.", "warning")
            return False
    except Exception as e:
        log(f"error during search and open for fate/go: {e}", "error")
        return False

# main function to run the automation
def main():
    # step 1: launch and focus the iphone mirroring app
    launch_iphone_mirroring()
    focus_iphone_mirroring_window()

    # step 2: open the fate/go game by clicking the icon
    if open_fate_go():
        log("fate/go successfully opened.", "info")
    else:
        log("attempting to search for fate/go.", "info")
        if search_and_open_fate_go():
            log("fate/go successfully opened via search.", "info")
        else:
            log("failed to open fate/go.", "error")

if __name__ == "__main__":
    main()
