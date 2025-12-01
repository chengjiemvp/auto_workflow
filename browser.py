from playwright.sync_api import sync_playwright
import time
import random


class FileMaker:
    _instance = None
    _initialized = False

    # singleton pattern
    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # initialize browser only once
    def __init__(self):
        if self._initialized==False:
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=False)
            user_agent_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
            self.page = self.browser.new_page(user_agent=user_agent_str)
            self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def log_in(self):
        self.page.goto("https://anl.gofreight.co/login/?next=/")
        self.page.wait_for_selector('input[value="Login"]', state='visible')
        print(f"[log] page loaded")
        self.page.fill('input[id="username"]', 'cheng.jie')
        self.page.fill('input[name="password"]', '1aA5Cc')
        time.sleep(random.uniform(0.1, 0.5))
        self.page.click('input[value="Login"]')
        self.page.wait_for_selector('//div[contains(text(), "Ocean Import (")]', state='visible')
        print(f'[log] logged in')
        return True


maker = FileMaker()
maker.log_in()
time.sleep(50)
