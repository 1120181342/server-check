import socket
import threading
import time
from datetime import datetime
import json
import sys

class AuctionSystem:
    def __init__(self):
        self.reset_auction()
        
    def reset_auction(self):
        self.auction_active = False
        self.item_name = ""
        self.current_price = 0
        self.bidders = {}
        self.bid_order = []
        self.current_bidder_index = 0
        self.last_bidder = None
        self.last_bid_price = 0
        self.consecutive_passes = 0
        self.bid_duration = 5
        self.bid_history = []
        self.lock = threading.Lock()
        
    def start_auction(self, item_name, initial_price):
        with self.lock:
            self.reset_auction()
            self.item_name = item_name
            self.current_price = initial_price
            self.auction_active = True
            self.last_bid_price = initial_price
            return True
            
    def add_bidder(self, bidder_id, bidder_name):
        with self.lock:
            if bidder_id not in self.bidders:
                self.bidders[bidder_id] = {
                    'name': bidder_name,
                    'status': 'active',
                    'bid_time': None
                }
                self.bid_order.append(bidder_id)
                return True
            return False
            
    def remove_bidder(self, bidder_id):
        with self.lock:
            if bidder_id in self.bidders:
                self.bidders[bidder_id]['status'] = 'out'
                return True
            return False
            
    def get_active_bidders(self):
        return [bid for bid in self.bid_order if self.bidders[bid]['status'] == 'active']
        
    def get_current_bidder(self):
        active_bidders = self.get_active_bidders()
        if not active_bidders:
            return None
        if self.current_bidder_index >= len(active_bidders):
            self.current_bidder_index = 0
        return active_bidders[self.current_bidder_index]
        
    def next_bidder(self):
        active_bidders = self.get_active_bidders()
        if not active_bidders:
            return None
            
        self.current_bidder_index += 1
        if self.current_bidder_index >= len(active_bidders):
            self.current_bidder_index = 0
            
        return active_bidders[self.current_bidder_index]
        
    def place_bid(self, bidder_id, price):
        with self.lock:
            if not self.auction_active:
                return False, "拍卖未开始"
                
            current_bidder = self.get_current_bidder()
            if current_bidder != bidder_id:
                return False, "不是您的出价轮次"
                
            if self.bidders[bidder_id]['status'] != 'active':
                return False, "您已退出竞拍"
                
            if price <= self.current_price:
                return False, "出价必须高于当前价格"
                
            self.current_price = price
            self.last_bidder = bidder_id
            self.last_bid_price = price
            self.consecutive_passes = 0
            self.bid_history.append({
                'bidder_id': bidder_id,
                'bidder_name': self.bidders[bidder_id]['name'],
                'price': price,
                'timestamp': datetime.now().isoformat()
            })
            self.next_bidder()
            return True, "出价成功"
            
    def pass_bid(self, bidder_id):
        with self.lock:
            if not self.auction_active:
                return False, "拍卖未开始"
                
            current_bidder = self.get_current_bidder()
            if current_bidder != bidder_id:
                return False, "不是您的出价轮次"
                
            self.remove_bidder(bidder_id)
            self.consecutive_passes += 1
            
            active_bidders = self.get_active_bidders()
            
            if not active_bidders:
                self.auction_active = False
                return True, "拍卖结束"
                
            if self.current_bidder_index >= len(active_bidders):
                self.current_bidder_index = 0
                
            return True, "已放弃本轮出价"
            
    def check_auction_end(self):
        with self.lock:
            if self.consecutive_passes >= len(self.get_active_bidders()):
                self.auction_active = False
                return True
            return False
            
    def get_auction_state(self):
        return {
            'auction_active': self.auction_active,
            'item_name': self.item_name,
            'current_price': self.current_price,
            'last_bidder': self.last_bidder,
            'last_bidder_name': self.bidders[self.last_bidder]['name'] if self.last_bidder else None,
            'last_bid_price': self.last_bid_price,
            'current_bidder': self.get_current_bidder(),
            'current_bidder_name': self.bidders[self.get_current_bidder()]['name'] if self.get_current_bidder() else None,
            'bidders': {k: {'name': v['name'], 'status': v['status']} for k, v in self.bidders.items()},
            'bid_history': self.bid_history
        }

