// 全局变量
let currentDate = new Date();
let selectedDate = null;
let selectedTime = null;
let selectedTicketType = null;
let selectedTicketPrice = 0;
let ticketQuantity = 1;
let currentOrderStatus = 'unused';

// 订单数据
const ordersData = {
    unused: [
        {
            id: 'ORD20260428001',
            ticketType: 'standard',
            ticketName: '原价票',
            price: 100,
            quantity: 2,
            totalPrice: 200,
            date: '2026-04-28',
            time: '09:00-12:00',
            status: 'unused',
            purchaseTime: '2026-04-25 10:30:15',
            image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=公园%20入口%20风景%2C%20阳光%20明媚%2C%20绿树%20环绕&image_size=square'
        },
        {
            id: 'ORD20260429002',
            ticketType: 'discount',
            ticketName: '特价票',
            price: 70,
            quantity: 1,
            totalPrice: 70,
            date: '2026-04-29',
            time: '14:00-17:00',
            status: 'unused',
            purchaseTime: '2026-04-25 14:20:30',
            image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=公园%20湖泊%20风景%2C%20小桥%20流水%2C%20绿树%20成荫&image_size=square'
        }
    ],
    used: [
        {
            id: 'ORD20260420003',
            ticketType: 'standard',
            ticketName: '原价票',
            price: 100,
            quantity: 3,
            totalPrice: 300,
            date: '2026-04-20',
            time: '09:00-12:00',
            status: 'used',
            purchaseTime: '2026-04-18 09:15:45',
            useTime: '2026-04-20 09:30:12',
            image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=公园%20花海%2C%20五颜六色%20花朵%2C%20游客%20游玩&image_size=square'
        }
    ],
    refunded: [
        {
            id: 'ORD20260415004',
            ticketType: 'standard',
            ticketName: '原价票',
            price: 100,
            quantity: 2,
            totalPrice: 200,
            date: '2026-04-15',
            time: '14:00-17:00',
            status: 'refunded',
            purchaseTime: '2026-04-13 16:45:20',
            refundTime: '2026-04-14 10:20:15',
            refundAmount: 200,
            image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=公园%20喷泉%2C%20水流%20飞溅%2C%20阳光%20照射&image_size=square'
        }
    ]
};

// 时间段数据
const timeSlots = [
    { time: '08:00-10:00', remaining: 50 },
    { time: '10:00-12:00', remaining: 30 },
    { time: '12:00-14:00', remaining: 80 },
    { time: '14:00-16:00', remaining: 45 },
    { time: '16:00-18:00', remaining: 60 },
    { time: '18:00-20:00', remaining: 25 }
];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('公园票务系统加载完成');
    
    // 初始化日期选择器
    initDatePicker();
    
    // 初始化时间段选择
    initTimeSlots();
    
    // 初始化页面导航
    initNavigation();
    
    // 初始化购票功能
    initPurchase();
    
    // 初始化订单功能
    initOrders();
    
    // 渲染订单列表
    renderOrders('unused');
});

// ==================== 导航功能 ====================
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const page = this.dataset.page;
            switchPage(page);
        });
    });
}

function switchPage(pageName) {
    // 隐藏所有页面
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    
    // 移除所有导航项的活动状态
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    
    // 显示选中的页面
    document.getElementById(pageName).classList.add('active');
    
    // 设置导航项活动状态
    const activeNav = document.querySelector(`.nav-item[data-page="${pageName}"]`);
    if (activeNav) {
        activeNav.classList.add('active');
    }
}

