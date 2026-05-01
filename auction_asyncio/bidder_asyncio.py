import asyncio
import json
import sys
import os
import time

class AsyncBidderClient:
    def __init__(self, host='localhost', port=9998):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.user_id = None
        self.user_name = None
        self.running = False
        self.state = None
        self.my_turn = False
        self.bid_duration = 5
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        print("="*60)
        print("              🏷️  拍卖竞标系统 - 竞标者端 (AsyncIO版)")
        print("="*60)
        print()
        
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
            
    async def send_message(self, message):
        try:
            self.writer.write((json.dumps(message, ensure_ascii=False) + '\n').encode('utf-8'))
            await self.writer.drain()
            return True
        except:
            return False
            
    async def receive_messages(self):
        buffer = b""
        while self.running:
            try:
                data = await asyncio.wait_for(self.reader.read(4096), timeout=0.1)
                if not data:
                    break
                    
                buffer += data
                while b'\n' in buffer:
                    line_bytes, buffer = buffer.split(b'\n', 1)
                    if not line_bytes:
                        continue
                    try:
                        line = line_bytes.decode('utf-8')
                        message = json.loads(line)
                        self.handle_message(message)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                        
            except asyncio.TimeoutError:
                continue
            except:
                break
                
        print("\n与服务器的连接已断开")
        self.running = False
        
    def handle_message(self, message):
        msg_type = message.get('type')
        
        if msg_type == 'joined':
            self.user_id = message.get('user_id')
            self.state = message.get('state')
            print(f"\n✅ {message.get('message')}")
            
        elif msg_type == 'user_joined':
            user_name = message.get('user_name')
            user_type = message.get('user_type')
            self.state = message.get('state')
            if user_type == 'bidder' and user_name != self.user_name:
                print(f"\n📢 竞标者 {user_name} 已加入拍卖")
            elif user_type == 'host':
                print(f"\n📢 主持人 {user_name} 已上线")
            
        elif msg_type == 'user_left':
            user_name = message.get('user_name')
            self.state = message.get('state')
            print(f"\n📢 {user_name} 已离开")
            
        elif msg_type == 'auction_started':
            self.state = message.get('state')
            print(f"\n🎉 拍卖已开始!")
            print(f"   拍卖品: {message.get('item_name')}")
            print(f"   起拍价: ¥{message.get('initial_price')}")
            print("\n请等待您的出价轮次...")
            
        elif msg_type == 'your_turn':
            self.state = message.get('state')
            self.my_turn = True
            self.bid_duration = message.get('bid_duration', 5)
            print(f"\n{'='*60}")
            print(f"                    ⏰ 轮到您出价了!")
            print(f"{'='*60}")
            print(f"\n当前价格: ¥{message.get('current_price')}")
            print(f"您有 {self.bid_duration} 秒时间出价")
            print(f"\n请输入出价金额 (输入 'pass' 放弃): ", end="")
            sys.stdout.flush()
            
        elif msg_type == 'bid_placed':
            self.state = message.get('state')
            bidder_name = message.get('bidder_name')
            price = message.get('price')
            if bidder_name == self.user_name:
                print(f"\n✅ 您的出价 ¥{price} 已成功!")
            else:
                print(f"\n💰 {bidder_name} 出价 ¥{price}")
            self.my_turn = False
            
        elif msg_type == 'bid_passed':
            self.state = message.get('state')
            bidder_name = message.get('bidder_name')
            if bidder_name == self.user_name:
                print(f"\n⏭️ 您已放弃出价，退出竞拍")
            else:
                print(f"\n⏭️ {bidder_name} 放弃出价，退出竞拍")
            self.my_turn = False
            
        elif msg_type == 'bid_timeout':
            self.state = message.get('state')
            bidder_name = message.get('bidder_name')
            if bidder_name == self.user_name:
                print(f"\n⏰ 您出价超时，已退出竞拍")
            else:
                print(f"\n⏰ {bidder_name} 出价超时，已退出竞拍")
            self.my_turn = False
            
        elif msg_type == 'auction_ended':
            self.state = message.get('state')
            winner_name = message.get('winner_name')
            final_price = message.get('final_price')
            item_name = message.get('item_name')
            
            print("\n" + "="*60)
            print("                    🎊 拍卖结束!")
            print("="*60)
            print(f"\n   拍卖品: {item_name}")
            print(f"   获胜者: {winner_name if winner_name else '无人'}")
            print(f"   成交价格: ¥{final_price}")
            
            if winner_name == self.user_name:
                print(f"\n   🎉 恭喜您赢得了拍卖!")
                
            print("\n" + "="*60)
            self.my_turn = False
            
        elif msg_type == 'state':
            self.state = message.get('state')
            
        elif msg_type == 'error':
            print(f"\n❌ 错误: {message.get('message')}")
            
        elif msg_type == 'bid_error':
            print(f"\n❌ 出价失败: {message.get('message')}")
            if self.my_turn:
                print(f"\n请重新输入出价金额 (输入 'pass' 放弃): ", end="")
                sys.stdout.flush()
            
    async def ainput(self, prompt):
        print(prompt, end="", flush=True)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sys.stdin.readline)
        
    async def start(self):
        self.clear_screen()
        self.print_header()
        
        print("请输入您的竞标者名称: ", end="", flush=True)
        self.user_name = sys.stdin.readline().strip()
        if not self.user_name:
            self.user_name = f"竞标者{int(time.time()) % 1000}"
            
        if not await self.connect():
            return
            
        await self.send_message({
            'type': 'join',
            'user_type': 'bidder',
            'user_name': self.user_name
        })
        
        self.running = True
        receive_task = asyncio.create_task(self.receive_messages())
        
        await asyncio.sleep(0.3)
        await self.main_loop(receive_task)
        
    async def main_loop(self, receive_task):
        print("\n欢迎加入拍卖! 等待拍卖开始...")
        print("提示: 当轮到您出价时，系统会提示您输入金额")
        
        while self.running:
            try:
                if self.my_turn:
                    loop = asyncio.get_event_loop()
                    try:
                        user_input = await asyncio.wait_for(
                            loop.run_in_executor(None, sys.stdin.readline),
                            timeout=0.1
                        )
                        user_input = user_input.strip()
                        if user_input:
                            if user_input.lower() == 'pass':
                                await self.send_message({'type': 'pass_bid'})
                                self.my_turn = False
                            else:
                                try:
                                    price = float(user_input)
                                    await self.send_message({
                                        'type': 'place_bid',
                                        'price': price
                                    })
                                except ValueError:
                                    print(f"❌ 请输入有效的数字或 'pass'")
                                    print(f"请输入出价金额 (输入 'pass' 放弃): ", end="")
                                    sys.stdout.flush()
                    except asyncio.TimeoutError:
                        pass
                else:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                print("\n\n正在退出...")
                self.running = False
                break

if __name__ == '__main__':
    try:
        asyncio.run(AsyncBidderClient().start())
    except KeyboardInterrupt:
        print("\n正在退出...")
