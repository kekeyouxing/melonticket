import asyncio
import base64
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, UnexpectedAlertPresentException
import ddddocr

from config import Config

class ReservationHandler:
    """处理预约流程"""

    def __init__(self, driver):
        self.driver = driver
        self.ocr = ddddocr.DdddOcr(show_ad=False)  # 初始化ddddocr

    def _take_debug_screenshot(self, filename_prefix):
        """拍摄调试截图"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join("data", filename)
            self.driver.save_screenshot(filepath)
            print(f"📸 调试截图已保存: {filepath}")
        except Exception as e:
            print(f"⚠️ 保存截图失败: {e}")

    def add_white_background(self, base64_str):
        """为验证码图片添加白色背景，以提高识别准确率"""
        img_bytes = base64.b64decode(base64_str)
        img = Image.open(BytesIO(img_bytes))
        bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
        bg.paste(img, (0, 0), img)
        return bg

    def recognize(self, base64_str):
        """识别验证码"""
        value = self.add_white_background(base64_str)
        return self.ocr.classification(value)

    def _recognize_captcha(self, base64_str):
        """验证码识别 - 使用ddddocr"""
        try:
            result = self.recognize(base64_str)
            
            if result:
                # 转换为大写并返回
                recognized_text = result.upper()
                print(f"🔤 ddddocr识别结果: {recognized_text}")
                return recognized_text
            else:
                print("❌ ddddocr识别失败，返回空结果")
                return None
                
        except Exception as e:
            print(f"❌ ddddocr识别异常: {e}")
            return None

    async def _handle_captcha(self):
        """处理验证码 - 简化版本"""
        for attempt in range(10):
            try:
                print(f"🔍 验证码处理尝试 {attempt + 1}/10")
                
                # 检查是否已经通过验证
                certification_style = self.driver.execute_script(
                    'return document.querySelector("#certification").style.display'
                )
                if certification_style == "none":
                    print("✅ 验证码已通过")
                    return True
                
                # 获取验证码图片 - 修正元素ID
                captcha_img = self.driver.find_element(By.ID, 'captchaImg')
                captcha_src = captcha_img.get_attribute('src')
                base64_str = captcha_src.split('base64,')[1]
                
                # 识别验证码
                recognized_text = self._recognize_captcha(base64_str)
                print(f"🎯 识别结果: {recognized_text}")
                
                # 输入验证码并确认
                captcha_input = self.driver.find_element(By.ID, 'label-for-captcha')
                captcha_input.clear()
                captcha_input.send_keys(recognized_text)
                self.driver.find_element(By.ID, 'btnComplete').click()
                
                # 使用WebDriverWait智能等待，而不是固定sleep
                try:
                    WebDriverWait(self.driver, 2).until(
                        lambda d: d.execute_script('return document.querySelector("#certification").style.display') == "none"
                    )
                    print("✅ 验证码验证成功")
                    return True
                except TimeoutException:
                    print(f"❌ 验证码验证失败，准备第 {attempt + 2} 次尝试")
                    if attempt < 9:
                        self.driver.find_element(By.ID, 'btnReload').click()
                        # 智能等待，直到图片src发生变化
                        WebDriverWait(self.driver, 5).until(
                            lambda d: d.find_element(By.ID, 'captchaImg').get_attribute('src') != captcha_src
                        )
                
            except Exception as e:
                print(f"❌ 验证码处理异常: {e}")
                if attempt < 9:
                    try:
                        old_captcha_src = self.driver.find_element(By.ID, 'captchaImg').get_attribute('src')
                        self.driver.find_element(By.ID, 'btnReload').click()
                        # 智能等待，直到图片src发生变化
                        WebDriverWait(self.driver, 5).until(
                            lambda d: d.find_element(By.ID, 'captchaImg').get_attribute('src') != old_captcha_src
                        )
                    except Exception as wait_e:
                        print(f"⚠️ 刷新验证码时发生异常或超时: {wait_e}")
                        pass
            
        print("❌ 验证码处理失败，已重试10次")
        return False
            
    def _check_and_close_alert(self):
        """检查并关闭JS警告框（如果存在），模仿用户提供的健壮实现."""
        try:
            # 等待最多2秒，看是否有alert出现
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            print(f"👋 检测到JS弹窗，内容: '{alert_text}'，正在关闭...")
            alert.accept()
            print("✅ JS弹窗已关闭")
        except (TimeoutException, NoAlertPresentException):
            pass  # 如果没有弹窗，则跳过

    def _click_with_alert_handling(self, element):
        """使用JS点击元素，并处理可能出现的JS警告框."""
        try:
            self.driver.execute_script("arguments[0].click();", element)
        except UnexpectedAlertPresentException:
            print("❌ 点击时出现意外的JS弹窗")
            self._check_and_close_alert()
            print("🤔 正在重试点击...")
            self.driver.execute_script("arguments[0].click();", element) # 再次尝试点击

    def _close_notice_popup_if_present(self):
        """检查并关闭网站的HTML通知弹窗（如果存在）"""
        try:
            # 优先尝试点击"今日不再开启"
            cookie_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'noticeAlert_layerpopup_cookie'))
            )
            print("👋 检测到通知弹窗，点击'今日不再开启'...")
            cookie_button.click()
            print("✅ '今日不再开启' 已点击")
        except TimeoutException:
            # 如果"今日不再开启"不存在，则尝试点击普通的关闭按钮
            try:
                close_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, 'noticeAlert_layerpopup_close'))
                )
                print("👋 检测到HTML通知弹窗，正在关闭...")
                close_button.click()
                print("✅ HTML通知弹窗已关闭")
            except TimeoutException:
                print("ℹ️ 未发现HTML通知弹窗")
                pass

    async def execute_reservation(self):
        """执行完整的预约流程"""
        try:
            print(f"⏰ 开始运行预约流程... 当前时间: {datetime.now()}")
            self.driver.get(Config.MELON_BASE_URL)
            print("✅ 已导航到主页面")
            self._close_notice_popup_if_present()
            wait = WebDriverWait(self.driver, 20)
            # 使用JS点击，可以绕过弹窗遮挡
            # 等待元素存在即可，无需等待其可点击
            # 选择日期
            date_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#list_date li button')))
            date_button.click()
            self._check_and_close_alert()
            print("✅ 日期点击完成")
            # 选择时间
            time_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#list_time li button')))
            time_button.click()
            print("✅ 时间点击完成")

            reservation_button = wait.until(EC.presence_of_element_located((By.ID, 'ticketReservation_Btn')))
            reservation_button.click()
            print("✅ 已点击预约按钮")

            print("🔍 等待新窗口出现...")
            original_window = self.driver.current_window_handle
            
            # 等待新的窗口出现
            WebDriverWait(self.driver, 20).until(lambda d: len(d.window_handles) > 1)
            
            # 切换到新窗口
            new_window = [window for window in self.driver.window_handles if window != original_window][0]
            self.driver.switch_to.window(new_window)
            
            # 等待关键元素加载，超时时间为10秒
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'captchaEncStr')))
            print("✅ 弹窗已就绪")
            
            self._take_debug_screenshot("popup_page")

            if not await self._handle_captcha():
                return False
            
            print("🎯 开始选择座位...")
            wait = WebDriverWait(self.driver, 30)

            # 切换到iframe
            iframe = wait.until(EC.presence_of_element_located((By.ID, 'oneStopFrame')))
            self.driver.switch_to.frame(iframe)
            print("✅ 已切换到iframe")
            
            # 等待座位区域画布加载
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#iez_canvas svg')))
            print("✅ 座位区域画布已加载")
            
            # 先获取一次可点击区域的总数，用于日志记录和判断
            initial_clickable_zones_script = """
                const allElements = document.querySelectorAll('#iez_canvas svg rect, #iez_canvas svg path');
                const clickableZones = [];
                for (const el of allElements) {
                        const event = new MouseEvent('mouseover', { bubbles: true, cancelable: true, view: window });
                        el.dispatchEvent(event);
                    if (window.getComputedStyle(el).cursor === 'pointer') {
                            clickableZones.push(el);
                    }
                }
                return clickableZones;
            """
            total_clickable_zones = len(self.driver.execute_script(initial_clickable_zones_script))
            
            if total_clickable_zones == 0:
                print("❌ 未找到可点击的座位区域")
                return False
            
            print(f"📍 找到 {total_clickable_zones} 个可点击的座位区域")

            # 循环尝试每个可点击区域的索引
            for i in range(total_clickable_zones):
                print(f"🎯 尝试区域 {i + 1}/{total_clickable_zones}")
                
                # 每次循环都重新获取当前所有可点击区域
                clickable_zones = self.driver.execute_script(initial_clickable_zones_script)
                
                # 检查索引是否有效
                if i >= len(clickable_zones):
                    print("⚠️ 可点击区域数量发生变化，提前结束")
                    break
                
                # 在点击前获取当前viewBox，为智能等待做准备
                main_svg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#iez_canvas svg')))
                old_viewbox = main_svg.get_attribute('viewBox')

                zone = clickable_zones[i]
                
                # 点击区域
                try:
                    self.driver.execute_script(
                        "arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }))",
                        zone
                    )
                    # 智能等待，直到SVG的viewBox发生变化，表示已缩放
                    WebDriverWait(self.driver, 5).until(
                        lambda d: d.find_element(By.CSS_SELECTOR, '#iez_canvas svg').get_attribute('viewBox') != old_viewbox
                    )
                except Exception as e:
                    print(f"⚠️ 点击区域或等待SVG加载失败: {e}")
                    # 如果点击失败，可能需要返回并重试，或者直接跳过
                    self.driver.execute_script("history.back();")
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#iez_canvas svg')))
                    continue

                # 检查是否有可用座位
                try:
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ez_canvas svg')))
                    seat_selected = self.driver.execute_script("""
                        const rects = document.querySelectorAll('#ez_canvas svg rect');
                        const availableSeats = Array.from(rects).filter(rect => {
                            const fill = rect.getAttribute('fill');
                            return fill !== '#DDDDDD' && fill !== 'none';
                        });
                        if (availableSeats.length > 0) {
                            availableSeats[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                            return true;
                        }
                        return false;
                    """)
                    
                    if seat_selected:
                        print("✅ 成功选择座位")
                        # 截图
                        self._take_debug_screenshot("seat_selected")
                        break
                        
                except Exception:
                    # 如果座位图未加载或没有可用座位，则返回上一页重新选择区域
                    self.driver.execute_script("history.back();")
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#iez_canvas svg'))) # 确保返回成功
                    continue
            else:
                print("❌ 已尝试所有区域，均未找到可用座位")
            return False
            
            # --- 开始支付流程 ---
            print("💳 开始支付...")

            # 等待按钮变为可点击状态（等待 'on' 类出现）
            # print("🔍 等待选座完成按钮变为可点击状态...")
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.button.btNext.on #nextTicketSelection')))
            # print("✅ 选座完成按钮已激活")

            # 点击下一步
            element = wait.until(EC.presence_of_element_located((By.ID, 'nextTicketSelection')))
            self.driver.execute_script("arguments[0].click();", element)
            print("✅ 已点击 '下一步'")
            
            # 等待支付页面加载
            element = wait.until(EC.presence_of_element_located((By.ID, 'nextPayment')))
            self.driver.execute_script("arguments[0].click();", element)
            print("✅ 已点击 '下一步支付'")
            
            # 输入手机号
            print("📱 输入手机号...")
            phone_parts = Config.PHONE.split('-')
            if len(phone_parts) == 3:
                wait.until(EC.presence_of_element_located((By.ID, 'tel1'))).send_keys(phone_parts[0])
                wait.until(EC.presence_of_element_located((By.ID, 'tel2'))).send_keys(phone_parts[1])
                wait.until(EC.presence_of_element_located((By.ID, 'tel3'))).send_keys(phone_parts[2])
                print(f"✅ 已输入手机号: {Config.PHONE}")

            # 选择支付方式
            print("🔄 选择支付方式...")
            element = wait.until(EC.presence_of_element_located((By.ID, 'payMethodCode003')))
            self.driver.execute_script("arguments[0].click();", element)
            
            element = wait.until(EC.presence_of_element_located((By.ID, 'cashReceiptIssueCode3')))
            self.driver.execute_script("arguments[0].click();", element)
            

            # 选择银行
            print("🔄 选择银行...")
            self.driver.execute_script("""
                const select = document.querySelector('select[name="bankCode"]');
                if (select) {
                    select.value = '88';
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            

            # 同意条款
            print("🔄 同意所有条款...")
            element = wait.until(EC.presence_of_element_located((By.ID, 'chkAgreeAll')))
            self.driver.execute_script("arguments[0].click();", element)
            
            
            # 最终支付
            print("🔄 点击最终支付...")
            element = wait.until(EC.presence_of_element_located((By.ID, 'btnFinalPayment')))
            self.driver.execute_script("arguments[0].click();", element)
            
            print(f"⏰ 最终支付已提交！... 当前时间: {datetime.now()}")
            # 等待10秒
            await asyncio.sleep(10)
            self._take_debug_screenshot("success")
            return True
            
        except Exception as e:
            print(f"❌ 预约流程失败: {e}")
            self._take_debug_screenshot("reservation_failure")
            return False
        finally:
            # 确保在操作结束后切回主内容
            self.driver.switch_to.default_content()
