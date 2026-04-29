from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'auction-secret-key-2024'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*", async_handlers=True)

class AuctionSystem:
    def __init__(self):
        self.reset_auction()
        
    def reset_auction(self):
        self.auction_active = False
        self.item_name = ""
        self.current_price = 0
        self.bidders = {}  # {bidder_id: {name: str, status: 'active'|'out', bid_time: float}}
        self.bid_order = []
        self.current_bidder_index = 0
        self.last_bidder = None
        self.last_bid_price = 0
        self.consecutive_passes = 0
        self.bid_timer = None
        self.bid_start_time = 0
        self.bid_duration = 5  # seconds
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
            'bid_history': self.bid_history,
            'bid_time_remaining': max(0, self.bid_duration - (time.time() - self.bid_start_time)) if self.bid_start_time > 0 else 0
        }

auction_system = AuctionSystem()
bid_timers = {}

def start_bid_timer(bidder_id):
    def timer_callback():
        time.sleep(auction_system.bid_duration)
        current_bidder = auction_system.get_current_bidder()
        if current_bidder == bidder_id and auction_system.auction_active:
            result, message = auction_system.pass_bid(bidder_id)
            if result:
                state = auction_system.get_auction_state()
                socketio.emit('bid_timeout', {
                    'bidder_id': bidder_id,
                    'bidder_name': auction_system.bidders[bidder_id]['name'],
                    'message': '出价超时，已退出竞拍',
                    'state': state
                }, room='auction_room')
                
                if not auction_system.auction_active:
                    socketio.emit('auction_ended', {
                        'winner_id': auction_system.last_bidder,
                        'winner_name': auction_system.bidders[auction_system.last_bidder]['name'] if auction_system.last_bidder else None,
                        'final_price': auction_system.last_bid_price,
                        'item_name': auction_system.item_name
                    }, room='auction_room')
    
    timer = threading.Thread(target=timer_callback)
    timer.daemon = True
    auction_system.bid_start_time = time.time()
    timer.start()
    bid_timers[bidder_id] = timer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/host')
def host():
    return render_template('host.html')

@app.route('/bidder')
def bidder():
    return render_template('bidder.html')

@app.route('/api/state')
def get_state():
    return jsonify(auction_system.get_auction_state())

@socketio.on('join')
def handle_join(data):
    user_type = data.get('user_type')
    user_name = data.get('user_name')
    user_id = request.sid
    
    join_room('auction_room')
    
    if user_type == 'host':
        emit('joined', {
            'user_id': user_id,
            'user_type': 'host',
            'message': f'主持人 {user_name} 已加入',
            'state': auction_system.get_auction_state()
        })
    else:
        auction_system.add_bidder(user_id, user_name)
        emit('joined', {
            'user_id': user_id,
            'user_type': 'bidder',
            'message': f'竞标者 {user_name} 已加入',
            'state': auction_system.get_auction_state()
        })
    
    emit('user_joined', {
        'user_id': user_id,
        'user_type': user_type,
        'user_name': user_name,
        'state': auction_system.get_auction_state()
    }, room='auction_room', include_self=False)

@socketio.on('start_auction')
def handle_start_auction(data):
    item_name = data.get('item_name')
    initial_price = float(data.get('initial_price', 0))
    
    if initial_price <= 0:
        emit('error', {'message': '初始价格必须大于0'})
        return
    
    auction_system.start_auction(item_name, initial_price)
    state = auction_system.get_auction_state()
    
    emit('auction_started', {
        'item_name': item_name,
        'initial_price': initial_price,
        'state': state
    }, room='auction_room')
    
    current_bidder = auction_system.get_current_bidder()
    if current_bidder:
        emit('your_turn', {
            'current_price': state['current_price'],
            'bid_duration': auction_system.bid_duration,
            'state': state
        }, room=current_bidder)
        start_bid_timer(current_bidder)

@socketio.on('place_bid')
def handle_place_bid(data):
    user_id = request.sid
    price = float(data.get('price', 0))
    
    result, message = auction_system.place_bid(user_id, price)
    
    if result:
        state = auction_system.get_auction_state()
        emit('bid_placed', {
            'bidder_id': user_id,
            'bidder_name': auction_system.bidders[user_id]['name'],
            'price': price,
            'message': message,
            'state': state
        }, room='auction_room')
        
        next_bidder = auction_system.get_current_bidder()
        if next_bidder:
            emit('your_turn', {
                'current_price': state['current_price'],
                'bid_duration': auction_system.bid_duration,
                'state': state
            }, room=next_bidder)
            start_bid_timer(next_bidder)
    else:
        emit('bid_error', {'message': message})

@socketio.on('pass_bid')
def handle_pass_bid(data):
    user_id = request.sid
    result, message = auction_system.pass_bid(user_id)
    
    if result:
        state = auction_system.get_auction_state()
        
        if not auction_system.auction_active:
            emit('auction_ended', {
                'winner_id': auction_system.last_bidder,
                'winner_name': auction_system.bidders[auction_system.last_bidder]['name'] if auction_system.last_bidder else None,
                'final_price': auction_system.last_bid_price,
                'item_name': auction_system.item_name
            }, room='auction_room')
        else:
            emit('bid_passed', {
                'bidder_id': user_id,
                'bidder_name': auction_system.bidders[user_id]['name'],
                'message': message,
                'state': state
            }, room='auction_room')
            
            next_bidder = auction_system.get_current_bidder()
            if next_bidder:
                emit('your_turn', {
                    'current_price': state['current_price'],
                    'bid_duration': auction_system.bid_duration,
                    'state': state
                }, room=next_bidder)
                start_bid_timer(next_bidder)
    else:
        emit('bid_error', {'message': message})

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in auction_system.bidders:
        bidder_name = auction_system.bidders[user_id]['name']
        auction_system.remove_bidder(user_id)
        leave_room('auction_room')
        
        state = auction_system.get_auction_state()
        emit('user_left', {
            'user_id': user_id,
            'user_name': bidder_name,
            'state': state
        }, room='auction_room')

if __name__ == '__main__':
    print("启动拍卖竞标系统...")
    print(f"访问地址: http://localhost:5000")
    print(f"主持人页面: http://localhost:5000/host")
    print(f"竞标者页面: http://localhost:5000/bidder")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
