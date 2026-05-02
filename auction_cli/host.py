import socket
import json
import threading
import sys
import os
import time

class HostClient:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.socket = None
        self.user_id = None
        self.user_name = None
        self.running = False
        self.state = None
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        print("="*60)
        print("                    🏷️  拍卖竞标系统 - 主持人端")
        print("="*60)
        print()
        
    def print_menu(self):
        print("\n--- 主持人菜单 ---")
        print("1. 查看当前状态")
        print("2. 启动新拍卖")
        print("3. 查看竞标者列表")
        print("4. 查看出价历史")
        print("5. 退出系统")
        print("-" * 40)
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
            
    def send_message(self, message):
        try:
            self.socket.sendall((json.dumps(message) + '\n').encode('utf-8'))
            return True
        except:
            return False
            
    def receive_messages(self):
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line:
                        continue
                    try:
                        message = json.loads(line)
                        self.handle_message(message)
                    except json.JSONDecodeError:
                        pass
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
            if user_type == 'bidder':
                print(f"\n📢 竞标者 {user_name} 已加入拍卖")
            
        elif msg_type == 'user_left':
            user_name = message.get('user_name')
            self.state = message.get('state')
            print(f"\n📢 {user_name} 已离开")
            
        elif msg_type == 'auction_started':
            self.state = message.get('state')
            print(f"\n🎉 拍卖已开始!")
            print(f"   拍卖品: {message.get('item_name')}")
            print(f"   起拍价: ¥{message.get('initial_price')}")
            
        elif msg_type == 'bid_placed':
            self.state = message.get('state')
            bidder_name = message.get('bidder_name')
            price = message.get('price')
            print(f"\n💰 {bidder_name} 出价 ¥{price}")
            
        elif msg_type == 'bid_passed':
            self.state = message.get('state')
            bidder_name = message.get('bidder_name')
            print(f"\n⏭️ {bidder_name} 放弃出价，退出竞拍")
            
        elif msg_type == 'bid_timeout':
            self.state = message.get('state')
            bidder_name = message.get('bidder_name')
            print(f"\n⏰ {bidder_name} 出价超时，已退出竞拍")
            
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
            print("\n" + "="*60)
            
        elif msg_type == 'state':
            self.state = message.get('state')
            
        elif msg_type == 'error':
            print(f"\n❌ 错误: {message.get('message')}")
            
    def start(self):
        self.clear_screen()
        self.print_header()
        
        print("请输入您的主持人名称: ", end="")
        self.user_name = input().strip()
        if not self.user_name:
            self.user_name = "主持人"
            
        if not self.connect():
            return
            
        self.send_message({
            'type': 'join',
            'user_type': 'host',
            'user_name': self.user_name
        })
        
        self.running = True
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        time.sleep(0.5)
        self.main_loop()
        
    def main_loop(self):
        while self.running:
            try:
                self.print_menu()
                choice = input("\n请选择操作 (1-5): ").strip()
                
                if choice == '1':
                    self.show_status()
                elif choice == '2':
                    self.start_auction()
                elif choice == '3':
                    self.show_bidders()
                elif choice == '4':
                    self.show_bid_history()
                elif choice == '5':
                    print("\n感谢使用拍卖系统，再见!")
                    self.running = False
                    break
                else:
                    print("\n❌ 无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n\n正在退出...")
                self.running = False
                break
                
    def show_status(self):
        self.send_message({'type': 'get_state'})
        time.sleep(0.3)
        
        if self.state:
            print("\n--- 当前拍卖状态 ---")
            if self.state['auction_active']:
                print(f"状态: 🔄 拍卖进行中")
                print(f"拍卖品: {self.state['item_name']}")
                print(f"当前价格: ¥{self.state['current_price']}")
                print(f"当前出价者: {self.state['current_bidder_name'] or '无'}")
                print(f"最后出价者: {self.state['last_bidder_name'] or '无'}")
                print(f"最后出价: ¥{self.state['last_bid_price']}")
            else:
                print(f"状态: ⏸️ 等待开始拍卖")
                print(f"竞标者数量: {len(self.state['bidders'])}")
        else:
            print("\n❌ 无法获取状态")
            
    def start_auction(self):
        if self.state and self.state['auction_active']:
            print("\n⚠️  拍卖正在进行中!")
            return
            
        print("\n--- 启动新拍卖 ---")
        item_name = input("请输入拍卖品名称: ").strip()
        if not item_name:
            print("❌ 拍卖品名称不能为空")
            return
            
        try:
            initial_price = float(input("请输入初始价格: ¥").strip())
            if initial_price <= 0:
                print("❌ 价格必须大于0")
                return
        except ValueError:
            print("❌ 请输入有效的数字")
            return
            
        self.send_message({
            'type': 'start_auction',
            'item_name': item_name,
            'initial_price': initial_price
        })
        print(f"\n📤 已发送拍卖启动请求...")
        
    def show_bidders(self):
        self.send_message({'type': 'get_state'})
        time.sleep(0.3)
        
        if self.state:
            bidders = self.state['bidders']
            print(f"\n--- 竞标者列表 ({len(bidders)}人) ---")
            if bidders:
                for i, (bidder_id, info) in enumerate(bidders.items(), 1):
                    status = "✅ 活跃" if info['status'] == 'active' else "❌ 已退出"
                    print(f"{i}. {info['name']} - {status}")
            else:
                print("暂无竞标者")
        else:
            print("\n❌ 无法获取竞标者列表")
            
    def show_bid_history(self):
        self.send_message({'type': 'get_state'})
        time.sleep(0.3)
        
        if self.state:
            history = self.state['bid_history']
            print(f"\n--- 出价历史 ({len(history)}条) ---")
            if history:
                for i, bid in enumerate(history, 1):
                    print(f"{i}. {bid['bidder_name']} - ¥{bid['price']} ({bid['timestamp']})")
            else:
                print("暂无出价记录")
        else:
            print("\n❌ 无法获取出价历史")

if __name__ == '__main__':
    client = HostClient()
    client.start()
