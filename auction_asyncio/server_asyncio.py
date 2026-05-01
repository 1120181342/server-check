import asyncio
import json
import time
from datetime import datetime
import sys
import os

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
        self._lock = asyncio.Lock()
        
    async def start_auction(self, item_name, initial_price):
        async with self._lock:
            self.reset_auction()
            self.item_name = item_name
            self.current_price = initial_price
            self.auction_active = True
            self.last_bid_price = initial_price
            return True
            
    async def add_bidder(self, bidder_id, bidder_name):
        async with self._lock:
            if bidder_id not in self.bidders:
                self.bidders[bidder_id] = {
                    'name': bidder_name,
                    'status': 'active',
                    'bid_time': None
                }
                self.bid_order.append(bidder_id)
                return True
            return False
            
    async def remove_bidder(self, bidder_id):
        async with self._lock:
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
        
    async def place_bid(self, bidder_id, price):
        async with self._lock:
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
            
    async def pass_bid(self, bidder_id):
        async with self._lock:
            if not self.auction_active:
                return False, "拍卖未开始"
                
            current_bidder = self.get_current_bidder()
            if current_bidder != bidder_id:
                return False, "不是您的出价轮次"
                
            self.bidders[bidder_id]['status'] = 'out'
            self.consecutive_passes += 1
            
            active_bidders = self.get_active_bidders()
            
            if not active_bidders:
                self.auction_active = False
                return True, "拍卖结束"
                
            if self.current_bidder_index >= len(active_bidders):
                self.current_bidder_index = 0
                
            return True, "已放弃本轮出价"
            
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

