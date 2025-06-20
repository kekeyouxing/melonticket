import asyncio
import json
import os
import base64
import random
from io import BytesIO
from PIL import Image
import ddddocr
from pyppeteer import launch
from config import Config
from datetime import datetime, timedelta
import time
import schedule
import threading

class MelonTicketService:
    """Melon票务定时服务"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.iframe_element = None
        self.is_logged_in = False
        self.service_running = True
        self.login_completed = False
        self.reservation_completed = False
        self._event_loop = None  # 共享事件循环
        
        # 确保数据目录存在
        data_dir = "/app/data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def setup_scheduler(self):
        """设置精确定时调度"""
        print("🍈 Melon票务定时服务启动")
        print("=" * 50)
        
        # 解析时间
        login_time = datetime.strptime(Config.LOGIN_TIME, '%Y-%m-%d %H:%M:%S')
        reservation_time = datetime.strptime(Config.RESERVATION_START_TIME, '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        
        # 检查时间是否已过期
        if reservation_time <= current_time:
            print(f"⚠️ 预约时间已过期: {Config.RESERVATION_START_TIME}")
            print("❌ 服务退出")
            return False
        
        # 设置登录任务
        if login_time > current_time:
            login_time_str = login_time.strftime('%H:%M:%S')
            schedule.every().day.at(login_time_str).do(self.execute_login_job).tag('login')
            print(f"📅 登录任务已设置: {Config.LOGIN_TIME}")
        else:
            print(f"⚠️ 登录时间已过期，将在预约时直接登录")
        
        # 设置预约任务
        reservation_time_str = reservation_time.strftime('%H:%M:%S')
        schedule.every().day.at(reservation_time_str).do(self.execute_reservation_job).tag('reservation')
        print(f"📅 预约任务已设置: {Config.RESERVATION_START_TIME}")
        
        print("=" * 50)
        print("⏰ 定时服务运行中，等待执行时间...")
        return True
    
    def execute_login_job(self):
        """执行登录任务 - schedule回调"""
        print("⏰ 登录时间到！开始执行登录任务...")
        try:
            # 创建共享事件循环（只创建一次）
            if not hasattr(self, '_event_loop') or self._event_loop is None or self._event_loop.is_closed():
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
                print("🔄 创建新的事件循环用于整个会话")
            
            success = self._event_loop.run_until_complete(self.login_task())
            
            if success:
                self.login_completed = True
                self.is_logged_in = True
                # 取消登录任务，避免重复执行
                schedule.clear('login')
            else:
                print("❌ 登录任务执行失败")
                self._cleanup_and_stop()
        except Exception as e:
            print(f"❌ 登录任务执行异常: {e}")
            self._cleanup_and_stop()
    
    def execute_reservation_job(self):
        """执行预约任务 - schedule回调"""
        print("⏰ 预约时间到！开始执行预约任务...")
        try:
            # 检查是否已登录
            if not self.login_completed:
                print("❌ 登录任务未完成，无法执行预约")
                self._cleanup_and_stop()
                return
            
            # 使用已存在的事件循环（不创建新的）
            if not hasattr(self, '_event_loop') or self._event_loop is None or self._event_loop.is_closed():
                print("❌ 事件循环不可用，无法执行预约")
                self._cleanup_and_stop()
                return
            
            success = self._event_loop.run_until_complete(self.reservation_task())
            
            if success:
                self.reservation_completed = True
                print("✅ 预约任务执行完成")
            else:
                print("❌ 预约任务执行失败")
                
            # 无论成功失败，预约任务完成后都清理资源
            self._cleanup_and_stop()
                
        except Exception as e:
            print(f"❌ 预约任务执行异常: {e}")
            self._cleanup_and_stop()
    
    def _cleanup_and_stop(self):
        """清理资源并停止服务"""
        print("🧹 开始清理资源...")
        schedule.clear()
        self.service_running = False
        
        # 清理浏览器和事件循环
        try:
            if self._event_loop and not self._event_loop.is_closed():
                if self.browser:
                    print("🔒 关闭浏览器...")
                    self._event_loop.run_until_complete(self.browser.close())
                print("🔒 关闭事件循环...")
                self._event_loop.close()
        except Exception as e:
            print(f"⚠️ 清理资源时出错: {e}")
        
        self._event_loop = None
        self.browser = None
        self.page = None
    
    def run_scheduler(self):
        """运行定时调度器"""
        while self.service_running:
            schedule.run_pending()
            time.sleep(1)  # 每秒检查一次，确保精确度
        
        print("🎉 定时服务执行完成")
    
    async def login_task(self):
        """登录任务 - 初始化浏览器并登录"""
        print("🔐 执行登录任务...")
        try:
            # 初始化浏览器（如果还未初始化）
            if not self.browser:
                print("🌐 初始化浏览器...")
                await self.init_browser()
                self.page = await self.browser.newPage()
                await self.page.setViewport({'width': 1920, 'height': 1080})
                print("✅ 浏览器初始化完成")
            
            # 执行登录
            success = await self.login()
            if success:
                print("✅ 登录任务完成，会话已建立")
                return True
            else:
                print("❌ 登录任务失败")
                return False
        except Exception as e:
            print(f"❌ 登录任务出错: {e}")
            return False
    
    async def reservation_task(self):
        """预约任务 - 基于已登录状态执行预约"""
        print("🎫 执行预约任务...")
        try:
            # 验证浏览器和页面是否可用
            if not self.browser or not self.page:
                print("❌ 浏览器会话不可用")
                return False
            
            # 验证登录状态
            if not self.is_logged_in:
                print("❌ 未登录状态，无法执行预约")
                return False
            
            print("✅ 使用已建立的浏览器会话执行预约...")
            
            # 执行预约流程（跳过登录步骤）
            success = await self.execute_reservation_flow(skip_login=True)
            if success:
                print("✅ 预约任务完成")
                return True
            else:
                print("❌ 预约任务失败")
                return False
        except Exception as e:
            print(f"❌ 预约任务出错: {e}")
            return False
    
    async def stop_service(self):
        """停止服务"""
        self.service_running = False
        schedule.clear()
        if self.browser:
            await self.browser.close()
        print("🛑 定时服务已停止")
        
    # 以下是原有的业务逻辑方法，保持不变
    async def init_browser(self):
        """初始化浏览器（Docker环境）"""
        browser_args = [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--window-size=1920,1080'
        ]
        
        executable_path = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        
        self.browser = await launch(
            headless=False,  # 调试期间关闭无头模式以支持截图
            executablePath=executable_path,
            args=browser_args,
            defaultViewport=None
        )
        
    async def load_cookies(self):
        """加载已保存的cookies"""
        if os.path.exists(Config.COOKIE_FILE):
            try:
                with open(Config.COOKIE_FILE, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    if cookies and self.page:
                        await self.page.setCookie(*cookies)
                        print("✅ 成功加载已保存的cookies")
                        return True
            except Exception as e:
                print(f"❌ 加载cookies失败: {e}")
        return False
        
    async def save_cookies(self):
        """保存cookies到本地文件"""
        if self.page:
            try:
                cookies = await self.page.cookies()
                with open(Config.COOKIE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print(f"✅ cookies已保存到 {Config.COOKIE_FILE}")
            except Exception as e:
                print(f"❌ 保存cookies失败: {e}")
    
    async def take_debug_screenshot(self, filename_prefix):
        """调试用截图函数"""
        try:
            if self.page:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/app/data/{filename_prefix}_{timestamp}.png"
                await self.page.screenshot({'path': screenshot_path, 'fullPage': True})
                print(f"📸 截图已保存: {screenshot_path}")
                return screenshot_path
        except Exception as e:
            print(f"❌ 截图失败: {e}")
        return None

    async def save_page_content(self, filename_prefix):
        """保存页面HTML内容用于调试"""
        try:
            if self.page:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                html_path = f"/app/data/{filename_prefix}_{timestamp}.html"
                content = await self.page.content()
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"📄 页面内容已保存: {html_path}")
                return html_path
        except Exception as e:
            print(f"❌ 保存页面内容失败: {e}")
        return None
                
    async def login(self):
        """执行登录流程"""
        try:
            # 验证配置
            Config.validate()
            
            # 验证浏览器和页面是否已初始化
            if not self.browser or not self.page:
                print("❌ 浏览器未初始化")
                return False
            
            # 首先尝试加载已保存的cookies
            cookies_loaded = await self.load_cookies()
            if cookies_loaded:
                print("🔄 尝试使用已保存的cookies...")
                # 直接访问基础URL检查cookies是否有效
                await self.page.goto(Config.MELON_BASE_URL)
                await asyncio.sleep(2)
                
                # 检查是否已经登录成功
                current_url = self.page.url
                print(f"🔍 当前URL: {current_url}")
                if "login" not in current_url.lower():
                    print("✅ 使用已保存的cookies登录成功")
                    return True
                else:
                    print("❌ 已保存的cookies已失效")
            
            # cookies无效或不存在，执行登录流程
            print("🔐 开始登录...")
            print(f"🔗 访问登录URL: {Config.MELON_LOGIN_URL}")
            
            # 添加重试机制处理网站访问延迟
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.page.goto(Config.MELON_LOGIN_URL)
                    await asyncio.sleep(3)  # 等待页面加载
                    
                    # 调试：截图当前登录页面状态
                    await self.take_debug_screenshot("login_page")
                    
                    current_url = self.page.url
                    print(f"🔍 实际访问的URL: {current_url}")
                    
                    # 检查页面内容，看是否遇到访问延迟页面
                    page_content = await self.page.content()
                    if "访问页面使用率过高" in page_content or "访问延迟" in page_content:
                        print(f"⚠️  网站访问量过高，等待后重试... (第{attempt + 1}次)")
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 30  # 递增等待时间
                            print(f"⏳ 等待 {wait_time} 秒...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print("❌ 多次重试仍无法访问登录页面，网站可能暂时不可用")
                            return False
                    
                    # 等待登录按钮元素出现，表示登录页面已加载
                    print("⏳ 等待登录按钮出现...")
                    await self.page.waitForSelector('#btnLogin', {'timeout': 15000})
                    print("✅ 登录页面加载成功")
                    break
                    
                except Exception as e:
                    print(f"❌ 访问登录页面失败 (第{attempt + 1}次): {e}")
                    if attempt < max_retries - 1:
                        print("🔄 30秒后重试...")
                        await asyncio.sleep(30)
                    else:
                        raise e
            
            # 输入用户名和密码
            print("🔑 输入登录凭据...")
            await self.page.type('#id', Config.USERNAME)
            await self.page.type('#pwd', Config.PASSWORD)
            
            # 点击登录按钮
            await self.page.click('#btnLogin')
            print("✅ 已点击登录按钮")
            
            # 等待页面跳转
            await asyncio.sleep(5)
            
            # 调试：登录后截图
            await self.take_debug_screenshot("after_login")
            
            # 检查登录结果
            current_url = self.page.url
            print(f"🔍 登录后URL: {current_url}")
            
            if "login" in current_url.lower():
                print(f"❌ 登录失败: {current_url}")
                return False
            else:
                print("✅ 登录成功")
                await self.save_cookies()
                return True
                
        except Exception as e:
            print(f"❌ 登录过程中发生错误: {e}")
            return False
            
    async def reserve_ticket(self):
        """预约票务"""
        try:
            print("🎫 开始预约流程...")
            await self.page.goto(Config.MELON_BASE_URL, {'waitUntil': 'domcontentloaded'})
            
            # 关闭可能出现的提示弹窗
            await self.close_popup_dialogs(self.page)
            
            # 等待并点击日期列表第一个选项
            try:
                await self.page.waitForSelector('#list_date li:first-child', {'timeout': 5000})
                await self.page.click('#list_date li:first-child')
                print("✅ 已选择日期")
            except:
                print("❌ 预约失败: 未找到可选择的日期选项")
                return False
            
            # 等待并点击时间列表第一个选项
            try:
                await self.page.waitForSelector('#list_time li:first-child', {'timeout': 5000})
                await self.page.click('#list_time li:first-child')
                print("✅ 已选择时间")
            except:
                print("❌ 预约失败: 未找到可选择的时间选项")
                return False
            
            # 等待并点击预约按钮
            try:
                await self.page.waitForSelector('#ticketReservation_Btn', {'timeout': 5000})
                await self.page.click('#ticketReservation_Btn')
                print("✅ 已点击预约按钮")
            except:
                print("❌ 预约失败: 未找到预约按钮或按钮不可点击")
                return False
            
            return True
        except Exception as e:
            print(f"❌ 预约过程中发生错误: {e}")
            return False
    
    async def get_popup_page(self, max_wait_time=10):
        """获取弹窗页面，增加重试机制"""
        print("🔍 等待弹窗页面打开...")
        
        for attempt in range(max_wait_time):
            await asyncio.sleep(1)
            pages = await self.browser.pages()
            
            # 查找新打开的页面（不是主页面的其他页面）
            for page in pages:
                if page != self.page:
                    url = page.url.lower()
                    # 检查URL是否包含相关关键词
                    if ('onestop' in url or 'popup' in url or 'reservation' in url or 'ticket' in url):
                        print(f"✅ 已获取弹窗页面: {page.url}")
                        return page
                    
                    # 如果URL不明确，尝试检查页面内容
                    try:
                        # 等待验证码元素出现，如果出现说明是正确的弹窗页面
                        await page.waitForSelector('#captchaImg', {'timeout': 1000})
                        print(f"✅ 通过验证码元素确认弹窗页面: {page.url}")
                        return page
                    except:
                        # 检查iframe元素
                        try:
                            await page.waitForSelector('#oneStopFrame', {'timeout': 1000})
                            print(f"✅ 通过iframe元素确认弹窗页面: {page.url}")
                            return page
                        except:
                            continue
            
            print(f"⏳ 等待弹窗页面... ({attempt + 1}/{max_wait_time})")
        
        print("⚠️ 未找到弹窗页面，可能需要手动检查")
        return None
    
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

    async def handle_captcha(self, popup_page):
        """处理验证码，支持重试机制"""
        max_retries = 5  # 最大重试次数
        
        for attempt in range(max_retries):
            try:
                print(f"🔍 开始处理验证码... (第{attempt + 1}次尝试)")
                
                # 等待验证码图片加载
                await popup_page.waitForSelector('#captchaImg')
                
                # 获取验证码图片的base64数据
                captcha_src = await popup_page.evaluate('document.querySelector("#captchaImg").src')
                
                # 提取base64数据部分
                base64_data = captcha_src.split('base64,')[1]
                
                # 使用OCR识别文字
                captcha_text = self.recognize(base64_data).upper()
                
                print(f"🔤 识别到验证码: {captcha_text}")
                
                # 清空并填入验证码
                await popup_page.evaluate('document.querySelector("#label-for-captcha").value = ""')
                await popup_page.type('#label-for-captcha', captcha_text)
                print("✅ 已填入验证码")
                
                # 点击完成按钮
                await popup_page.click('#btnComplete')
                print("✅ 已点击完成按钮")
                
                # 等待一下，检查验证码是否成功
                await popup_page.waitFor(1000)
                
                # 检查验证码验证是否成功 (certification元素是否隐藏)
                certification_style = await popup_page.evaluate('document.querySelector("#certification").style.display')
                
                if certification_style == "none":
                    print("🎉 验证码验证成功！")
                    return True
                else:
                    print(f"❌ 验证码验证失败，准备重试... (剩余{max_retries - attempt - 1}次)")
                    
                    # 如果不是最后一次尝试，点击刷新按钮获取新验证码
                    if attempt < max_retries - 1:
                        await popup_page.click('#btnReload')
                        print("🔄 已刷新验证码")
                        # 等待新验证码加载
                        await popup_page.waitFor(1000)
                
            except Exception as e:
                print(f"❌ 验证码处理异常: {e}")
                
                # 如果不是最后一次尝试，点击刷新按钮获取新验证码
                if attempt < max_retries - 1:
                    try:
                        await popup_page.click('#btnReload')
                        print("🔄 已刷新验证码")
                        await popup_page.waitFor(1000)
                    except:
                        pass
        
        print(f"❌ 验证码处理失败，已重试{max_retries}次，可能原因：验证码识别不准确或网络延迟")
        return False
    
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

    async def get_iframe(self, popup_page):
        """获取iframe元素"""
        try:
            # 等待iframe加载
            await popup_page.waitForSelector('#oneStopFrame', {'timeout': 30000})
            print("✅ iframe已加载")
            
            # 获取iframe元素
            self.iframe_element = await popup_page.querySelector('#oneStopFrame')
            
            if not self.iframe_element:
                print("❌ 无法获取iframe元素")
                return None
            
            print("✅ 已获取iframe元素，现在可以通过self.iframe_element访问")
            return self.iframe_element
            
        except Exception as e:
            print(f"❌ 获取iframe失败: {e}")
            return None
    
    async def select_zone_and_seat(self, iframe_element):
        """选择座位区域并选择座位"""
        try:
            print("🎯 开始选择座位区域和座位...")
            
            if not iframe_element:
                print("❌ iframe_element为空")
                return False
            
            # 获取iframe的contentFrame
            iframe_frame = await iframe_element.contentFrame()
            if not iframe_frame:
                print("❌ 无法获取iframe frame")
                return False
            
            # 等待座位区域画布加载
            await iframe_frame.waitForSelector('#iez_canvas svg', {'timeout': 30000})
            print("✅ 座位区域画布已加载")
            
            # 获取所有可点击的座位区域
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
            
            # 按前排中间优先排序
            zone_positions = []
            for zone in clickable_zones:
                pos = await iframe_frame.evaluate('(el) => { const bbox = el.getBBox(); return { centerX: bbox.x + bbox.width/2, centerY: bbox.y + bbox.height/2 }; }', zone)
                zone_positions.append({'element': zone, 'position': pos})
            
            svg_bounds = await iframe_frame.evaluate('() => { const svg = document.querySelector("#iez_canvas svg"); const vb = svg.viewBox.baseVal; return { centerX: vb.width/2 }; }')
            zone_positions.sort(key=lambda x: x['position']['centerY'] * 2 + abs(x['position']['centerX'] - svg_bounds['centerX']))
            
            # 尝试所有区域直到找到可用座位
            total_zones = len(zone_positions)
            print(f"🔄 将依次尝试所有 {total_zones} 个区域")
            
            for attempt in range(total_zones):
                selected_zone = zone_positions[attempt]['element']
                zone_pos = zone_positions[attempt]['position']
                print(f"🎯 尝试区域 {attempt + 1}/{total_zones} (Y: {zone_pos['centerY']:.1f}, X: {zone_pos['centerX']:.1f})")
                
                # 点击区域
                await iframe_frame.evaluate('(el) => el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }))', selected_zone)
                await asyncio.sleep(1)
                
                # 检查是否有可用座位
                try:
                    await iframe_frame.waitForSelector('#ez_canvas svg', {'timeout': 5000})
                    available_seats = await iframe_frame.evaluate('''() => {
                        const rects = document.querySelectorAll('#ez_canvas svg rect');
                        return Array.from(rects).filter(rect => {
                            const fill = rect.getAttribute('fill');
                            return fill !== '#DDDDDD' && fill !== 'none';
                        }).length;
                    }''')
                    
                    if available_seats > 0:
                        print(f"✅ 区域 {attempt + 1} 找到 {available_seats} 个可用座位，开始选择")
                        # 选择第一个可用座位
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
                            return True
                    
                    print(f"⚠️ 区域 {attempt + 1} 无可用座位，继续尝试下一个区域")
                    
                except:
                    print(f"⚠️ 区域 {attempt + 1} 座位画布未加载，继续尝试下一个区域")
                    continue
            
            print(f"❌ 已尝试所有 {total_zones} 个区域，均无可用座位，可能原因：演出票已售罄或座位被占用")
            return False
            
        except Exception as e:
            print(f"❌ 选择座位区域和座位失败: {e}")
            return False

    async def proceed_to_payment(self, iframe_element):
        """进入支付流程"""
        try:
            print("💳 开始进入支付流程...")
            
            if not iframe_element:
                print("❌ iframe_element为空")
                return False
            
            # 获取iframe的contentFrame
            iframe_frame = await iframe_element.contentFrame()
            if not iframe_frame:
                print("❌ 无法获取iframe frame")
                return False
            
            # 1. 点击下一步按钮
            print("🔄 点击下一步...")
            try:
                await iframe_frame.waitForSelector('#nextTicketSelection', {'timeout': 10000})
                await iframe_frame.click('#nextTicketSelection')
                await asyncio.sleep(2)
                print("✅ 已点击下一步")
            except:
                print("❌ 支付流程失败: 未找到下一步按钮，可能座位选择不完整")
                return False
            
            # 2. 点击下一步支付
            print("🔄 点击下一步支付...")
            await iframe_frame.waitForSelector('#nextPayment', {'timeout': 10000})
            await iframe_frame.click('#nextPayment')
            await asyncio.sleep(2)
            print("✅ 已点击下一步支付")
            
            # 3. 输入手机号
            print("📱 输入手机号...")
            phone = Config.PHONE
            phone_parts = phone.split('-')
            
            if len(phone_parts) == 3:
                await iframe_frame.waitForSelector('#tel1', {'timeout': 10000})
                await iframe_frame.type('#tel1', phone_parts[0])
                await iframe_frame.type('#tel2', phone_parts[1])
                await iframe_frame.type('#tel3', phone_parts[2])
                print(f"✅ 已输入手机号: {phone}")
            else:
                print("❌ 手机号格式错误")
                return False
            
            await asyncio.sleep(1)
            # 5. 选择支付方式
            print("🔄 选择支付方式...")
            await iframe_frame.waitForSelector('#payMethodCode003', {'timeout': 10000})
            await iframe_frame.click('#payMethodCode003')
            await asyncio.sleep(1)
            print("✅ 已选择支付方式")
            
            await iframe_frame.waitForSelector('#cashReceiptIssueCode3', {'timeout': 10000})
            await iframe_frame.click('#cashReceiptIssueCode3')
            await asyncio.sleep(1)
            print("✅ 已选择现金收据选项")
            
            # 6. 选择银行（신한은행 - value: 88）
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
            print("✅ 已选择银行：신한은행")

            # 4. 点击同意所有条款
            print("🔄 同意所有条款...")
            await iframe_frame.waitForSelector('#chkAgreeAll', {'timeout': 10000})
            await iframe_frame.click('#chkAgreeAll')
            await asyncio.sleep(1)
            print("✅ 已同意所有条款")
            # 7. 点击最终支付按钮
            print("🔄 点击最终支付...")
            await iframe_frame.waitForSelector('#btnFinalPayment', {'timeout': 10000})
            await iframe_frame.click('#btnFinalPayment')
            await asyncio.sleep(1)
            print("✅ 已点击最终支付")
            
            print("🎉 支付流程完成！")
            return True
            
        except Exception as e:
            print(f"❌ 支付流程失败: {e}")
            return False
    
    async def execute_reservation_flow(self, skip_login=False):
        """执行预约流程"""
        try:
            if not skip_login:
                success = await self.login()
                if not success:
                    print("❌ 登录失败")
                    return False
            print("🎉 登录完成！")
            
            # 执行预约流程
            reserve_success = await self.reserve_ticket()
            
            if reserve_success:
                print("🎉 预约流程完成！")
                
                # 获取弹窗页面
                popup_page = await self.get_popup_page()
                
                if popup_page:
                    print("🎉 已获取弹窗页面，可以继续操作")
                    
                    # 处理验证码
                    captcha_success = await self.handle_captcha(popup_page)
                    if captcha_success:
                        print("🎉 验证码处理完成！")
                        
                        # 获取iframe
                        iframe_element = await self.get_iframe(popup_page)
                        if iframe_element:
                            print("🎉 已获取iframe，可以继续操作")
                            
                            # 选择座位区域和座位
                            success = await self.select_zone_and_seat(iframe_element)
                            if success:
                                print("🎉 座位选择完成！")
                                
                                # 进入支付流程
                                payment_success = await self.proceed_to_payment(iframe_element)
                                if payment_success:
                                    print("🎉 支付流程设置完成！")
                                    return True
                                else:
                                    print("💔 支付流程失败")
                            else:
                                print("💔 座位选择失败")
                        else:
                            print("💔 获取iframe失败")
                    else:
                        print("💔 验证码处理失败")
                else:
                    print("💔 获取弹窗页面失败")
            else:
                print("💔 预约失败")
                
            return False
            
        except Exception as e:
            print(f"❌ 预约流程执行失败: {e}")
            return False

def main():
    """主函数"""
    service = MelonTicketService()
    
    try:
        # 验证配置
        Config.validate()
        
        # 设置定时调度
        if not service.setup_scheduler():
            return
        
        print("🚀 定时服务启动中...")
        print(f"📅 登录时间: {Config.LOGIN_TIME}")
        print(f"🎫 预约时间: {Config.RESERVATION_START_TIME}")
        
        # 运行定时服务
        service.run_scheduler()
        
        print("🐳 Docker容器运行完成，自动关闭...")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
        if hasattr(service, '_cleanup_and_stop'):
            service._cleanup_and_stop()
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
    finally:
        print("👋 服务已关闭")

if __name__ == "__main__":
    main() 