import os
import asyncio
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, UnexpectedAlertPresentException
import base64
from PIL import Image, ImageEnhance, ImageFilter
import io
import cv2
import numpy as np

from config import Config

class ReservationHandler:
    """处理预约流程"""

    def __init__(self, driver):
        self.driver = driver

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

    def _recognize_captcha(self, base64_str):
        """验证码识别 - 保持原始逻辑"""
        try:
            image_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(image_data))
            
            # 转换为白色背景
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            img_array = np.array(img)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 保存处理后的图像用于调试
            cv2.imwrite('data/processed_captcha.png', binary)
            
            # 这里返回一个示例值，实际应该接入OCR服务
            return "ABCD"
        except Exception as e:
            print(f"验证码识别失败: {e}")
            return None

    async def _handle_captcha(self):
        """处理验证码 - 增强错误处理和调试信息"""
        for attempt in range(10):
            try:
                print(f"🔍 验证码处理尝试 {attempt + 1}/10")
                
                wait = WebDriverWait(self.driver, 10)
                
                # 检查验证码容器是否存在
                try:
                    certification_div = wait.until(EC.presence_of_element_located((By.ID, 'certification')))
                    if not certification_div.is_displayed():
                        print("✅ 验证码已通过，无需处理")
                        return True
                except Exception as e:
                    print(f"⚠️ 无法找到验证码容器: {e}")
                
                # 查找验证码图片
                try:
                    captcha_img = wait.until(EC.presence_of_element_located((By.ID, 'imgCaptcha')))
                    print("✅ 找到验证码图片元素")
                except Exception as e:
                    print(f"❌ 无法找到验证码图片: {e}")
                    if attempt < 9:
                        await asyncio.sleep(2)
                        continue
                    else:
                        return False
                
                # 获取验证码图片数据
                try:
                    captcha_src = captcha_img.get_attribute('src')
                    if not captcha_src:
                        print("❌ 验证码图片src为空")
                        if attempt < 9:
                            self._safe_click_reload()
                            await asyncio.sleep(2)
                            continue
                        else:
                            return False
                    
                    if 'data:image' not in captcha_src:
                        print(f"❌ 验证码图片格式异常: {captcha_src[:100]}...")
                        if attempt < 9:
                            self._safe_click_reload()
                            await asyncio.sleep(2)
                            continue
                        else:
                            return False
                    
                    base64_str = captcha_src.split(',')[1]
                    print(f"✅ 获取到验证码图片数据，长度: {len(base64_str)}")
                    
                except Exception as e:
                    print(f"❌ 获取验证码图片数据失败: {e}")
                    if attempt < 9:
                        self._safe_click_reload()
                        await asyncio.sleep(2)
                        continue
                    else:
                        return False
                
                # 识别验证码
                try:
                    recognized_text = self._recognize_captcha(base64_str)
                    if not recognized_text:
                        print("❌ 验证码识别失败")
                        if attempt < 9:
                            self._safe_click_reload()
                            await asyncio.sleep(2)
                            continue
                        else:
                            return False
                    
                    print(f"🎯 识别结果: {recognized_text}")
                    
                except Exception as e:
                    print(f"❌ 验证码识别异常: {e}")
                    if attempt < 9:
                        self._safe_click_reload()
                        await asyncio.sleep(2)
                        continue
                    else:
                        return False
                
                # 输入验证码 - 使用正确的元素ID
                try:
                    captcha_input = self.driver.find_element(By.ID, 'label-for-captcha')
                    captcha_input.clear()
                    captcha_input.send_keys(recognized_text)
                    print("✅ 验证码已输入")
                    
                    # 点击确认按钮 - 使用正确的元素ID
                    confirm_btn = self.driver.find_element(By.ID, 'btnComplete')
                    confirm_btn.click()
                    print("✅ 已点击确认按钮")
                    
                except Exception as e:
                    print(f"❌ 输入验证码或点击确认失败: {e}")
                    if attempt < 9:
                        self._safe_click_reload()
                        await asyncio.sleep(2)
                        continue
                    else:
                        return False

                # 等待验证结果
                await asyncio.sleep(2)

                # 检查验证是否成功
                try:
                    certification_div = self.driver.find_element(By.ID, 'certification')
                    if not certification_div.is_displayed():
                        print("✅ 验证码验证成功")
                        return True
                    else:
                        print("❌ 验证码验证失败，准备重试")
                        if attempt < 9:
                            print(f"🔄 准备第 {attempt + 2} 次尝试，点击重新加载验证码")
                            self._safe_click_reload()
                            await asyncio.sleep(2)
                        
                except Exception as e:
                    print(f"❌ 检查验证结果失败: {e}")
                    if attempt < 9:
                        self._safe_click_reload()
                        await asyncio.sleep(2)
                        continue
                    
            except Exception as e:
                print(f"❌ captcha处理异常: {e}")
                if attempt < 9:
                    print(f"🔄 异常重试第 {attempt + 2} 次，点击重新加载验证码")
                    self._safe_click_reload()
                    await asyncio.sleep(2)
                    continue
            
        print("❌ 验证码处理失败，已重试10次")
        return False
    
    def _safe_click_reload(self):
        """安全地点击重新加载按钮"""
        try:
            reload_btn = self.driver.find_element(By.ID, 'btnReload')
            reload_btn.click()
            print("🔄 已点击重新加载验证码")
        except Exception as e:
            print(f"⚠️ 点击重新加载按钮失败: {e}")

    def _check_and_close_alert(self):
        """检查并关闭JS警告框（如果存在），模仿用户提供的健壮实现."""
        try:
            # 等待最多2秒，看是否有alert出现
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            print(f"👋 检测到JS弹窗，内容: '{alert_text}'，正在关闭...")
            alert.accept()
            print("✅ JS弹窗已关闭")
            # 切换回主内容是一个好习惯
            self.driver.switch_to.default_content()
        except (TimeoutException, NoAlertPresentException):
            pass  # 如果没有弹窗，则跳过

    def _click_with_alert_handling(self, element):
        """点击元素，并处理可能出现的JS警告框."""
        try:
            element.click()
        except UnexpectedAlertPresentException:
            print("❌ 点击时出现意外的JS弹窗")
            self._check_and_close_alert()
            print("🤔 正在重试点击...")
            element.click() # 再次尝试点击

    def _close_notice_popup_if_present(self):
        """检查并关闭网站的HTML通知弹窗（如果存在）"""
        try:
            close_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.ID, 'noticeAlert_layerpopup_close'))
            )
            print("👋 检测到HTML通知弹窗，正在关闭...")
            close_button.click()
            print("✅ HTML通知弹窗已关闭")
        except TimeoutException:
            print("ℹ️ 未发现HTML通知弹窗")
            pass

    async def _select_zone_and_seat(self):
        """选择座位区域并选择座位 - 修复SVG交互问题"""
        try:
            print("🎯 开始选择座位区域和座位...")
            
            wait = WebDriverWait(self.driver, 30)
            
            # 等待座位区域画布加载
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#iez_canvas svg')))
            print("✅ 座位区域画布已加载")
            
            # 获取所有可点击的座位区域 - 修改选择器，排除透明元素
            clickable_zones = self.driver.execute_script("""
                const svgElements = document.querySelectorAll('#iez_canvas svg rect, #iez_canvas svg path');
                const clickableZones = [];
                
                for (const el of svgElements) {
                    // 检查元素是否可见且不透明
                    const style = window.getComputedStyle(el);
                    const opacity = el.getAttribute('opacity') || style.opacity || '1';
                    const display = el.getAttribute('display') || style.display || 'block';
                    
                    if (opacity !== '0' && display !== 'none') {
                        // 触发鼠标悬停事件检查cursor
                        const event = new MouseEvent('mouseover', { bubbles: true, cancelable: true, view: window });
                        el.dispatchEvent(event);
                        const cursor = window.getComputedStyle(el).cursor;
                        
                        if (cursor === 'pointer' || el.style.cursor === 'pointer') {
                            clickableZones.push(el);
                        }
                    }
                }
                return clickableZones;
            """)
            
            if len(clickable_zones) == 0:
                print("❌ 未找到可点击的座位区域")
                return False
            
            print(f"📍 找到 {len(clickable_zones)} 个可点击的座位区域")
            
            # 按前排中间优先排序
            zone_positions = []
            for zone in clickable_zones:
                try:
                    pos = self.driver.execute_script("""
                        const el = arguments[0];
                        let bbox;
                        try {
                            bbox = el.getBBox();
                        } catch(e) {
                            // 如果getBBox失败，尝试使用getBoundingClientRect
                            const rect = el.getBoundingClientRect();
                            bbox = { x: rect.left, y: rect.top, width: rect.width, height: rect.height };
                        }
                        return { centerX: bbox.x + bbox.width/2, centerY: bbox.y + bbox.height/2 };
                    """, zone)
                    zone_positions.append({'element': zone, 'position': pos})
                except Exception as e:
                    print(f"⚠️ 获取座位区域位置失败: {e}")
                    continue
            
            if len(zone_positions) == 0:
                print("❌ 无法获取座位区域位置信息")
                return False
            
            # 获取SVG边界以计算中心位置
            svg_bounds = self.driver.execute_script("""
                const svg = document.querySelector('#iez_canvas svg');
                let centerX = 0;
                try {
                    const vb = svg.viewBox.baseVal;
                    centerX = vb.width / 2;
                } catch(e) {
                    // 如果viewBox不可用，使用SVG的宽度
                    centerX = parseFloat(svg.getAttribute('width') || '1225') / 2;  
                }
                return { centerX: centerX };
            """)
            
            # 按前排中间优先排序：Y坐标权重*2 + 距离中心的X坐标距离
            zone_positions.sort(key=lambda x: x['position']['centerY'] * 2 + abs(x['position']['centerX'] - svg_bounds['centerX']))
            
            # 尝试所有区域直到找到可用座位
            total_zones = len(zone_positions)
            print(f"🔄 将依次尝试所有 {total_zones} 个区域")
            
            for attempt in range(total_zones):
                selected_zone = zone_positions[attempt]['element']
                zone_pos = zone_positions[attempt]['position']
                print(f"🎯 尝试区域 {attempt + 1}/{total_zones} (Y: {zone_pos['centerY']:.1f}, X: {zone_pos['centerX']:.1f})")
                
                # 点击区域
                try:
                    self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));", selected_zone)
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"⚠️ 点击区域 {attempt + 1} 失败: {e}")
                    continue
                
                # 检查是否有可用座位
                try:
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ez_canvas svg')))
                    seat_result = self.driver.execute_script("""
                        const rects = document.querySelectorAll('#ez_canvas svg rect');
                        const availableSeats = Array.from(rects).filter(rect => {
                            const fill = rect.getAttribute('fill');
                            const opacity = rect.getAttribute('opacity') || '1';
                            const display = rect.getAttribute('display') || 'block';
                            return fill !== '#DDDDDD' && fill !== 'none' && opacity !== '0' && display !== 'none';
                        });
                        
                        if (availableSeats.length > 0) {
                            // 选择第一个可用座位
                            availableSeats[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                            return { success: true, count: availableSeats.length };
                        }
                        return { success: false, count: 0 };
                    """)
                    
                    if seat_result['success']:
                        print(f"✅ 区域 {attempt + 1} 找到 {seat_result['count']} 个可用座位，已成功选择座位")
                        await asyncio.sleep(1)  # 等待座位选择生效
                        return True
                    else:
                        print(f"⚠️ 区域 {attempt + 1} 无可用座位，继续尝试下一个区域")
                    
                except Exception as e:
                    print(f"⚠️ 区域 {attempt + 1} 座位画布未加载或选择失败: {e}")
                    continue
            
            print(f"❌ 已尝试所有 {total_zones} 个区域，均无可用座位，可能原因：演出票已售罄或座位被占用")
            return False
            
        except Exception as e:
            print(f"❌ 选择座位区域和座位失败: {e}")
            return False

    async def execute_reservation(self):
        """执行完整的预约流程"""
        try:
            print("⏰ 开始选择时间...")
            # self.driver.refresh()
            self._close_notice_popup_if_present()
            
            wait = WebDriverWait(self.driver, 20)

            # 选择日期
            print("🔍 正在查找日期选择器...")
            date_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#list_date li button')))
            print("🖱️ 正在点击日期...")
            self._click_with_alert_handling(date_button)
            self._check_and_close_alert()
            print("✅ 日期点击完成")

            # 等待时间列表更新
            print("⏳ 等待时间列表更新...")
            await asyncio.sleep(2)

            # 选择时间
            print("🔍 正在查找时间选择器...")
            time_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#list_time li button')))
            print("🖱️ 正在点击时间...")
            self._click_with_alert_handling(time_button)
            self._check_and_close_alert()
            print("✅ 时间点击完成")

            print("🔍 正在查找预约按钮...")
            original_window = self.driver.current_window_handle
            print(f"🔍 原始窗口句柄: {original_window}")
            
            reservation_button = wait.until(EC.element_to_be_clickable((By.ID, 'ticketReservation_Btn')))
            self._click_with_alert_handling(reservation_button)
            print("✅ 已点击预约按钮")

            print("🔍 等待新窗口出现...")
            # 更强健的窗口检测逻辑
            max_wait_time = 15
            popup_window = None
            for i in range(max_wait_time):
                current_windows = self.driver.window_handles
                print(f"🔍 当前窗口数量: {len(current_windows)}")
                
                if len(current_windows) > 1:
                    popup_window = next((w for w in current_windows if w != original_window), None)
                    if popup_window:
                        print(f"✅ 找到弹窗句柄: {popup_window}")
                        break
                
                await asyncio.sleep(1)
            
            if not popup_window:
                print("❌ 未检测到弹窗，可能弹窗未正确打开")
                self._take_debug_screenshot("no_popup_detected")
                return False
            
            print("🔄 切换到弹窗...")
            self.driver.switch_to.window(popup_window)
            
            # 等待弹窗内容加载，检查多个可能的标识元素
            print("⏳ 等待弹窗内容加载...")
            popup_loaded = False
            for element_id in ['captchaEncStr', 'imgCaptcha', 'txtCaptcha', 'certification']:
                try:
                    wait.until(EC.presence_of_element_located((By.ID, element_id)))
                    print(f"✅ 弹窗加载完成 (检测到元素: {element_id})")
                    popup_loaded = True
                    break
                except:
                    continue
            
            if not popup_loaded:
                print("⚠️ 无法确认弹窗内容是否完全加载，继续尝试...")
            
            # 等待渲染完成
            await asyncio.sleep(3)
            self._take_debug_screenshot("popup_page")
            
            # 检查弹窗内容
            try:
                page_source_length = len(self.driver.page_source)
                print(f"📄 弹窗页面源码长度: {page_source_length}")
                
                if page_source_length < 100:
                    print("⚠️ 弹窗页面内容异常少，可能未正确加载")
                    self._take_debug_screenshot("popup_minimal_content")
                
            except Exception as e:
                print(f"⚠️ 无法获取页面源码: {e}")

            if not await self._handle_captcha():
                return False
            
            print("🎯 开始选座...")
            # 使用用户原始的智能选座逻辑，改写为Selenium版本
            success = await self._select_zone_and_seat()
            if not success:
                print("❌ 选座失败")
                return False
            
            print("🔍 切换到iframe...")
            iframe = wait.until(EC.presence_of_element_located((By.ID, 'oneStopFrame')))
            self.driver.switch_to.frame(iframe)

            print("✅ 已选择座位")

            print("💳 开始支付...")
            wait.until(EC.element_to_be_clickable((By.ID, 'nextTicketSelection'))).click()
            wait.until(EC.element_to_be_clickable((By.ID, 'nextPayment'))).click()
            
            phone_parts = Config.PHONE.split('-')
            wait.until(EC.presence_of_element_located((By.ID, 'tel1'))).send_keys(phone_parts[0])
            self.driver.find_element(By.ID, 'tel2').send_keys(phone_parts[1])
            self.driver.find_element(By.ID, 'tel3').send_keys(phone_parts[2])
            
            self.driver.find_element(By.ID, 'payMethodCode003').click()
            self.driver.find_element(By.ID, 'cashReceiptIssueCode3').click()
            self.driver.execute_script("document.querySelector('select[name=\"bankCode\"]').value = '88';")
            
            self.driver.find_element(By.ID, 'chkAgreeAll').click()
            self.driver.find_element(By.ID, 'btnFinalPayment').click()
            print("🎉 最终支付已提交！")

            await asyncio.sleep(10)
            return True
            
        except Exception as e:
            print(f"❌ 预约流程失败: {e}")
            self._take_debug_screenshot("reservation_failure")
            return False
