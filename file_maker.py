import os
import json
import time
import random
import socket
import pandas as pd
import sqlite3
from log import output
from working_list import get_list
from cryptography.fernet import Fernet
from playwright.sync_api import sync_playwright, expect


user_data_dir = os.path.join(os.getcwd(), "palywright_user_data")

class FileMaker:
    _instance = None
    _initialized = False
    _cookie = False
    user_agent_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"

    # singleton pattern
    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    # initialize browser only once
    def __init__(self):
        if self._initialized==False:
            output("[log] opening browser and connect db")
            self.conn = sqlite3.connect("database.db")
            output("[log] db connected")
            self.cursor = self.conn.cursor()
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=False)
            self.context = self.load_session()
            self.page = self.context.new_page()
            self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        output("[log] closing browser and disconnect db")
        self.conn.close()
        output("[log] db closed")
        if self.context:
            self.context.close()
            output("[log] context closed")
        if self.browser:
            self.browser.close()
            output("[log] browser closed")

    def load_session(self):
        hostname = socket.gethostname()
        try:
            self.cursor.execute("select * from sessions where username = ? AND hostname = ?", 
                                ("cheng.jie", hostname, ))
            session_data = self.cursor.fetchone()[2]
            self.context = self.browser.new_context(storage_state=json.loads(session_data), 
                                                    user_agent=self.user_agent_str,
                                                    viewport={'width': 1366, 'height': 768})
            self._cookie = True
        except sqlite3.OperationalError:
            self.context = self.browser.new_context(user_agent=self.user_agent_str,
                                                    viewport={'width': 1366, 'height': 768})
            self._cookie = False
        return self.context

    def log_in(self):
        if self._cookie:
            self.page.goto("https://anl.gofreight.co/")
        else:
            self.page.goto("https://anl.gofreight.co/login/?next=/")
            self.page.wait_for_selector('input[value="Login"]', state='visible')
            output(f"[log] page loaded")
            ## get user info from db
            user_info = self.get_user()
            username = user_info[0]
            password = user_info[1]
            input_box = self.page.locator("input[id='username']")
            input_box.press_sequentially(username, delay=random.uniform(0.1, 0.3))
            input_box = self.page.locator("input[name='password']")
            input_box.press_sequentially(password, delay=random.uniform(0.1, 0.3))
            ##
            self.page.click("input[name='remember']")
            time.sleep(random.uniform(0.1, 0.5))
            self.page.click('input[value="Login"]')
        self.page.wait_for_selector('''//div[contains(text(), "Ocean Import (")]''', state='visible')
        output(f'[log] logged in')
        if len(self.context.cookies()) > 0:
            new_cookies = self.context.storage_state()
            output(f"[log] cookies eg: name:{new_cookies['cookies'][0]['name']}")
            new_cookies_str = json.dumps(new_cookies)
            self.cursor.execute("UPDATE sessions SET session_data = ? WHERE username = ? AND hostname = ?", 
                                (new_cookies_str, "cheng.jie", socket.gethostname()))
            self.conn.commit()
        else:
            output("[err] no cookies found")
            raise Exception("no cookies found")
        return True

    def get_user(self):
        user_info = None
        try:
            with open('.key', 'rb') as f:
                key = f.read()
            self.cursor.execute("SELECT user, pswd_encrypt from gofreight_users WHERE user = ?", ("cheng.jie",))
            user_info = self.cursor.fetchone()
            user_info = [*user_info]
        except FileNotFoundError:
            output(".key file not found")
        fernet = Fernet(key)
        user_info[1] = fernet.decrypt(user_info[1].encode('utf-8')).decode('utf-8')
        return user_info

    def gather_tasks(self, working_list):
        for index, row in working_list.iterrows():
            self.create_file(row)
        return True

    def create_file(self,row):
        self.page.locator('a[href="/ocean/import/myshipment/"]').get_by_text("My Shipment", exact=True).click()
        time.sleep(random.uniform(0.1, 0.5))
        self.page.locator('a[href="/ocean/import/shipment/"]').click()
        time.sleep(random.uniform(0.1, 0.5))
        self.page.wait_for_selector("text='Subject'", state='visible')
        self.page.locator('''input[name="MBL_NO"]''').press_sequentially(row['MBL'], delay=random.uniform(0.1, 0.3))
        self.page.locator('''hc-vessel-name-select''').click()
        self.page.locator('''hc-vessel-name-select div[class='search-container select2-search']>input[type='text']''').press_sequentially(row['Vessel'], delay=random.uniform(0.1, 0.3))
        self.page.get_by_role("option", name=row['Vessel'], exact=True).click()
        self.page.locator('''input[ng-model="vm.mbl.voyage"]''').press_sequentially(row['Voyage'], delay=random.uniform(0.1, 0.3))
        ## Terminal
        if row['Terminal'] in ["?", "？"]:
            pass
        else:
            self.page.locator('''hc-tp-select[ng-model="vm.mbl.cy_location"]''').click()
            self.page.locator('''hc-tp-select[ng-model="vm.mbl.cy_location"] div[class='search-container select2-search']>input[type='search']''').press_sequentially(row['Terminal'], delay=random.uniform(0.1, 0.3))
            try:
                self.cursor.execute("SELECT TP_ID from terminals WHERE firms_code = ?", (row['Terminal'],))
                tp_id = self.cursor.fetchone()[0]
            except Exception as e:
                output(f"[err] terminal {row['Terminal']} not found in db: {e}")
                raise Exception
            self.page.locator(f'''//span[contains(text(), "{tp_id}")]''').click()
        ## POL
        self.page.locator('''hc-location-select[ng-model="vm.mbl.POL"]''').click()
        try:
            self.cursor.execute("SELECT TP_ID from cy_locations WHERE cy_code = ?", (row['POL'],))
            loc_tp_id = self.cursor.fetchone()[0]
        except:
            output(f"[err] POL {row['POL']} not found in db")
            raise Exception
        self.page.locator('''hc-location-select[ng-model="vm.mbl.POL"] div[class='search-container select2-search']>input[type='text']''').press_sequentially(loc_tp_id, delay=random.uniform(0.1, 0.3))
        self.page.get_by_role("option", name=loc_tp_id).click()
        ## POD
        self.page.locator('''hc-location-select[ng-model="vm.mbl.POD"]''').click()
        try:
            self.cursor.execute("SELECT TP_ID from cy_locations WHERE cy_code = ?", (row['POD'],))
            des_tp_id = self.cursor.fetchone()[0]
        except:
            output(f"[err] POL {row['POD']} not found in db")
            raise Exception
        self.page.locator('''hc-location-select[ng-model="vm.mbl.POD"] div[class='search-container select2-search']>input[type='text']''').press_sequentially(des_tp_id, delay=random.uniform(0.1, 0.3))
        self.page.get_by_role("option", name=des_tp_id).click()
        ## ETD
        etd_ele = self.page.locator('''input[type="text"][name="ETD"][ng-model="vm.mbl.ETD"]''')
        etd_ele.click()
        etd_ele.clear()
        etd_ele.press_sequentially(row['ETD'].strftime(f"%m-%d-%Y"), delay=100)
        etd_ele.press("Enter")
        ## ETA
        eta_ele = self.page.locator('''input[type="text"][name="ETA"][ng-model="vm.mbl.ETA"]''')
        eta_ele.click()
        eta_ele.clear()
        eta_ele.press_sequentially(row['ETA'].strftime(f"%m-%d-%Y"), delay=100)
        eta_ele.press("Enter")
        ## PART2 - FinalDes, DEL, FND, DETA, FETA
        if row['FinalDes'] == "|":
            pass
        else:
            ## DEL
            self.page.locator('''hc-location-select[ng-model="vm.mbl.DEL"]''').click()
            try:
                self.cursor.execute("SELECT TP_ID from cy_locations WHERE cy_code = ?", (row['FinalDes'],))
                final_tp_id = self.cursor.fetchone()[0]
            except Exception as e:
                output(f"[err] FinalDes {row['FinalDes']} not found in db: {e}")
                raise Exception
            self.page.locator('''hc-location-select[ng-model="vm.mbl.DEL"] div[class='search-container select2-search']>input[type='text']''').press_sequentially(final_tp_id, delay=random.uniform(0.1, 0.3))
            self.page.get_by_role("option", name=final_tp_id).click()
            ## FND
            self.page.locator('''hc-location-select[ng-model="vm.mbl.FDEST"]''').click()
            self.page.locator('''hc-location-select[ng-model="vm.mbl.FDEST"] div[class='search-container select2-search']>input[type='text']''').press_sequentially(final_tp_id, delay=random.uniform(0.1, 0.3))
            self.page.get_by_role("option", name=final_tp_id).click()
            ## DATE
            eta_ele = self.page.locator('''input[name="DETA"][type="text"][ng-model="vm.mbl.DETA"]''')
            eta_ele.click()
            eta_ele.clear()
            eta_ele.press_sequentially((row['ETA'] + pd.Timedelta(days=2)).strftime(f"%m-%d-%Y"), delay=100)
            eta_ele.press("Enter")
            ## DATE2
            eta_ele = self.page.locator('''input[name="FETA"][type="text"][ng-model="vm.mbl.FETA"]''')
            eta_ele.click()
            eta_ele.clear()
            eta_ele.press_sequentially((row['ETA'] + pd.Timedelta(days=2)).strftime(f"%m-%d-%Y"), delay=100)
            eta_ele.press("Enter")  
        ## button save
        expect(self.page.locator('''button[id='save'][type='submit']''')).to_be_visible()
        expect(self.page.locator('''button[id='save'][type='submit']''')).to_be_enabled()
        self.page.locator('''button[id='save'][type='submit']''').click()
        ## finished
        return True

    def get_working_list(self):
        return True

with FileMaker() as maker:
    maker.log_in()
    maker.gather_tasks(get_list())
    maker.page.pause()
    time.sleep(50)
