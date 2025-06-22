import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config import Config

class LoginHandler:
    """处理登录流程"""
    
    def __init__(self, driver):
        self.driver = driver
    
    # def _close_notice_popup_if_present(self):
    #     """检查并关闭网站的HTML通知弹窗（如果存在）"""
    #     try:
    #         # 优先尝试点击"今日不再开启"
    #         cookie_button = WebDriverWait(self.driver, 5).until(
    #             EC.element_to_be_clickable((By.ID, 'noticeAlert_layerpopup_cookie'))
    #         )
    #         print("👋 检测到通知弹窗，点击'今日不再开启'...")
    #         cookie_button.click()
    #         print("✅ '今日不再开启' 已点击")
    #     except TimeoutException:
    #         # 如果"今日不再开启"不存在，则尝试点击普通的关闭按钮
    #         try:
    #             close_button = WebDriverWait(self.driver, 5).until(
    #                 EC.element_to_be_clickable((By.ID, 'noticeAlert_layerpopup_close'))
    #             )
    #             print("👋 检测到HTML通知弹窗，正在关闭...")
    #             close_button.click()
    #             print("✅ HTML通知弹窗已关闭")
    #         except TimeoutException:
    #             print("ℹ️ 未发现HTML通知弹窗")
    #             pass

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
            
            print("✅ Login successful.")
            # 登录成功后，直接导航到预定页面
            print(f"🚀 Navigating to reservation page: {Config.MELON_BASE_URL}")
            # self.driver.get(Config.MELON_BASE_URL)
            
            # 由于页面加载策略为 'none'，driver.get是非阻塞的。
            # 在尝试关闭弹窗前，使用智能等待确保body元素已加载，这比固定等待更高效可靠。
            # WebDriverWait(self.driver, 5).until(
            #     EC.presence_of_element_located((By.TAG_NAME, 'body'))
            # )
            
            # # 关闭可能出现的弹窗
            # self._close_notice_popup_if_present()
            
            return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            # 登录失败时截图以供调试
            self.driver.save_screenshot('/app/data/login_failure.png')
            return False 