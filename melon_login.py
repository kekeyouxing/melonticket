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

class MelonLogin:
    """Melon自动登录类"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.iframe_element = None  # 存储iframe元素
        
    async def init_browser(self):
        """初始化浏览器"""
        self.browser = await launch(
            headless=Config.HEADLESS_MODE,
            executablePath='/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--start-maximized',  # 启动时最大化窗口
                '--disable-web-security',  # 禁用web安全
                '--disable-features=VizDisplayCompositor'  # 改善渲染
            ],
            defaultViewport=None  # 使用完整窗口大小
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
                
    async def login(self):
        """执行登录流程"""
        try:
            # 验证配置
            Config.validate()
            
            # 初始化浏览器
            await self.init_browser()
            self.page = await self.browser.newPage()
            
            # 设置视口大小为常见的全屏分辨率
            await self.page.setViewport({'width': 1920, 'height': 1080})
            
            # 尝试加载已保存的cookies
            cookies_loaded = await self.load_cookies()
            
            if cookies_loaded:
                # 验证cookies是否有效
                print("🔍 验证已保存的登录状态...")
                await self.page.goto(Config.MELON_BASE_URL, {'waitUntil': 'domcontentloaded'})
                
                if "login" not in self.page.url.lower():
                    print("✅ 使用已保存的cookies登录成功！")
                    return True
                else:
                    print("⚠️ 已保存的cookies已失效，需要重新登录")
            
            # 执行登录流程
            print("🔐 开始登录流程...")
            await self.page.goto(Config.MELON_LOGIN_URL, {'waitUntil': 'domcontentloaded'})
            
            # 等待登录按钮加载
            await self.page.waitForSelector('#btnLogin', {'timeout': 10000})
            
            # 输入用户名和密码
            await self.page.type('#id', Config.USERNAME)
            print("✅ 已输入用户名")
            
            await self.page.type('#pwd', Config.PASSWORD)
            print("✅ 已输入密码")
            
            # 点击登录按钮
            await self.page.click('#btnLogin')
            print("🔄 正在登录...")
            
            # 等待页面跳转
            await asyncio.sleep(3)
            
            # 检查登录结果
            current_url = self.page.url
            if "login" in current_url.lower():
                print("❌ 登录失败，请检查用户名和密码")
                return False
            else:
                print("✅ 登录成功！")
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
            await self.page.waitForSelector('#list_date li:first-child')
            await self.page.click('#list_date li:first-child')
            print("✅ 已选择日期")
            
            # 等待并点击时间列表第一个选项
            await self.page.waitForSelector('#list_time li:first-child')
            await self.page.click('#list_time li:first-child')
            print("✅ 已选择时间")
            
            # 等待并点击预约按钮
            await self.page.waitForSelector('#ticketReservation_Btn')
            await self.page.click('#ticketReservation_Btn')
            print("✅ 已点击预约按钮")
            
            return True
        except Exception as e:
            print(f"❌ 预约过程中发生错误: {e}")
            return False
    
    async def get_popup_page(self):
        """获取弹窗页面"""
        await asyncio.sleep(2)
        pages = await self.browser.pages()
        for page in pages:
            if 'onestop.htm' in page.url:
                print("✅ 已获取弹窗页面")
                return page
        print("⚠️ 未找到弹窗页面")
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
        
        print(f"❌ 验证码处理失败，已重试{max_retries}次")
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
    
    async def select_seat_zone(self, iframe_element):
        """选择座位区域"""
        try:
            print("🎯 开始选择座位区域...")
            
            if not iframe_element:
                print("❌ iframe_element为空")
                return False
            
            # 获取iframe的contentFrame
            iframe_frame = await iframe_element.contentFrame()
            if not iframe_frame:
                print("❌ 无法获取iframe frame")
                return False
            
            # 在iframe内等待座位区域画布加载
            await iframe_frame.waitForSelector('#ez_canvas_zone svg', {'timeout': 30000})
            print("✅ 座位区域画布已加载")
            
            # 使用原生API获取所有rect元素
            rect_elements = await iframe_frame.querySelectorAll('#ez_canvas_zone svg rect')
            path_elements = await iframe_frame.querySelectorAll('#ez_canvas_zone svg path')
            
            print(f"📍 找到 {len(rect_elements)} 个rect元素和 {len(path_elements)} 个path元素")
            
            # 合并所有元素
            all_elements = rect_elements + path_elements
            
            if len(all_elements) == 0:
                print("❌ 未找到任何SVG元素")
                return False
            
                        # 过滤可点击元素（检查cursor:pointer）
            clickable_elements = []
            for element in all_elements:
                # 检查元素的cursor样式
                cursor_style = await iframe_frame.evaluate('''(el) => {
                    // 模拟hover来检查cursor
                    const event = new MouseEvent('mouseover', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    el.dispatchEvent(event);
                    
                    // 获取计算后的样式
                    const computedStyle = window.getComputedStyle(el);
                    return computedStyle.cursor;
                }''', element)
                
                if cursor_style == 'pointer':
                    clickable_elements.append(element)
            
            if len(clickable_elements) == 0:
                print("❌ 未找到可点击的座位区域")
                return False
            
            print(f"📍 找到 {len(clickable_elements)} 个可点击的座位区域")
            
            # 随机选择一个可点击的元素
            selected_element = random.choice(clickable_elements)
            
            # 获取元素信息用于日志
            tag_name = await iframe_frame.evaluate('(element) => element.tagName', selected_element)
            fill_color = await iframe_frame.evaluate('(el) => el.getAttribute("fill")', selected_element)
            print(f"🎯 随机选择: 类型 {tag_name}, 颜色 {fill_color}")
            
            # 直接在元素上模拟点击事件 - 点击两次
            await iframe_frame.evaluate('''(element) => {
                // 创建鼠标点击事件
                const mouseEvent = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                 
                // 第一次点击
                element.dispatchEvent(mouseEvent);
            }''', selected_element)
            
            await asyncio.sleep(0.1)  # 稍微等待一下
            
            # 等待页面响应
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ 选择座位区域失败: {e}")
            return False
    

    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()

async def main():
    """主函数"""
    login_manager = MelonLogin()
    
    try:
        success = await login_manager.login()
        
        if success:
            print("🎉 登录完成！")
            
            # 执行预约流程
            reserve_success = await login_manager.reserve_ticket()
            
            if reserve_success:
                print("🎉 预约流程完成！")
                
                # 获取弹窗页面
                popup_page = await login_manager.get_popup_page()
                
                if popup_page:
                    print("🎉 已获取弹窗页面，可以继续操作")
                    
                    # 处理验证码
                    captcha_success = await login_manager.handle_captcha(popup_page)
                    if captcha_success:
                        print("🎉 验证码处理完成！")
                        
                        # 获取iframe
                        iframe_element = await login_manager.get_iframe(popup_page)
                        if iframe_element:
                            print("🎉 已获取iframe，可以继续操作")
                            
                            # 选择座位区域
                            zone_success = await login_manager.select_seat_zone(iframe_element)
                            if zone_success:
                                print("🎉 座位区域选择完成！")
                            else:
                                print("💔 座位区域选择失败")
                        else:
                            print("💔 获取iframe失败")
                    else:
                        print("💔 验证码处理失败")
                
            else:
                print("💔 预约失败")
                
            input("按回车键关闭浏览器...")
        else:
            print("💔 登录失败")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
    finally:
        await login_manager.close()
        print("👋 浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 