// ==================== 日期选择器功能 ====================
function initDatePicker() {
    renderCalendar();
    
    // 绑定月份切换按钮
    document.getElementById('prevMonth').addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    
    document.getElementById('nextMonth').addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    
    // 绑定人数选择器
    document.getElementById('decreasePeople').addEventListener('click', function() {
        let count = parseInt(document.getElementById('peopleCount').textContent);
        if (count > 1) {
            count--;
            document.getElementById('peopleCount').textContent = count;
        }
    });
    
    document.getElementById('increasePeople').addEventListener('click', function() {
        let count = parseInt(document.getElementById('peopleCount').textContent);
        if (count < 10) {
            count++;
            document.getElementById('peopleCount').textContent = count;
        }
    });
    
    // 绑定前往购票按钮
    document.getElementById('goToPurchase').addEventListener('click', function() {
        if (selectedDate && selectedTime) {
            // 存储预约信息到本地存储
            localStorage.setItem('bookingDate', selectedDate);
            localStorage.setItem('bookingTime', selectedTime);
            localStorage.setItem('bookingPeople', document.getElementById('peopleCount').textContent);
            
            // 切换到购票页面
            switchPage('purchase');
            
            // 更新购票页面的使用日期
            document.getElementById('modalUseDate').textContent = selectedDate;
        } else {
            alert('请先选择日期和时间段');
        }
    });
}

function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // 更新显示的年月
    document.getElementById('currentMonth').textContent = `${year}年${month + 1}月`;
    
    const dateGrid = document.getElementById('dateGrid');
    dateGrid.innerHTML = '';
    
    // 获取当月第一天是星期几
    const firstDay = new Date(year, month, 1).getDay();
    
    // 获取当月的天数
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    // 获取上个月的天数
    const daysInPrevMonth = new Date(year, month, 0).getDate();
    
    // 计算两天后的日期（最早可预约日期）
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const twoDaysLater = new Date(today);
    twoDaysLater.setDate(twoDaysLater.getDate() + 2);
    
    // 填充上个月的日期
    for (let i = 0; i < firstDay; i++) {
        const day = daysInPrevMonth - firstDay + i + 1;
        const dayElement = createDayElement(day, true, false);
        dateGrid.appendChild(dayElement);
    }
    
    // 填充当月的日期
    for (let day = 1; day <= daysInMonth; day++) {
        const currentDayDate = new Date(year, month, day);
        
        // 判断是否是两天前或今天（不可预约）
        const isDisabled = currentDayDate < twoDaysLater;
        
        // 判断是否是已选日期
        const isSelected = selectedDate === formatDate(currentDayDate);
        
        const dayElement = createDayElement(day, false, isDisabled, isSelected, currentDayDate);
        dateGrid.appendChild(dayElement);
    }
    
    // 计算需要填充的下个月日期数量
    const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;
    const remainingCells = totalCells - (firstDay + daysInMonth);
    
    // 填充下个月的日期
    for (let i = 1; i <= remainingCells; i++) {
        const dayElement = createDayElement(i, true, false);
        dateGrid.appendChild(dayElement);
    }
}

