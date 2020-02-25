import os
# encoding=utf8
import sys

sys.path.insert(0, '%s/../' % os.path.dirname(__file__))
import re
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep, strptime
import datetime
import csv


DRIVER_CHROME = 0
DRIVER_SPYNNER = 1
DRIVER_NONE = 2
USER_ID = 'michealpearce@outlook.com'
PASSWORD = 'e8P5!DQ@b7uZ'


class IntuitSpider:
    CHROME_DRIVER_PATH = os.path.dirname(__file__) + '/chromedriver'
    HOME_URL = 'https://ito.intuit.com/app/protax/sign-in'
    CSV_HEADER = ['CLIENT NAME', 'RETURN NAME', 'TYPE', 'DATA REQUESTS', 'STATUS', 'ESIGNATURE STATUS', 'EFILE STATUS', 'ACTION']

    def __init__(self, *args, **kwargs):
        self.driver = None
        self.headless = True
        self.use_driver = kwargs.pop('use_driver', DRIVER_CHROME)

    def driver_startup(self):
        caps = DesiredCapabilities.CHROME
        caps['loggingPrefs'] = {'performance': 'ALL'}

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--num-raster-threads=8')
        chrome_options.add_argument('--no-proxy-server')
        chrome_options.add_argument('--enable-low-res-tiling')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument('--user_agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36')

        if self.headless:
            chrome_options.add_argument('--headless')

        # chrome_options.binary_location = self.CHROME_BIN_PATH

        self.driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_PATH, desired_capabilities=caps, chrome_options=chrome_options)

    def run(self):
        self.driver_startup()
        self.driver.get(self.HOME_URL)
        self.wait_for_page_load_using_js()
        print('---> Page loaded')

        while True:
            try:
                user_id = self.driver.find_element_by_css_selector("input[id='ius-userid']")
                user_password = self.driver.find_element_by_css_selector("input[id='ius-password']")
                user_id.send_keys(USER_ID)
                user_password.send_keys(PASSWORD)

                remember_me = self.driver.find_element(By.ID,'ius-signin-label-checkbox')
                self.click(remember_me)

                submit_btn = self.driver.find_element(By.ID,'ius-sign-in-submit-btn-text')
                self.click(submit_btn)
                print('---> Loggedin now.')

                table_container = self.driver.find_elements_by_class_name('protax-data-table-container')[0]
                print('---> Collecting data.')
                break
            except:
                try:
                    table_container = self.driver.find_elements_by_class_name('protax-data-table-container')[0]
                    break
                except:
                    pass

                try:
                    pin_btn = self.driver.find_element_by_css_selector("input[id='ius-mfa-options-submit-btn']")
                    self.click(pin_btn)

                    pin_code = input('Enter a code: ')

                    code_input = self.driver.find_element_by_css_selector("input[id='ius-mfa-confirm-code']")
                    code_input.send_keys(pin_code)

                    confirm_btn = self.driver.find_element_by_css_selector("input[id='ius-mfa-otp-submit-btn']")
                    self.click(confirm_btn)
                    print('---> Confirmation success.')
                    sleep(2)

                    table_container = self.driver.find_elements_by_class_name('protax-data-table-container')[0]
                    print('---> Collecting data.')
                    break
                except:
                    pass


        today = datetime.datetime.today()

        with open("result_" + today.strftime('%M%H_%m%d%Y') + ".csv", "w") as result:
            wr = csv.writer(result)
            wr.writerow(self.CSV_HEADER)

            while True:
                tbody = table_container.find_elements_by_tag_name('tbody')[0]
                tr_list = tbody.find_elements_by_tag_name('tr')

                for tr in tr_list:
                    tds = tr.find_elements_by_tag_name('td')

                    client_name = self._clean_text(tds[0].text)
                    return_name = self._clean_text(tds[1].text)
                    type = self._clean_text(tds[2].text)
                    data_requests = self._clean_text(tds[3].text)
                    status = self._clean_text(tds[4].text)
                    esignature_status = self._clean_text(tds[5].text)
                    efile_status = self._clean_text(tds[6].text)
                    action = self._clean_text(tds[7].text)

                    data = [client_name, return_name, type, data_requests, status, esignature_status, efile_status, action]
                    wr.writerow(data)
                    print('--->', data)

                next_btn = self.driver.find_element_by_css_selector("button[data-automation-id='protax-pagination-input-next']")
                if next_btn.is_enabled():
                    try:
                        over_lay = self.driver.find_element_by_css_selector("div[data-reach-dialog-content='true']")
                        over_lay_btn = over_lay.find_elements_by_tag_name('button')[0]
                        self.click(over_lay_btn)
                        sleep(0.5)

                        close_overlay_btn = self.driver.find_element_by_css_selector("button[data-automation-id='modal-close']")
                        self.click(close_overlay_btn)
                        sleep(0.5)

                    except:
                        pass

                    self.click(next_btn)
                    sleep(0.5)
                else:
                    print('---> Collecting process was ended')
                    break

    def wait_for_page_load_using_js(self, timeout=30):
        for i in range(timeout):
            if self.page_has_loaded():
                return True

            sleep(0.5)

        print('---> Page did not load in time')
        return False

    def page_has_loaded(self):
        if self.use_driver == DRIVER_CHROME:
            page_state = self.driver.execute_script('return document.readyState;')
        elif self.use_driver == DRIVER_SPYNNER:
            page_state = self.driver.execute_script('(function checkReadyState(){return document.readyState;})()')
            self.driver.browser.wait(0.5)

        if page_state == 'complete':
            return True
        elif page_state == 'interactive':
            if self.use_driver == DRIVER_CHROME:
                sleep(3)
                return True
            elif self.use_driver == DRIVER_SPYNNER:
                self.driver.browser.wait(5)
                return True

        return False

    def click(self, we):
        if self.use_driver == DRIVER_CHROME:
            return we.click()
        elif self.use_driver == DRIVER_SPYNNER:
            return self.driver.click(we)

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()

if __name__ == "__main__":
    spider = IntuitSpider()
    spider.run()