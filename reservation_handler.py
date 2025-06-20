import asyncio
import base64
from io import BytesIO
from PIL import Image
import ddddocr
import os
from datetime import datetime
from config import Config

class ReservationHandler:
    """预约处理器"""
    
    def __init__(self, browser=None):
        self.browser = browser
        self.page = None
        self.iframe_element = None
        self.ocr = ddddocr.DdddOcr(show_ad=False)
    
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

    async def close_popup_dialogs(self, page):
        """检测并关闭提示弹窗"""
        try:
            print("🔍 检测提示弹窗...")
            
            # 查找并点击关闭按钮
            closed = await page.evaluate('''() => {
                const closeBtn = document.getElementById('noticeAlert_layerpopup_close');
                if (closeBtn && closeBtn.offsetParent !== null) {
                    closeBtn.click();
                    console.log('点击了noticeAlert关闭按钮');
                    return true;
                }
                return false;
            }''')
            
            if closed:
                print("✅ 关闭了noticeAlert弹窗")
                await page.waitFor(300)
            else:
                print("ℹ️ 未发现noticeAlert弹窗")
                
        except Exception as e:
            print(f"⚠️ 关闭弹窗时出错: {e}")

    async def complete_reservation_flow(self):
        """完整的预约流程：选择时间 -> 获取弹窗 -> 验证码 -> iframe -> 选座 -> 支付"""
        try:
            # 第1步：选择时间（选择日期时间并点击预约按钮）
            print("⏰ 开始选择时间流程...")
            
            # 获取当前页面URL并刷新页面（预约时间到了界面会变化）
            current_url = self.page.url
            print(f"🔄 当前页面: {current_url}")
            print("🔄 刷新页面以获取最新的时间选择状态...")
            await self.page.reload({'waitUntil': 'domcontentloaded'})
            print("✅ 页面刷新完成")
            
            # 关闭可能出现的提示弹窗
            await self.close_popup_dialogs(self.page)
            
            # 等待并点击日期列表第一个选项
            try:
                await self.page.waitForSelector('#list_date li:first-child', {'timeout': 5000})
                await self.page.click('#list_date li:first-child')
                print("✅ 已选择日期")
            except:
                print("❌ 选择时间失败: 未找到可选择的日期选项")
                return False
            
            # 等待并点击时间列表第一个选项
            try:
                await self.page.waitForSelector('#list_time li:first-child', {'timeout': 5000})
                await self.page.click('#list_time li:first-child')
                print("✅ 已选择时间")
            except:
                print("❌ 选择时间失败: 未找到可选择的时间选项")
                return False
            
            # 等待并点击预约按钮
            try:
                await self.page.waitForSelector('#ticketReservation_Btn', {'timeout': 5000})
                await self.page.click('#ticketReservation_Btn')
                print("✅ 已点击预约按钮")
            except:
                print("❌ 选择时间失败: 未找到预约按钮或按钮不可点击")
                return False
            
            print("✅ 时间选择完成，预约请求已发送")
            
            # 第2步：获取弹窗页面
            popup_page = await self._find_popup_page()
            if not popup_page:
                print("❌ 获取弹窗页面失败")
                return False
            
            # 对弹窗页面进行截图
            await self.take_debug_screenshot(popup_page, "popup_page")
            
            # 第3步：处理验证码 (恢复内联实现)
            print("🔍 处理验证码...")
            captcha_verified = True
            # for attempt in range(10): # 最多重试5次
            #     try:
            #         await popup_page.waitForSelector('#captchaImg')
            #         captcha_src = await popup_page.evaluate('document.querySelector("#captchaImg").src')
            #         base64_data = captcha_src.split('base64,')[1]
            #         captcha_text = self.recognize(base64_data).upper()
            #         print(f"🔤 识别到验证码: {captcha_text}")
                    
            #         await popup_page.evaluate('document.querySelector("#label-for-captcha").value = ""')
            #         await popup_page.type('#label-for-captcha', captcha_text)
            #         await popup_page.click('#btnComplete')
            #         await popup_page.waitFor(1000)
                    
            #         certification_style = await popup_page.evaluate('document.querySelector("#certification").style.display')
            #         if certification_style == "none":
            #             print("✅ 验证码验证成功")
            #             captcha_verified = True
            #             break
            #         else:
            #             if attempt < 4:
            #                 await popup_page.click('#btnReload')
            #                 await popup_page.waitFor(1000)
            #     except Exception as e:
            #         print(f"验证码处理异常: {e}")
            #         if attempt < 4:
            #             try:
            #                 await popup_page.click('#btnReload')
            #                 await popup_page.waitFor(1000)
            #             except: pass
            
            if not captcha_verified:
                print("❌ 验证码处理失败，终止流程")
                return False
            
            # 第4步：获取iframe并进行所有后续操作
            print("🔍 获取iframe...")
            await popup_page.waitForSelector('#oneStopFrame', {'timeout': 30000})
            iframe_element = await popup_page.querySelector('#oneStopFrame')
            if not iframe_element:
                print("❌ 无法获取iframe元素")
                return False
            
            iframe_frame = await iframe_element.contentFrame()
            if not iframe_frame:
                print("❌ 无法获取iframe frame")
                return False
            print("✅ 已获取iframe")
            print(f"📄 初始 iframe_frame: {iframe_frame}")
            
            # 第5步：选择座位
            print("🎯 开始选择座位...")
            await iframe_frame.waitForSelector('#iez_canvas svg', {'timeout': 30000})
            print("✅ 座位区域画布已加载")
            
            # 获取所有可点击的座位区域并选择座位
            all_elements = await iframe_frame.querySelectorAll('#iez_canvas svg rect, #iez_canvas svg path')
            clickable_zones = []
            
            for element in all_elements:
                cursor_style = await iframe_frame.evaluate('''(el) => {
                    const event = new MouseEvent('mouseover', { bubbles: true, cancelable: true, view: window });
                    el.dispatchEvent(event);
                    return window.getComputedStyle(el).cursor;
                }''', element)
                if cursor_style == 'pointer':
                    clickable_zones.append(element)
            
            if len(clickable_zones) == 0:
                print("❌ 未找到可点击的座位区域")
                return False
            
            print(f"📍 找到 {len(clickable_zones)} 个可点击的座位区域")
            
            # 尝试选择座位
            seat_selected = False
            for attempt, zone in enumerate(clickable_zones):
                print(f"🎯 尝试区域 {attempt + 1}/{len(clickable_zones)}")
                await iframe_frame.evaluate('(el) => el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }))', zone)
                await asyncio.sleep(0.1)
                
                try:
                    await iframe_frame.waitForSelector('#ez_canvas svg', {'timeout': 5000})
                    seat_selected = await iframe_frame.evaluate('''() => {
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
                    }''')
                    
                    if seat_selected:
                        print("✅ 成功选择座位")
                        break
                except:
                    continue
            
            if not seat_selected:
                print("❌ 未能选择到座位")
                return False
            
            # 第6步：支付流程
            print("💳 开始支付流程...")
            
            # 点击下一步
            await iframe_frame.waitForSelector('#nextTicketSelection', {'timeout': 10000})
            await iframe_frame.click('#nextTicketSelection')

            await asyncio.sleep(3) # 等待内容开始加载

            # 在更新后的frame中等待元素出现
            await iframe_frame.waitForSelector("#nextPayment", {"timeout": 15000})
            print("✅ #nextPayment 元素已出现")
            
            # 点击下一步支付
            await iframe_frame.click("#nextPayment")
            print("✅ 已点击下一步支付")
            await asyncio.sleep(5)
            
            # 输入手机号
            print("📱 输入手机号...")
            phone = Config.PHONE
            phone_parts = phone.split('-')
            if len(phone_parts) == 3:
                await iframe_frame.waitForSelector('#tel1', {'timeout': 10000})
                await iframe_frame.type('#tel1', phone_parts[0])
                await iframe_frame.type('#tel2', phone_parts[1])
                await iframe_frame.type('#tel3', phone_parts[2])
                print(f"✅ 已输入手机号: {phone}")
                await asyncio.sleep(3)
            
            # 选择支付方式
            print("🔄 选择支付方式...")
            await iframe_frame.waitForSelector('#payMethodCode003', {'timeout': 10000})
            await iframe_frame.click('#payMethodCode003')
            await asyncio.sleep(3)
            
            await iframe_frame.waitForSelector('#cashReceiptIssueCode3', {'timeout': 10000})
            await iframe_frame.click('#cashReceiptIssueCode3')
            await asyncio.sleep(3)
            
            # 选择银行
            print("🔄 选择银行...")
            await iframe_frame.waitForSelector('select[name="bankCode"]', {'timeout': 10000})
            await iframe_frame.evaluate('''() => {
                const select = document.querySelector('select[name="bankCode"]');
                if (select) {
                    select.value = '88';
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }''')
            await asyncio.sleep(1)

            # 同意条款
            print("🔄 同意所有条款...")
            await iframe_frame.waitForSelector('#chkAgreeAll', {'timeout': 10000})
            await iframe_frame.click('#chkAgreeAll')
            await asyncio.sleep(1)
            
            # 最终支付
            print("🔄 点击最终支付...")
            await iframe_frame.waitForSelector('#btnFinalPayment', {'timeout': 10000})
            await self.take_element_screenshot(iframe_element, "before_final_payment")
            await iframe_frame.click('#btnFinalPayment')
            await asyncio.sleep(3)
            await self.take_element_screenshot(iframe_element, "finalPayment")
            
            print("🎉 完整预约流程执行成功！")
            return True
            
        except Exception as e:
            print(f"❌ 完整预约流程失败: {e}")
            return False

    async def _find_popup_page(self):
        """在浏览器中查找并返回当前的弹窗页面"""
        for attempt in range(10):
            await asyncio.sleep(1)
            pages = await self.browser.pages()
            for page in pages:
                if page != self.page:  # 排除主页面
                    url = page.url.lower()
                    try:
                        # 优先通过URL和关键元素来识别
                        is_popup = ('onestop' in url or 'popup' in url)
                        if is_popup and (await page.querySelector('#oneStopFrame') or await page.querySelector('#captchaImg')):
                            print(f"✅ 已找到弹窗页面: {page.url}")
                            return page
                    except Exception:
                        # 如果页面在检查时关闭，会抛出异常，忽略并继续
                        continue
            print(f"⏳ 等待弹窗页面... ({attempt + 1}/10)")
        return None

    async def take_debug_screenshot(self, page, filename_prefix):
        """调试用截图函数"""
        try:
            if page:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/app/data/{filename_prefix}_{timestamp}.png"
                
                # 设置更大的视口以确保完整截图
                await page.setViewport({'width': 1920, 'height': 1080})
                
                # 等待页面完全加载
                await page.waitFor(1000)
                
                # 高质量全页面截图
                await page.screenshot({
                    'path': screenshot_path, 
                    'fullPage': True,
                    'quality': 95,
                    'type': 'png'
                })
                print(f"📸 截图已保存: {screenshot_path}")
                return screenshot_path
        except Exception as e:
            print(f"❌ 截图失败: {e}")
            return None

    async def take_element_screenshot(self, element, filename_prefix):
        """对指定的ElementHandle进行截图"""
        try:
            if element:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/app/data/{filename_prefix}_{timestamp}.png"
                
                await asyncio.sleep(1)
                
                await element.screenshot({
                    'path': screenshot_path,
                    'quality': 95,
                    'type': 'png'
                })
                print(f"📸 元素截图已保存: {screenshot_path}")
                return screenshot_path
        except Exception as e:
            print(f"❌ 元素截图失败: {e}")
            return None

    async def execute_reservation(self):
        """执行完整的预约流程"""
        return await self.complete_reservation_flow()