function createDayElement(day, isOtherMonth, isDisabled, isSelected = false, dateObj = null) {
    const dayElement = document.createElement('div');
    dayElement.className = 'date-item';
    
    if (isOtherMonth) {
        dayElement.classList.add('other-month');
    }
    
    if (isDisabled) {
        dayElement.classList.add('disabled');
    }
    
    if (isSelected) {
        dayElement.classList.add('selected');
    }
    
    // 计算星期几
    let weekdayText = '';
    if (dateObj) {
        const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
        weekdayText = weekdays[dateObj.getDay()];
    }
    
    dayElement.innerHTML = `
        <span class="day">${day}</span>
        ${weekdayText ? `<span class="weekday">${weekdayText}</span>` : ''}
    `;
    
    // 绑定点击事件
    if (!isOtherMonth && !isDisabled) {
        dayElement.addEventListener('click', function() {
            // 移除其他日期的选中状态
            document.querySelectorAll('.date-item').forEach(item => {
                item.classList.remove('selected');
            });
            
            // 添加选中状态
            this.classList.add('selected');
            
            // 保存选中的日期
            selectedDate = formatDate(dateObj);
            
            // 更新摘要
            document.getElementById('summaryDate').textContent = selectedDate;
            
            // 显示时间段选择
            document.getElementById('timeSection').style.display = 'block';
            
            // 重置时间段选择
            selectedTime = null;
            document.querySelectorAll('.time-slot').forEach(slot => {
                slot.classList.remove('selected');
            });
            
            // 隐藏摘要
            document.getElementById('bookingSummary').style.display = 'none';
        });
    }
    
    return dayElement;
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// ==================== 时间段选择功能 ====================
function initTimeSlots() {
    renderTimeSlots();
}

function renderTimeSlots() {
    const timeSlotsContainer = document.getElementById('timeSlots');
    timeSlotsContainer.innerHTML = '';
    
    timeSlots.forEach(slot => {
        const slotElement = document.createElement('div');
        slotElement.className = 'time-slot';
        
        // 模拟部分时间段不可用
        const isDisabled = slot.remaining === 0;
        if (isDisabled) {
            slotElement.classList.add('disabled');
        }
        
        slotElement.innerHTML = `
            <div class="time">${slot.time}</div>
            <div class="remaining">剩余 ${slot.remaining} 位</div>
        `;
        
        // 绑定点击事件
        if (!isDisabled) {
            slotElement.addEventListener('click', function() {
                // 移除其他时间段的选中状态
                document.querySelectorAll('.time-slot').forEach(s => {
                    s.classList.remove('selected');
                });
                
                // 添加选中状态
                this.classList.add('selected');
                
                // 保存选中的时间段
                selectedTime = slot.time;
                
                // 更新摘要
                document.getElementById('summaryTime').textContent = selectedTime;
                
                // 显示摘要
                document.getElementById('bookingSummary').style.display = 'block';
            });
        }
        
        timeSlotsContainer.appendChild(slotElement);
    });
}

// ==================== 购票功能 ====================
function initPurchase() {
    // 绑定购买按钮
    const purchaseButtons = document.querySelectorAll('.purchase-btn');
    purchaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const ticketType = this.dataset.ticketType;
            openPurchaseModal(ticketType);
        });
    });
    
    // 绑定关闭弹窗按钮
    document.getElementById('closeModal').addEventListener('click', closePurchaseModal);
    document.getElementById('cancelPurchase').addEventListener('click', closePurchaseModal);
    
    // 绑定数量选择器
    document.getElementById('decreaseQty').addEventListener('click', function() {
        if (ticketQuantity > 1) {
            ticketQuantity--;
            updateTicketQuantity();
        }
    });
    
    document.getElementById('increaseQty').addEventListener('click', function() {
        if (ticketQuantity < 10) {
            ticketQuantity++;
            updateTicketQuantity();
        }
    });
    
    // 绑定确认支付按钮
    document.getElementById('confirmPurchase').addEventListener('click', handleWechatPayment);
}

function openPurchaseModal(ticketType) {
    selectedTicketType = ticketType;
    
    // 设置票价
    if (ticketType === 'standard') {
        selectedTicketPrice = 100;
        document.getElementById('modalTicketType').textContent = '原价票';
        document.getElementById('modalTicketPrice').textContent = '¥100/人';
    } else {
        selectedTicketPrice = 70;
        document.getElementById('modalTicketType').textContent = '特价票';
        document.getElementById('modalTicketPrice').textContent = '¥70/人';
    }
    
    // 重置数量
    ticketQuantity = 1;
    updateTicketQuantity();
    
    // 设置使用日期（如果有预约信息）
    const bookingDate = localStorage.getItem('bookingDate');
    if (bookingDate) {
        document.getElementById('modalUseDate').textContent = bookingDate;
    }
    
    // 显示弹窗
    document.getElementById('purchaseModal').classList.add('active');
}

function closePurchaseModal() {
    document.getElementById('purchaseModal').classList.remove('active');
}

function updateTicketQuantity() {
    document.getElementById('ticketQuantity').textContent = ticketQuantity;
    
    // 更新总价
    const totalPrice = selectedTicketPrice * ticketQuantity;
    document.getElementById('modalTotalPrice').textContent = `¥${totalPrice}`;
}

