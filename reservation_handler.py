import asyncio
import base64
import os
import time
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
            # 使用绝对路径确保截图保存在挂载的数据卷中
            filepath = f"/app/data/{filename}"
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
        """检查并关闭JS警告框（如果存在）"""
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
            print("弹窗已自动关闭")
            self.driver.switch_to.default_content()
        except NoAlertPresentException:
            pass  # 如果没有弹窗，则跳过

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
        """执行完整的预约流程，将所有逻辑放在一个方法内。"""
        try:
            # 1. 循环导航直到页面正常加载
            print(f"⏰ 开始运行预约流程... 当前时间: {datetime.now()}")
            
            # 循环进入页面，处理alert弹窗，直到出现正常元素
            max_attempts = 10
            for attempt in range(max_attempts):
                print(f"🔄 第 {attempt + 1} 次尝试进入页面...")
                self.driver.get(Config.MELON_BASE_URL)
                
                # 检测并关闭alert弹窗
                self._check_and_close_alert()
                
                # 检查是否出现了正常的页面元素
                try:
                    wait = WebDriverWait(self.driver, 3)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#list_date li button')))
                    print("✅ 页面正常加载，找到日期选择元素")
                    break
                except TimeoutException:
                    print(f"⚠️ 第 {attempt + 1} 次尝试未找到日期元素，继续重试...")
                    if attempt == max_attempts - 1:
                        print("❌ 已达最大重试次数，页面可能存在问题")
                        return False
                    time.sleep(0.3)  # 等待1秒后重试
            
            # self._close_notice_popup_if_present()
            wait = WebDriverWait(self.driver, 20)
            
            # 选择日期和时间
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#list_date li button'))).click()
            print("✅ 日期点击完成")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#list_time li button'))).click()
            print("✅ 时间点击完成")
            wait.until(EC.presence_of_element_located((By.ID, 'ticketReservation_Btn'))).click()
            print("✅ 已点击预约按钮")
            self._check_and_close_alert()
            # 2. 切换到新窗口并处理验证码
            print("🔍 等待新窗口出现...")
            # 截图
            self._take_debug_screenshot("reservation_window")
            original_window = self.driver.current_window_handle
            WebDriverWait(self.driver, 3600).until(lambda d: len(d.window_handles) > 1)
            new_window = [window for window in self.driver.window_handles if window != original_window][0]
            self.driver.switch_to.window(new_window)
            
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'captchaEncStr')))
            print("✅ 弹窗已就绪")

            if not await self._handle_captcha():
                print("❌ 验证码处理失败，流程终止。")
                return False
            
            # 3. 进入Iframe并处理座位选择和支付
            print("🎯 开始处理iframe工作流...")
            iframe_wait = WebDriverWait(self.driver, 30)
            try:
                # 切换到iframe
                iframe = iframe_wait.until(EC.presence_of_element_located((By.ID, 'oneStopFrame')))
                self.driver.switch_to.frame(iframe)
                print("✅ 已切换到iframe")
                
                # 等待座位区域画布加载
                iframe_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#iez_canvas svg')))
                print("✅ 座位区域画布已加载")

                # --- 恢复您原有的座位选择逻辑 ---
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
                    self._take_debug_screenshot("no_clickable_zones")
                    return False
            
                print(f"📍 找到 {total_clickable_zones} 个可点击的座位区域")

                seat_selection_successful = False
                for i in range(total_clickable_zones):
                    print(f"🎯 尝试区域 {i + 1}/{total_clickable_zones}")
                    # 每次循环都重新获取可点击区域
                    clickable_zones = self.driver.execute_script(initial_clickable_zones_script)
                    if i >= len(clickable_zones):
                        print("⚠️ DOM结构发生变化，跳过此轮尝试")
                        continue
            
                    zone = clickable_zones[i]
                    try:
                        # 使用 dispatchEvent 以确保能可靠地点击SVG内部的区域元素
                        self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));", zone)
                        # 给页面一点时间来响应点击事件
                        time.sleep(0.1)
                        
                        # 使用您原来的逻辑查找座位
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
                            print(f"  - ✅ 在区域 {i + 1} 中成功选择座位")
                            self._take_debug_screenshot("seat_selected")
                            seat_selection_successful = True
                            break # 成功，跳出选区循环
                    
                    except Exception as e:
                        print(f"  - 区域 {i + 1} 尝试失败: {e}，返回...")
                        self.driver.execute_script("history.back();")
                        iframe_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#iez_canvas svg')))
                        continue
            
                if not seat_selection_successful:
                    print("❌ 已尝试所有区域，均未找到可用座位")
                    self._take_debug_screenshot("all_zones_failed")
                    return False
            
                # --- 恢复您原有的支付流程，仅在选座成功后执行 ---
                print("💳 选座成功，开始支付流程...")
                # 复用 iframe_wait 以保持一致的超时时间
                
                # 点击下一步
                # 等待按钮变为激活状态（等待 'on' 类出现）
                print("🔍 等待选座完成按钮变为可点击状态...")
                iframe_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.button.btNext.on #nextTicketSelection')))
                print("✅ 选座完成按钮已激活")
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'nextTicketSelection')))
 
                self.driver.execute_script("arguments[0].click();", element)
                print("✅ 已点击 '下一步'")
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'nextPayment')))
                self.driver.execute_script("arguments[0].click();", element)
                
                # 输入手机号
                print("📱 输入手机号...")
                phone_parts = Config.PHONE.split('-')
                if len(phone_parts) == 3:
                    iframe_wait.until(EC.presence_of_element_located((By.ID, 'tel1'))).send_keys(phone_parts[0])
                    iframe_wait.until(EC.presence_of_element_located((By.ID, 'tel2'))).send_keys(phone_parts[1])
                    iframe_wait.until(EC.presence_of_element_located((By.ID, 'tel3'))).send_keys(phone_parts[2])
                    print(f"✅ 已输入手机号: {Config.PHONE}")

                # 选择支付方式
                print("🔄 选择支付方式...")
                # element = iframe_wait.until(EC.element_to_be_clickable((By.ID, 'payMethodCode003')))
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'payMethodCode003')))
                self.driver.execute_script("arguments[0].click();", element)
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'cashReceiptIssueCode3')))
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
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'chkAgreeAll')))
                self.driver.execute_script("arguments[0].click();", element)
                
                # 最终支付
                print("🔄 点击最终支付...")
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'btnFinalPayment')))
                self.driver.execute_script("arguments[0].click();", element)
                
                print(f"🎉 最终支付已提交！... 当前时间: {datetime.now()}")
                time.sleep(5)
                self._take_debug_screenshot("reservation_submitted")
                
                return True
                
            finally:
                # 确保在操作结束后切回主内容
                self.driver.switch_to.default_content()
                print("✅ 已切换回主页面")

        except TimeoutException as e:
            print(f"❌ 预约流程超时: {e}")
            self._take_debug_screenshot("reservation_timeout")
            return False
        except Exception as e:
            print(f"❌ 预约流程发生未知错误: {e}")
            self._take_debug_screenshot("reservation_exception")
            return False
