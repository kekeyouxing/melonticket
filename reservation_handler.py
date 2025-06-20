import asyncio
from config import Config

class ReservationHandler:
    """预约处理器"""
    
    def __init__(self, browser=None):
        self.browser = browser
        self.page = None
        self.iframe_element = None
    
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