function handleWechatPayment() {
    // 模拟微信支付跳转
    // 实际项目中，这里应该调用后端API获取支付链接
    
    const totalPrice = selectedTicketPrice * ticketQuantity;
    const bookingDate = localStorage.getItem('bookingDate') || document.getElementById('modalUseDate').textContent;
    const bookingTime = localStorage.getItem('bookingTime') || '09:00-12:00';
    
    // 模拟生成订单
    const newOrder = {
        id: `ORD${new Date().getFullYear()}${String(new Date().getMonth() + 1).padStart(2, '0')}${String(new Date().getDate()).padStart(2, '0')}${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
        ticketType: selectedTicketType,
        ticketName: selectedTicketType === 'standard' ? '原价票' : '特价票',
        price: selectedTicketPrice,
        quantity: ticketQuantity,
        totalPrice: totalPrice,
        date: bookingDate,
        time: bookingTime,
        status: 'unused',
        purchaseTime: formatDateTime(new Date()),
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=公园%20入口%20风景%2C%20阳光%20明媚%2C%20绿树%20环绕&image_size=square'
    };
    
    // 添加到未使用订单列表
    ordersData.unused.unshift(newOrder);
    
    // 关闭弹窗
    closePurchaseModal();
    
    // 显示支付提示
    alert(`正在跳转到微信支付页面...\n\n订单信息：\n订单号：${newOrder.id}\n门票类型：${newOrder.ticketName}\n数量：${ticketQuantity}人\n总价：¥${totalPrice}`);
    
    // 实际项目中，这里应该是：
    // 1. 调用后端API创建订单
    // 2. 获取微信支付链接
    // 3. 跳转到微信支付页面
    // 例如：window.location.href = wechatPayUrl;
    
    // 模拟支付成功后跳转到订单页面
    setTimeout(() => {
        alert('支付成功！');
        switchPage('orders');
        renderOrders('unused');
    }, 1000);
}

function formatDateTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// ==================== 订单功能 ====================
function initOrders() {
    // 绑定订单标签切换
    const orderTabs = document.querySelectorAll('.order-tab');
    orderTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const status = this.dataset.status;
            
            // 移除其他标签的活动状态
            orderTabs.forEach(t => t.classList.remove('active'));
            
            // 添加当前标签的活动状态
            this.classList.add('active');
            
            // 渲染对应状态的订单
            renderOrders(status);
        });
    });
    
    // 绑定关闭订单详情弹窗
    document.getElementById('closeOrderModal').addEventListener('click', function() {
        document.getElementById('orderDetailModal').classList.remove('active');
    });
}

function renderOrders(status) {
    currentOrderStatus = status;
    const ordersList = document.getElementById('ordersList');
    const orders = ordersData[status];
    
    if (orders.length === 0) {
        ordersList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>暂无${getStatusText(status)}订单</p>
            </div>
        `;
        return;
    }
    
    ordersList.innerHTML = orders.map(order => createOrderCard(order)).join('');
    
    // 绑定订单卡片点击事件
    const orderCards = document.querySelectorAll('.order-card');
    orderCards.forEach((card, index) => {
        // 绑定查看详情按钮
        const viewBtn = card.querySelector('.order-btn[data-action="view"]');
        if (viewBtn) {
            viewBtn.addEventListener('click', function() {
                showOrderDetail(orders[index]);
            });
        }
        
        // 绑定退票按钮
        const refundBtn = card.querySelector('.order-btn[data-action="refund"]');
        if (refundBtn) {
            refundBtn.addEventListener('click', function() {
                handleRefund(orders[index]);
            });
        }
    });
}

function getStatusText(status) {
    const statusMap = {
        'unused': '未使用',
        'used': '已使用',
        'refunded': '已退票'
    };
    return statusMap[status] || '';
}

function createOrderCard(order) {
    const statusClass = `status-${order.status}`;
    const statusText = getStatusText(order.status);
    
    let actions = '';
    if (order.status === 'unused') {
        actions = `
            <button class="order-btn danger" data-action="refund">申请退票</button>
            <button class="order-btn primary" data-action="view">查看详情</button>
        `;
    } else {
        actions = `
            <button class="order-btn primary" data-action="view">查看详情</button>
        `;
    }
    
    return `
        <div class="order-card">
            <div class="order-header">
                <span class="order-number">订单号：${order.id}</span>
                <span class="order-status ${statusClass}">${statusText}</span>
            </div>
            <div class="order-content">
                <img src="${order.image}" alt="订单图片" class="order-image">
                <div class="order-details">
                    <h4 class="order-title">公园门票</h4>
                    <p class="order-type">${order.ticketName}</p>
                    <p class="order-date">使用日期：${order.date} ${order.time}</p>
                    <p class="order-people">购买数量：${order.quantity}人</p>
                    <div class="order-price">
                        <span class="price-label">订单金额：</span>
                        <span class="price-amount">¥${order.totalPrice}</span>
                    </div>
                </div>
            </div>
            <div class="order-actions">
                ${actions}
            </div>
        </div>
    `;
}

