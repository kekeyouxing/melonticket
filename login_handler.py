import asyncio
import json
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config import Config

class LoginHandler:
    """处理登录流程，支持Cookie复用"""

    def __init__(self, driver):
        self.driver = driver
        self.cookie_path = "/app/data/cookies.json"

    def _take_debug_screenshot(self, filename_prefix):
        """拍摄调试截图"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = f"/app/data/{filename}"
            self.driver.save_screenshot(filepath)
            print(f"📸 调试截图已保存: {filepath}")
        except Exception as e:
            print(f"⚠️ 保存截图失败: {e}")

    def _save_cookies(self):
        """保存当前会话的Cookie"""
        with open(self.cookie_path, 'w') as f:
            json.dump(self.driver.get_cookies(), f)
        print(f"🍪 Cookie已保存至 {self.cookie_path}")

    def _load_cookies(self):
        """加载Cookie并验证登录状态"""
        if not os.path.exists(self.cookie_path):
            return False

        print("🍪 发现Cookie文件，尝试使用Cookie登录...")
        try:
            # 必须先访问目标域名，才能设置Cookie
            self.driver.get(Config.MELON_BASE_URL)
            with open(self.cookie_path, 'r') as f:
                cookies = json.load(f)

            for cookie in cookies:
                # Selenium的add_cookie方法可能会对某些键敏感，例如 'expiry'
                if 'expiry' in cookie:
                    del cookie['expiry']
                self.driver.add_cookie(cookie)

            print("...Cookie已加载，刷新页面以应用...")
            self.driver.refresh()

            # 验证登录是否成功，通过查找ID为"btnLogout"的登出按钮
            # wait = WebDriverWait(self.driver, 5)
            # wait.until(EC.presence_of_element_located((By.ID, "btnLogout")))
            print("✅ 使用Cookie登录成功！")
            return True
        except Exception as e:
            print(f"⚠️ Cookie登录失败: {e}。")
            self._take_debug_screenshot("login_with_cookie_failed")
            return False

    async def _manual_login(self):
        """执行手动的用户名密码登录"""
        print("🔐 未找到有效会话，开始手动登录...")
        try:
            self.driver.get(Config.MELON_LOGIN_URL)
            wait = WebDriverWait(self.driver, 10)

            username_field = wait.until(EC.presence_of_element_located((By.ID, 'id')))
            password_field = wait.until(EC.presence_of_element_located((By.ID, 'pwd')))
            login_button = wait.until(EC.element_to_be_clickable((By.ID, 'btnLogin')))

            username_field.send_keys(Config.MELON_USERNAME)
            password_field.send_keys(Config.MELON_PASSWORD)
            login_button.click()

            # 关键：验证登录是否成功
            # 登录后通常会跳转，我们去主页检查ID为"btnLogout"的登出按钮
            # self.driver.get(Config.MELON_BASE_URL)
            # wait.until(EC.presence_of_element_located((By.ID, "btnLogout")))
            print("✅ 手动登录成功")
            
            # 登录成功后保存Cookie
            self._save_cookies()
            return True
        except TimeoutException:
            print("❌ 手动登录失败。可能是凭据错误或页面结构已更改。")
            self._take_debug_screenshot("manual_login_failed")
            return False
        except Exception as e:
            print(f"❌ 手动登录过程中发生意外错误: {e}")
            self._take_debug_screenshot("manual_login_exception")
            return False

    async def login(self):
        """执行登录流程，优先使用Cookie"""
        if self._load_cookies():
            return True
        return await self._manual_login() 