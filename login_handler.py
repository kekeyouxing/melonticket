import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import Config

class LoginHandler:
    """处理登录流程"""
    
    def __init__(self, driver):
        self.driver = driver
    
    async def login(self):
        """执行登录"""
        try:
            print("Navigating to login page...")
            self.driver.get(Config.MELON_LOGIN_URL)
            
            # 使用WebDriverWait等待元素加载完成，增加鲁棒性
            wait = WebDriverWait(self.driver, 10)
            
            username_field = wait.until(EC.presence_of_element_located((By.ID, 'id')))
            password_field = wait.until(EC.presence_of_element_located((By.ID, 'pwd')))
            login_button = wait.until(EC.element_to_be_clickable((By.ID, 'btnLogin')))
            
            print("Entering credentials...")
            username_field.send_keys(Config.MELON_USERNAME)
            password_field.send_keys(Config.MELON_PASSWORD)
            
            print("Clicking login button...")
            login_button.click()
            
            # 修正：使用您原始的URL检查逻辑，而不是等待一个不确定的元素
            print("Waiting for URL to change after login...")
            wait.until(EC.url_changes(Config.MELON_LOGIN_URL))

            current_url = self.driver.current_url
            if "login" in current_url.lower():
                print(f"❌ Login failed, redirected to: {current_url}")
                self.driver.save_screenshot('/app/data/login_failure.png')
                return False
            
            print("✅ Login successful.")
            return True
                
        except Exception as e:
            print(f"❌ Login failed: {e}")
            # 登录失败时截图以供调试
            self.driver.save_screenshot('/app/data/login_failure.png')
            return False 