function showOrderDetail(order) {
    const detailBody = document.getElementById('orderDetailBody');
    const detailActions = document.getElementById('orderDetailActions');
    
    let refundInfo = '';
    if (order.status === 'refunded') {
        refundInfo = `
            <p>退票时间：<span>${order.refundTime}</span></p>
            <p>退票金额：<span>¥${order.refundAmount}</span></p>
        `;
    }
    
    let useInfo = '';
    if (order.status === 'used') {
        useInfo = `<p>使用时间：<span>${order.useTime}</span></p>`;
    }
    
    detailBody.innerHTML = `
        <div class="detail-section">
            <h4>订单信息</h4>
            <p>订单号：<span>${order.id}</span></p>
            <p>门票类型：<span>${order.ticketName}</span></p>
            <p>购买数量：<span>${order.quantity}人</span></p>
            <p>订单金额：<span>¥${order.totalPrice}</span></p>
            <p>下单时间：<span>${order.purchaseTime}</span></p>
        </div>
        <div class="detail-section">
            <h4>使用信息</h4>
            <p>使用日期：<span>${order.date}</span></p>
            <p>使用时间：<span>${order.time}</span></p>
            ${useInfo}
            ${refundInfo}
        </div>
    `;
    
    let actionButtons = '';
    if (order.status === 'unused') {
        actionButtons = `
            <button class="secondary-btn" onclick="document.getElementById('orderDetailModal').classList.remove('active')">关闭</button>
            <button class="primary-btn order-btn danger" onclick="handleRefund(ordersData.${currentOrderStatus}.find(o => o.id === '${order.id}'))">申请退票</button>
        `;
    } else {
        actionButtons = `
            <button class="primary-btn" onclick="document.getElementById('orderDetailModal').classList.remove('active')">关闭</button>
        `;
    }
    
    detailActions.innerHTML = actionButtons;
    
    document.getElementById('orderDetailModal').classList.add('active');
}

function handleRefund(order) {
    if (order.status !== 'unused') {
        alert('该订单不支持退票');
        return;
    }
    
    // 特价票不可退票
    if (order.ticketType === 'discount') {
        alert('特价票不可退票');
        return;
    }
    
    // 确认退票
    if (confirm(`确定要申请退票吗？\n\n订单号：${order.id}\n退票金额：¥${order.totalPrice}`)) {
        // 从订单列表中找到该订单的索引
        const index = ordersData.unused.findIndex(o => o.id === order.id);
        
        if (index !== -1) {
            // 从unused列表中移除
            const refundedOrder = ordersData.unused.splice(index, 1)[0];
            
            // 更新订单状态
            refundedOrder.status = 'refunded';
            refundedOrder.refundTime = formatDateTime(new Date());
            refundedOrder.refundAmount = refundedOrder.totalPrice;
            
            // 添加到refunded列表
            ordersData.refunded.unshift(refundedOrder);
            
            // 关闭详情弹窗（如果打开）
            document.getElementById('orderDetailModal').classList.remove('active');
            
            // 显示退票成功提示
            alert('退票申请已提交，退款将在1-3个工作日内原路返回');
            
            // 重新渲染订单列表
            renderOrders(currentOrderStatus);
        }
    }
}

// ==================== 个人信息功能 ====================
// 个人信息页面的功能相对简单，主要是展示信息
// 可以添加编辑功能的占位符
document.addEventListener('DOMContentLoaded', function() {
    // 绑定编辑信息按钮
    const editButtons = document.querySelectorAll('.info-edit');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const label = this.parentElement.querySelector('.info-label').textContent;
            alert(`编辑${label}功能开发中...`);
        });
    });
    
    // 绑定退出登录按钮
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            if (confirm('确定要退出登录吗？')) {
                alert('已退出登录');
            }
        });
    }
});
