import base64
from io import BytesIO
from PIL import Image
import ddddocr

class CaptchaHandler:
    """验证码处理器"""
    
    def __init__(self):
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