class AuctionServer:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.auction_system = AuctionSystem()
        self.clients = {}
        self.host_client = None
        self.server_socket = None
        self.running = False
        self.bid_timer = None
        self.bid_start_time = 0
        
    def broadcast(self, message, exclude=None):
        for client_id, client_info in list(self.clients.items()):
            if client_id != exclude:
                try:
                    client_info['socket'].sendall((json.dumps(message) + '\n').encode('utf-8'))
                except:
                    pass
                    
    def send_to_client(self, client_id, message):
        if client_id in self.clients:
            try:
                self.clients[client_id]['socket'].sendall((json.dumps(message) + '\n').encode('utf-8'))
            except:
                pass
                
    def start_bid_timer(self, bidder_id):
        def timer_callback():
            time.sleep(self.auction_system.bid_duration)
            current_bidder = self.auction_system.get_current_bidder()
            if current_bidder == bidder_id and self.auction_system.auction_active:
                result, message = self.auction_system.pass_bid(bidder_id)
                if result:
                    state = self.auction_system.get_auction_state()
                    self.broadcast({
                        'type': 'bid_timeout',
                        'bidder_id': bidder_id,
                        'bidder_name': self.auction_system.bidders[bidder_id]['name'],
                        'message': '出价超时，已退出竞拍',
                        'state': state
                    })
                    
                    if not self.auction_system.auction_active:
                        self.broadcast({
                            'type': 'auction_ended',
                            'winner_id': self.auction_system.last_bidder,
                            'winner_name': self.auction_system.bidders[self.auction_system.last_bidder]['name'] if self.auction_system.last_bidder else None,
                            'final_price': self.auction_system.last_bid_price,
                            'item_name': self.auction_system.item_name
                        })
                    else:
                        next_bidder = self.auction_system.get_current_bidder()
                        if next_bidder:
                            self.send_to_client(next_bidder, {
                                'type': 'your_turn',
                                'current_price': state['current_price'],
                                'bid_duration': self.auction_system.bid_duration,
                                'state': state
                            })
                            self.bid_start_time = time.time()
                            self.bid_timer = threading.Thread(target=timer_callback)
                            self.bid_timer.daemon = True
                            self.bid_timer.start()
    
        self.bid_start_time = time.time()
        self.bid_timer = threading.Thread(target=timer_callback)
        self.bid_timer.daemon = True
        self.bid_timer.start()
        
    def handle_client(self, client_socket, client_address):
        client_id = f"{client_address[0]}:{client_address[1]}"
        print(f"新连接: {client_id}")
        
        buffer = ""
        
        try:
            while True:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line:
                        continue
                        
                    try:
                        message = json.loads(line)
                        self.process_message(client_id, message, client_socket)
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            print(f"客户端错误 {client_id}: {e}")
        finally:
            print(f"客户端断开: {client_id}")
            if client_id in self.clients:
                if self.clients[client_id]['type'] == 'bidder':
                    self.auction_system.remove_bidder(client_id)
                    self.broadcast({
                        'type': 'user_left',
                        'user_id': client_id,
                        'user_name': self.clients[client_id]['name'],
                        'state': self.auction_system.get_auction_state()
                    })
                del self.clients[client_id]
            try:
                client_socket.close()
            except:
                pass
                
    def process_message(self, client_id, message, client_socket):
        msg_type = message.get('type')
        
        if msg_type == 'join':
            user_type = message.get('user_type')
            user_name = message.get('user_name')
            
            self.clients[client_id] = {
                'socket': client_socket,
                'type': user_type,
                'name': user_name
            }
            
            if user_type == 'host':
                self.host_client = client_id
                response = {
                    'type': 'joined',
                    'user_id': client_id,
                    'user_type': 'host',
                    'message': f'主持人 {user_name} 已加入',
                    'state': self.auction_system.get_auction_state()
                }
            else:
                self.auction_system.add_bidder(client_id, user_name)
                response = {
                    'type': 'joined',
                    'user_id': client_id,
                    'user_type': 'bidder',
                    'message': f'竞标者 {user_name} 已加入',
                    'state': self.auction_system.get_auction_state()
                }
            
            self.send_to_client(client_id, response)
            self.broadcast({
                'type': 'user_joined',
                'user_id': client_id,
                'user_type': user_type,
                'user_name': user_name,
                'state': self.auction_system.get_auction_state()
            }, exclude=client_id)
            
        elif msg_type == 'start_auction':
            if self.clients[client_id]['type'] != 'host':
                self.send_to_client(client_id, {'type': 'error', 'message': '只有主持人可以启动拍卖'})
                return
                
            item_name = message.get('item_name')
            initial_price = float(message.get('initial_price', 0))
            
            if initial_price <= 0:
                self.send_to_client(client_id, {'type': 'error', 'message': '初始价格必须大于0'})
                return
            
            self.auction_system.start_auction(item_name, initial_price)
            state = self.auction_system.get_auction_state()
            
            self.broadcast({
                'type': 'auction_started',
                'item_name': item_name,
                'initial_price': initial_price,
                'state': state
            })
            
            current_bidder = self.auction_system.get_current_bidder()
            if current_bidder:
                self.send_to_client(current_bidder, {
                    'type': 'your_turn',
                    'current_price': state['current_price'],
                    'bid_duration': self.auction_system.bid_duration,
                    'state': state
                })
                self.start_bid_timer(current_bidder)
                
        elif msg_type == 'place_bid':
            if self.clients[client_id]['type'] != 'bidder':
                return
                
            price = float(message.get('price', 0))
            result, msg = self.auction_system.place_bid(client_id, price)
            
            if result:
                state = self.auction_system.get_auction_state()
                self.broadcast({
                    'type': 'bid_placed',
                    'bidder_id': client_id,
                    'bidder_name': self.auction_system.bidders[client_id]['name'],
                    'price': price,
                    'message': msg,
                    'state': state
                })
                
                next_bidder = self.auction_system.get_current_bidder()
                if next_bidder:
                    self.send_to_client(next_bidder, {
                        'type': 'your_turn',
                        'current_price': state['current_price'],
                        'bid_duration': self.auction_system.bid_duration,
                        'state': state
                    })
                    self.start_bid_timer(next_bidder)
            else:
                self.send_to_client(client_id, {'type': 'bid_error', 'message': msg})
                
        elif msg_type == 'pass_bid':
            if self.clients[client_id]['type'] != 'bidder':
                return
                
            result, msg = self.auction_system.pass_bid(client_id)
            
            if result:
                state = self.auction_system.get_auction_state()
                
                if not self.auction_system.auction_active:
                    self.broadcast({
                        'type': 'auction_ended',
                        'winner_id': self.auction_system.last_bidder,
                        'winner_name': self.auction_system.bidders[self.auction_system.last_bidder]['name'] if self.auction_system.last_bidder else None,
                        'final_price': self.auction_system.last_bid_price,
                        'item_name': self.auction_system.item_name
                    })
                else:
                    self.broadcast({
                        'type': 'bid_passed',
                        'bidder_id': client_id,
                        'bidder_name': self.auction_system.bidders[client_id]['name'],
                        'message': msg,
                        'state': state
                    })
                    
                    next_bidder = self.auction_system.get_current_bidder()
                    if next_bidder:
                        self.send_to_client(next_bidder, {
                            'type': 'your_turn',
                            'current_price': state['current_price'],
                            'bid_duration': self.auction_system.bid_duration,
                            'state': state
                        })
                        self.start_bid_timer(next_bidder)
            else:
                self.send_to_client(client_id, {'type': 'bid_error', 'message': msg})
                
        elif msg_type == 'get_state':
            self.send_to_client(client_id, {
                'type': 'state',
                'state': self.auction_system.get_auction_state()
            })
            
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"拍卖服务器已启动在 {self.host}:{self.port}")
        print(f"等待客户端连接...")
        print(f"提示: 请在新终端中运行 host.py 作为主持人，运行 bidder.py 作为竞标者")
        
        try:
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\n服务器正在关闭...")
        finally:
            self.running = False
            if self.server_socket:
                self.server_socket.close()

if __name__ == '__main__':
    server = AuctionServer()
    server.start()
