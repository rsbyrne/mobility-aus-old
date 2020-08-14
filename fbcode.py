import os
import shutil
import time
import random
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common import exceptions

MAXWAIT = 10.

def format_string(string):
    return string.replace(' ', '-')
def check_string(string):
    return string.replace(' ', '-').replace('-', '').isnumeric()

def random_sleep(factor = 1.):
    sleepTime = (random.random() + 1.) * factor
    time.sleep(sleepTime)
    return sleepTime

def wait_check(
        condition,
        message = None,
        repeatAction = None,
        repeatException = True,
        waitInterval = 1.,
        maxWait = None
        ):
    waited = 0.
    while not condition():
        if not message is None:
            print(message)
        waitTime = random_sleep(waitInterval)
        waited += waitTime
        if not maxWait is None:
            if waited > maxWait:
                raise Exception("Wait time exceeded!")
        if not repeatAction is None:
            if repeatException:
                repeatAction()
            else:
                try:
                    repeatAction()
                except:
                    pass

def _file_check(fp):
    if os.path.isfile(fp):
        return os.stat(fp).st_size
    return False

def download_all(
        linksDict,
        downloadDir,
        outDir,
        outExt,
        keys = None,
        notkeys = set(),
        maxWait = MAXWAIT
        ):
    print("Downloading all...")
    if keys is None:
        keys = linksDict.keys()
    keys = sorted([key for key in keys if key not in notkeys])
    for key in keys:
        newFilename = key + outExt
        if newFilename in os.listdir(outDir):
            print("File already exists - skipping.")
        else:
            random_sleep(1.)
            link = linksDict[key]
            link.click()
            wait_check(lambda: len(os.listdir(downloadDir)), maxWait = maxWait)
            checkFilenames = [
                fp for fp in os.listdir(downloadDir) \
                    if fp.endswith(outExt)
                ]
            assert len(checkFilenames) == 1
            oldFilename = checkFilenames[0]
            oldFilepath = os.path.join(downloadDir, oldFilename)
            wait_check(lambda: _file_check(oldFilepath), maxWait = maxWait)
            newFilepath = os.path.join(outDir, newFilename)
            random_sleep(1.)
            shutil.copyfile(oldFilepath, newFilepath)
            random_sleep(1.)
            wait_check(lambda: _file_check(newFilepath), maxWait = maxWait)
            for filename in os.listdir(downloadDir):
                filepath = os.path.join(downloadDir, filename)
                os.remove(filepath)
                wait_check(
                    lambda: not os.path.isfile(filepath),
                    maxWait = maxWait
                    )
            print("Downloaded:", newFilename)
    print("Downloaded all.")

class Driver:
    def __init__(self, options, profile, logDir = '.'):
        self.options, self.profile, self.logDir = options, profile, logDir
    def __enter__(self):
        self.driver = webdriver.Firefox(
            options = self.options,
            firefox_profile = self.profile
            )
        return self.driver
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_value:
            print("An error has occurred. Saving screenshot to target directory and exiting.")
            try:
                errorFilePath = os.path.join(self.logDir, str(int(time.time())) + '.png')
                self.driver.save_screenshot(errorFilePath)
            except:
                print("Another error occurred: could not save screenshot.")
        self.driver.quit()
        if os.path.isfile('geckodriver.log'):
            os.remove('geckodriver.log')
        if exc_type is not None:
            return False
        else:
            return True

class TempDir:
    def __init__(self, path, maxWait = None):
        self.path = path
        self.maxWait = maxWait
    def __enter__(self):
        os.makedirs(self.path, exist_ok = False)
        wait_check(lambda: os.path.isdir(self.path), maxWait = self.maxWait)
    def __exit__(self, exc_type, exc_value, exc_traceback):
        shutil.rmtree(self.path, ignore_errors = True)
        wait_check(lambda: not os.path.isdir(self.path), maxWait = self.maxWait)
        if exc_type is not None:
            return False
        else:
            return True

def pull_datas(
        dataURL,
        loginName,
        loginPass,
        outDir,
        dataMime,
        outExt,
        maxWait = MAXWAIT
        ):

    parsed = urlparse(dataURL)
    loginURL = '://'.join(parsed[:2])
#     loginURL = 'https://en-gb.facebook.com/'

    outDir = os.path.abspath(outDir)
    if not os.path.isdir(outDir):
        os.makedirs(outDir, exist_ok = True)

    downloadDir = os.path.join(outDir, '_temp')

    with TempDir(downloadDir, maxWait = maxWait):

        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", downloadDir)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", dataMime)
        options = Options()
        options.add_argument("--headless")

        with Driver(options, profile, outDir) as driver:

            print("Navigating to login page...")
            try:
                driver.get(loginURL)
            except exceptions.WebDriverException:
                raise ValueError("No login page found!")
            print("Navigated to login page.")

            print("Logging in...")

            random_sleep(1.)

            username = driver.find_element_by_id("email")
            password = driver.find_element_by_id("pass")
            try:
                submit = driver.find_element_by_id("loginbutton")
                normalLogin = True
            except exceptions.NoSuchElementException:
                submit = driver.find_element_by_name('login')
                normalLogin = False
            if normalLogin:
                username.send_keys(loginName)
                password.send_keys(loginPass)
                submit.click()
                try:
                    loginForm = driver.find_element_by_id("login_form")
                    raise ValueError("Bad login credentials!")
                except exceptions.NoSuchElementException:
                    pass
            else:
                submit = driver.find_element_by_name('login')
                username.send_keys(loginName)
                password.send_keys(loginPass)
                submit.click()
                print("Made it this far")
                errorText = "Sorry, something went wrong."
                if driver.find_element_by_id("facebook").text.startswith(errorText):
                    raise ValueError("Bad login credentials!")

            print("Logged in.")

            random_sleep(1.)

            print("Navigating to data page...")
            try:
                driver.get(dataURL)
            except exceptions.WebDriverException:
                raise ValueError("Bad data URL!")
            print("Navigated to data page.")

            random_sleep(1.)

            print("Finding data...")
            linksDict = {
                format_string(elem.text): elem \
                    for elem in driver.find_elements_by_xpath("//a[@href]") \
                        if check_string(elem.text)
                }
            if len(linksDict) > 0:
                print("Data found.")
                download_all(
                    linksDict,
                    downloadDir,
                    outDir,
                    outExt,
                    maxWait = maxWait
                    )
            else:
                print("No data found at that URL. Aborting.")
