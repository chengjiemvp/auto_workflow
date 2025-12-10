import os
import json
import time
import random
import socket
import sqlite3
from playwright.sync_api import sync_playwright
from log import output
from cryptography.fernet import Fernet
from working_list import working_list


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
                                                    user_agent=self.user_agent_str)
            self._cookie = True
        except sqlite3.OperationalError:
            self.context = self.browser.new_context(user_agent=self.user_agent_str)
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

    def create_file(self):
        return None

    def get_working_list(self):
        return True

with FileMaker() as maker:
    maker.log_in()
    maker.create_file()
    time.sleep(50)