class AsyncAuctionServer:
    def __init__(self, host='localhost', port=9998):
        self.host = host
        self.port = port
        self.auction_system = AuctionSystem()
        self.clients = {}
        self.host_client = None
        self.server = None
        self.running = False
        self.bid_timer_task = None
        
    async def broadcast(self, message, exclude=None):
        for client_id, writer in list(self.clients.items()):
            if client_id != exclude and not writer.is_closing():
                try:
                    writer.write((json.dumps(message, ensure_ascii=False) + '\n').encode('utf-8'))
                    await writer.drain()
                except:
                    pass
                    
    async def send_to_client(self, client_id, message):
        if client_id in self.clients and not self.clients[client_id].is_closing():
            try:
                self.clients[client_id].write((json.dumps(message, ensure_ascii=False) + '\n').encode('utf-8'))
                await self.clients[client_id].drain()
            except:
                pass
                
    async def start_bid_timer(self, bidder_id):
        async def timer_callback():
            try:
                await asyncio.sleep(self.auction_system.bid_duration)
                current_bidder = self.auction_system.get_current_bidder()
                if current_bidder == bidder_id and self.auction_system.auction_active:
                    result, message = await self.auction_system.pass_bid(bidder_id)
                    if result:
                        state = self.auction_system.get_auction_state()
                        await self.broadcast({
                            'type': 'bid_timeout',
                            'bidder_id': bidder_id,
                            'bidder_name': self.auction_system.bidders[bidder_id]['name'],
                            'message': '出价超时，已退出竞拍',
                            'state': state
                        })
                        
                        if not self.auction_system.auction_active:
                            await self.broadcast({
                                'type': 'auction_ended',
                                'winner_id': self.auction_system.last_bidder,
                                'winner_name': self.auction_system.bidders[self.auction_system.last_bidder]['name'] if self.auction_system.last_bidder else None,
                                'final_price': self.auction_system.last_bid_price,
                                'item_name': self.auction_system.item_name
                            })
                        else:
                            next_bidder = self.auction_system.get_current_bidder()
                            if next_bidder:
                                state = self.auction_system.get_auction_state()
                                await self.send_to_client(next_bidder, {
                                    'type': 'your_turn',
                                    'current_price': state['current_price'],
                                    'bid_duration': self.auction_system.bid_duration,
                                    'state': state
                                })
                                asyncio.create_task(self.start_bid_timer(next_bidder))
            except asyncio.CancelledError:
                pass
    
        self.bid_timer_task = asyncio.create_task(timer_callback())
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_addr = writer.get_extra_info('peername')
        client_id = f"{client_addr[0]}:{client_addr[1]}"
        print(f"新连接: {client_id}")
        
        buffer = b""
        client_info = {'type': None, 'name': None}
        
        try:
            while not writer.is_closing():
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=300)
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
                            await self.process_message(client_id, message, writer, client_info)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass
                            
                except asyncio.TimeoutError:
                    continue
                    
        except Exception as e:
            print(f"客户端错误 {client_id}: {e}")
        finally:
            print(f"客户端断开: {client_id}")
            if client_id in self.clients:
                if client_info['type'] == 'bidder':
                    await self.auction_system.remove_bidder(client_id)
                    await self.broadcast({
                        'type': 'user_left',
                        'user_id': client_id,
                        'user_name': client_info['name'],
                        'state': self.auction_system.get_auction_state()
                    })
                del self.clients[client_id]
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
                
    async def process_message(self, client_id, message, writer, client_info):
        msg_type = message.get('type')
        
        if msg_type == 'join':
            user_type = message.get('user_type')
            user_name = message.get('user_name')
            
            client_info['type'] = user_type
            client_info['name'] = user_name
            self.clients[client_id] = writer
            
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
                await self.auction_system.add_bidder(client_id, user_name)
                response = {
                    'type': 'joined',
                    'user_id': client_id,
                    'user_type': 'bidder',
                    'message': f'竞标者 {user_name} 已加入',
                    'state': self.auction_system.get_auction_state()
                }
            
            await self.send_to_client(client_id, response)
            await self.broadcast({
                'type': 'user_joined',
                'user_id': client_id,
                'user_type': user_type,
                'user_name': user_name,
                'state': self.auction_system.get_auction_state()
            }, exclude=client_id)
            
        elif msg_type == 'start_auction':
            if client_info['type'] != 'host':
                await self.send_to_client(client_id, {'type': 'error', 'message': '只有主持人可以启动拍卖'})
                return
                
            item_name = message.get('item_name')
            initial_price = float(message.get('initial_price', 0))
            
            if initial_price <= 0:
                await self.send_to_client(client_id, {'type': 'error', 'message': '初始价格必须大于0'})
                return
            
            await self.auction_system.start_auction(item_name, initial_price)
            state = self.auction_system.get_auction_state()
            
            await self.broadcast({
                'type': 'auction_started',
                'item_name': item_name,
                'initial_price': initial_price,
                'state': state
            })
            
            current_bidder = self.auction_system.get_current_bidder()
            if current_bidder:
                await self.send_to_client(current_bidder, {
                    'type': 'your_turn',
                    'current_price': state['current_price'],
                    'bid_duration': self.auction_system.bid_duration,
                    'state': state
                })
                await self.start_bid_timer(current_bidder)
                
        elif msg_type == 'place_bid':
            if client_info['type'] != 'bidder':
                return
                
            price = float(message.get('price', 0))
            result, msg = await self.auction_system.place_bid(client_id, price)
            
            if result:
                if self.bid_timer_task:
                    self.bid_timer_task.cancel()
                    
                state = self.auction_system.get_auction_state()
                await self.broadcast({
                    'type': 'bid_placed',
                    'bidder_id': client_id,
                    'bidder_name': self.auction_system.bidders[client_id]['name'],
                    'price': price,
                    'message': msg,
                    'state': state
                })
                
                next_bidder = self.auction_system.get_current_bidder()
                if next_bidder:
                    await self.send_to_client(next_bidder, {
                        'type': 'your_turn',
                        'current_price': state['current_price'],
                        'bid_duration': self.auction_system.bid_duration,
                        'state': state
                    })
                    await self.start_bid_timer(next_bidder)
            else:
                await self.send_to_client(client_id, {'type': 'bid_error', 'message': msg})
                
        elif msg_type == 'pass_bid':
            if client_info['type'] != 'bidder':
                return
                
            result, msg = await self.auction_system.pass_bid(client_id)
            
            if result:
                if self.bid_timer_task:
                    self.bid_timer_task.cancel()
                    
                state = self.auction_system.get_auction_state()
                
                if not self.auction_system.auction_active:
                    await self.broadcast({
                        'type': 'auction_ended',
                        'winner_id': self.auction_system.last_bidder,
                        'winner_name': self.auction_system.bidders[self.auction_system.last_bidder]['name'] if self.auction_system.last_bidder else None,
                        'final_price': self.auction_system.last_bid_price,
                        'item_name': self.auction_system.item_name
                    })
                else:
                    await self.broadcast({
                        'type': 'bid_passed',
                        'bidder_id': client_id,
                        'bidder_name': self.auction_system.bidders[client_id]['name'],
                        'message': msg,
                        'state': state
                    })
                    
                    next_bidder = self.auction_system.get_current_bidder()
                    if next_bidder:
                        await self.send_to_client(next_bidder, {
                            'type': 'your_turn',
                            'current_price': state['current_price'],
                            'bid_duration': self.auction_system.bid_duration,
                            'state': state
                        })
                        await self.start_bid_timer(next_bidder)
            else:
                await self.send_to_client(client_id, {'type': 'bid_error', 'message': msg})
                
        elif msg_type == 'get_state':
            await self.send_to_client(client_id, {
                'type': 'state',
                'state': self.auction_system.get_auction_state()
            })
            
    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        self.running = True
        addr = self.server.sockets[0].getsockname()
        print(f"拍卖服务器已启动在 {addr[0]}:{addr[1]}")
        print(f"等待客户端连接...")
        print(f"提示: 请在新终端中运行 host_asyncio.py 作为主持人，运行 bidder_asyncio.py 作为竞标者")
        
        async with self.server:
            await self.server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(AsyncAuctionServer().start())
    except KeyboardInterrupt:
        print("\n服务器正在关闭...")
