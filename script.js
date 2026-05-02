// 菜品数据
const menuItems = [
    // 热菜 (12道)
    { id: 1, name: '宫保鸡丁', category: 'hot', price: 28, description: '经典川菜，鸡肉鲜嫩，花生酥脆，口味咸香微辣', badge: 'hot', image: '宫保鸡丁,中式美食,辣椒花生,高清摄影' },
    { id: 2, name: '红烧肉', category: 'hot', price: 38, description: '肥而不腻，入口即化，色泽红亮，香气扑鼻', badge: 'recommend', image: '红烧肉,中式美食,五花肉,酱油烧制,高清摄影' },
    { id: 3, name: '糖醋里脊', category: 'hot', price: 32, description: '外酥里嫩，酸甜可口，金黄诱人，老少皆宜', badge: '', image: '糖醋里脊,中式美食,里脊肉,糖醋汁,高清摄影' },
    { id: 4, name: '麻婆豆腐', category: 'hot', price: 22, description: '麻辣鲜香，豆腐嫩滑，下饭神器，川菜经典', badge: 'hot', image: '麻婆豆腐,中式美食,辣椒花椒,高清摄影' },
    { id: 5, name: '鱼香肉丝', category: 'hot', price: 26, description: '鱼香味型，咸甜酸辣，肉丝滑嫩，配料丰富', badge: '', image: '鱼香肉丝,中式美食,肉丝木耳,高清摄影' },
    { id: 6, name: '水煮肉片', category: 'hot', price: 35, description: '麻辣鲜香，肉片嫩滑，汤汁浓郁，过瘾十足', badge: 'hot', image: '水煮肉片,中式美食,辣椒花椒,高清摄影' },
    { id: 7, name: '清蒸鲈鱼', category: 'hot', price: 68, description: '鲜嫩滑口，原汁原味，营养丰富，健康之选', badge: 'recommend', image: '清蒸鲈鱼,中式美食,新鲜鲈鱼,清蒸,高清摄影' },
    { id: 8, name: '京酱肉丝', category: 'hot', price: 30, description: '酱香浓郁，肉丝细嫩，搭配薄饼，风味独特', badge: '', image: '京酱肉丝,中式美食,甜面酱,高清摄影' },
    { id: 9, name: '回锅肉', category: 'hot', price: 32, description: '肥而不腻，香辣可口，蒜苗飘香，下饭首选', badge: 'hot', image: '回锅肉,中式美食,五花肉蒜苗,高清摄影' },
    { id: 10, name: '糖醋排骨', category: 'hot', price: 42, description: '酸甜适口，外酥里嫩，色泽红亮，香气诱人', badge: 'recommend', image: '糖醋排骨,中式美食,小排骨,糖醋汁,高清摄影' },
    { id: 11, name: '蒜蓉西兰花', category: 'hot', price: 18, description: '清爽健康，蒜香浓郁，营养丰富，素食首选', badge: '', image: '蒜蓉西兰花,中式美食,新鲜西兰花,蒜蓉,高清摄影' },
    { id: 12, name: '宫保虾球', category: 'hot', price: 58, description: '虾仁饱满，口感Q弹，麻辣鲜香，回味无穷', badge: 'new', image: '宫保虾球,中式美食,新鲜虾仁,辣椒花生,高清摄影' },
    
    // 凉菜 (6道)
    { id: 13, name: '凉拌黄瓜', category: 'cold', price: 12, description: '清爽开胃，酸辣可口，夏季必备，解腻神器', badge: '', image: '凉拌黄瓜,中式凉菜,新鲜黄瓜,蒜香,高清摄影' },
    { id: 14, name: '凉拌木耳', category: 'cold', price: 15, description: '口感爽脆，营养丰富，酸辣开胃，健康之选', badge: '', image: '凉拌木耳,中式凉菜,黑木耳,辣椒,高清摄影' },
    { id: 15, name: '夫妻肺片', category: 'cold', price: 38, description: '麻辣鲜香，口感丰富，川菜经典，下酒好菜', badge: 'hot', image: '夫妻肺片,中式凉菜,牛肉牛肚,辣椒花椒,高清摄影' },
    { id: 16, name: '拍黄瓜', category: 'cold', price: 10, description: '简单美味，清爽解腻，蒜香十足，家常必备', badge: '', image: '拍黄瓜,中式凉菜,黄瓜蒜蓉,高清摄影' },
    { id: 17, name: '凉拌海带丝', category: 'cold', price: 14, description: '爽脆可口，营养丰富，酸辣开胃，低卡健康', badge: '', image: '凉拌海带丝,中式凉菜,海带丝,辣椒蒜香,高清摄影' },
    { id: 18, name: '口水鸡', category: 'cold', price: 42, description: '麻辣鲜香，鸡肉嫩滑，红油透亮，川菜名品', badge: 'recommend', image: '口水鸡,中式凉菜,鸡肉,红油辣椒,高清摄影' },
    
    // 饮品 (6道)
    { id: 19, name: '酸梅汤', category: 'drink', price: 8, description: '酸甜可口，开胃解腻，冰镇更佳，传统饮品', badge: '', image: '酸梅汤,中式饮品,乌梅山楂,冰镇,高清摄影' },
    { id: 20, name: '鲜榨橙汁', category: 'drink', price: 15, description: '新鲜现榨，维C满满，酸甜可口，健康饮品', badge: 'new', image: '鲜榨橙汁,新鲜橙子,榨汁,高清摄影' },
    { id: 21, name: '可乐', category: 'drink', price: 5, description: '经典汽水，冰爽解渴，搭配美食，快乐加倍', badge: '', image: '可乐,汽水饮料,冰镇,高清摄影' },
    { id: 22, name: '雪碧', category: 'drink', price: 5, description: '清爽柠檬味，冰爽解渴，气泡十足，口感极佳', badge: '', image: '雪碧,柠檬汽水,冰镇,高清摄影' },
    { id: 23, name: '奶茶', category: 'drink', price: 12, description: '香浓丝滑，茶香浓郁，甜度适中，休闲必备', badge: 'recommend', image: '奶茶,珍珠奶茶,香浓丝滑,高清摄影' },
    { id: 24, name: '柠檬茶', category: 'drink', price: 10, description: '清新柠檬，茶香四溢，酸甜可口，消暑解渴', badge: '', image: '柠檬茶,新鲜柠檬,红茶,高清摄影' },
    
    // 甜点 (6道)
    { id: 25, name: '芒果班戟', category: 'dessert', price: 18, description: '芒果香甜，奶油绵密，皮薄馅足，甜蜜享受', badge: 'recommend', image: '芒果班戟,芒果奶油,港式甜点,高清摄影' },
    { id: 26, name: '杨枝甘露', category: 'dessert', price: 22, description: '芒果西柚，椰香浓郁，口感丰富，港式经典', badge: 'new', image: '杨枝甘露,芒果西柚,椰奶,港式甜点,高清摄影' },
    { id: 27, name: '双皮奶', category: 'dessert', price: 15, description: '奶香浓郁，口感嫩滑，甜而不腻，传统甜品', badge: '', image: '双皮奶,牛奶甜品,嫩滑,高清摄影' },
    { id: 28, name: '红豆沙', category: 'dessert', price: 12, description: '红豆绵密，香甜可口，温暖身心，经典甜汤', badge: '', image: '红豆沙,红豆甜汤,绵密,高清摄影' },
    { id: 29, name: '提拉米苏', category: 'dessert', price: 25, description: '咖啡香浓，奶油丝滑，层次分明，意式经典', badge: 'recommend', image: '提拉米苏,咖啡蛋糕,意式甜点,高清摄影' },
    { id: 30, name: '冰淇淋', category: 'dessert', price: 10, description: '口感丝滑，口味多样，清凉解暑，夏日必备', badge: '', image: '冰淇淋,草莓巧克力,清凉甜点,高清摄影' }
];

// 购物车数据
let cart = {};

// 当前选中的支付方式
let selectedPaymentMethod = '微信支付';

// 当前订单号
let currentOrderNumber = '';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('餐厅订餐系统加载完成');
    
    // 渲染菜单
    renderMenu('all');
    
    // 更新购物车显示
    updateCartDisplay();
    
    // 初始化订单号
    generateOrderNumber();
});

// 生成订单号
function generateOrderNumber() {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    
    currentOrderNumber = `ORD${year}${month}${day}${random}`;
}

// 渲染菜单
function renderMenu(category) {
    const menuList = document.getElementById('menuList');
    let filteredItems = menuItems;
    
    if (category !== 'all') {
        filteredItems = menuItems.filter(item => item.category === category);
    }
    
    menuList.innerHTML = filteredItems.map(item => {
        const quantity = cart[item.id]?.quantity || 0;
        const badgeClass = item.badge ? `menu-item-badge ${item.badge}` : '';
        const badgeText = item.badge === 'hot' ? '热销' : 
                          item.badge === 'new' ? '新品' : 
                          item.badge === 'recommend' ? '推荐' : '';
        
        return `
            <div class="menu-item" data-category="${item.category}">
                <div class="menu-item-image">
                    <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=${encodeURIComponent(item.image)}&image_size=square" alt="${item.name}">
                    ${item.badge ? `<div class="${badgeClass}">${badgeText}</div>` : ''}
                </div>
                <div class="menu-item-content">
                    <div>
                        <h4 class="menu-item-name">${item.name}</h4>
                        <p class="menu-item-description">${item.description}</p>
                    </div>
                    <div class="menu-item-footer">
                        <span class="menu-item-price">¥${item.price}<span class="unit">/份</span></span>
                        <div class="quantity-control">
                            ${quantity > 0 ? `
                                <button class="quantity-btn" onclick="decreaseQuantity(${item.id})">-</button>
                                <span class="quantity-value">${quantity}</span>
                            ` : ''}
                            <button class="quantity-btn add" onclick="increaseQuantity(${item.id})">+</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 切换分类
function filterCategory(category) {
    // 更新标签样式
    const tabs = document.querySelectorAll('.category-tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 重新渲染菜单
    renderMenu(category);
}

// 增加数量
function increaseQuantity(itemId) {
    if (!cart[itemId]) {
        const item = menuItems.find(i => i.id === itemId);
        cart[itemId] = {
            id: item.id,
            name: item.name,
            price: item.price,
            image: item.image,
            quantity: 0
        };
    }
    
    cart[itemId].quantity++;
    updateCartDisplay();
    
    // 获取当前分类
    const activeTab = document.querySelector('.category-tab.active');
    const category = activeTab ? activeTab.getAttribute('onclick').match(/'([^']+)'/)[1] : 'all';
    renderMenu(category);
}

// 减少数量
function decreaseQuantity(itemId) {
    if (cart[itemId] && cart[itemId].quantity > 0) {
        cart[itemId].quantity--;
        
        if (cart[itemId].quantity === 0) {
            delete cart[itemId];
        }
        
        updateCartDisplay();
        
        // 获取当前分类
        const activeTab = document.querySelector('.category-tab.active');
        const category = activeTab ? activeTab.getAttribute('onclick').match(/'([^']+)'/)[1] : 'all';
        renderMenu(category);
    }
}

// 更新购物车显示
function updateCartDisplay() {
    // 计算总数量和总金额
    let totalQuantity = 0;
    let totalPrice = 0;
    
    Object.values(cart).forEach(item => {
        totalQuantity += item.quantity;
        totalPrice += item.price * item.quantity;
    });
    
    // 更新顶部购物车图标
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        cartCount.textContent = totalQuantity;
        cartCount.style.display = totalQuantity > 0 ? 'flex' : 'none';
    }
    
    // 更新底部购物车
    const cartCountBig = document.querySelector('.cart-count-big');
    const cartTotal = document.querySelector('.cart-total');
    const cartCountText = document.querySelector('.cart-count-text');
    const confirmBtn = document.querySelector('.confirm-btn');
    
    if (cartCountBig) {
        cartCountBig.textContent = totalQuantity;
        cartCountBig.style.display = totalQuantity > 0 ? 'flex' : 'none';
    }
    
    if (cartTotal) {
        cartTotal.textContent = `¥${totalPrice.toFixed(2)}`;
    }
    
    if (cartCountText) {
        cartCountText.textContent = `共${totalQuantity}件商品`;
    }
    
    // 更新确认按钮状态
    if (confirmBtn) {
        if (totalQuantity === 0) {
            confirmBtn.disabled = true;
        } else {
            confirmBtn.disabled = false;
        }
    }
}

// 显示购物车
function showCart() {
    if (Object.keys(cart).length === 0) {
        alert('购物车是空的，请先选餐');
        return;
    }
    
    renderCartModal();
    const modal = document.getElementById('cartModal');
    modal.classList.add('active');
}

// 关闭购物车
function closeCart() {
    const modal = document.getElementById('cartModal');
    modal.classList.remove('active');
}

// 渲染购物车弹窗
function renderCartModal() {
    const cartItems = document.getElementById('cartItems');
    const modalTotal = document.querySelector('.modal-total .total-value');
    const modalConfirmBtn = document.querySelector('.modal-footer .btn-primary');
    
    // 计算总金额
    let totalPrice = 0;
    Object.values(cart).forEach(item => {
        totalPrice += item.price * item.quantity;
    });
    
    // 渲染购物车列表
    cartItems.innerHTML = Object.values(cart).map(item => `
        <div class="cart-item">
            <div class="cart-item-image">
                <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=${encodeURIComponent(item.image)}&image_size=square" alt="${item.name}">
            </div>
            <div class="cart-item-info">
                <h4 class="cart-item-name">${item.name}</h4>
                <p class="cart-item-price">¥${item.price} × ${item.quantity} = ¥${item.price * item.quantity}</p>
            </div>
            <div class="quantity-control">
                <button class="quantity-btn" onclick="decreaseQuantity(${item.id}); renderCartModal(); updateCartDisplay();">-</button>
                <span class="quantity-value">${item.quantity}</span>
                <button class="quantity-btn add" onclick="increaseQuantity(${item.id}); renderCartModal(); updateCartDisplay();">+</button>
            </div>
        </div>
    `).join('');
    
    // 更新总金额
    if (modalTotal) {
        modalTotal.textContent = `¥${totalPrice.toFixed(2)}`;
    }
    
    // 更新按钮状态
    if (modalConfirmBtn) {
        if (Object.keys(cart).length === 0) {
            modalConfirmBtn.disabled = true;
        } else {
            modalConfirmBtn.disabled = false;
        }
    }
}

// 页面历史栈
let pageHistory = ['menu'];

// 返回功能
function goBack() {
    if (pageHistory.length > 1) {
        pageHistory.pop();
        const previousPage = pageHistory[pageHistory.length - 1];
        switchPage(previousPage, false);
    }
}

// 页面切换
function switchPage(pageName, addToHistory = true) {
    const pages = document.querySelectorAll('.page');
    
    pages.forEach(page => {
        page.classList.remove('active');
    });
    
    document.getElementById(pageName).classList.add('active');
    
    // 添加到历史栈
    if (addToHistory) {
        pageHistory.push(pageName);
    }
    
    // 更新导航栏
    updateNavigation(pageName);
    
    // 根据页面执行不同操作
    if (pageName === 'menu') {
        // 回到菜单页面
    } else if (pageName === 'booking') {
        // 渲染预订页面
        renderBookingPage();
    } else if (pageName === 'payment') {
        // 渲染付款页面
        renderPaymentPage();
    } else if (pageName === 'aftersale') {
        // 渲染售后页面
        renderAftersalePage();
    }
}

// 更新导航栏
function updateNavigation(pageName) {
    const pageTitle = document.getElementById('pageTitle');
    const backBtnNav = document.getElementById('backBtnNav');
    const cartIconNav = document.getElementById('cartIconNav');
    
    const titles = {
        'menu': '美味餐厅',
        'booking': '预订确认',
        'payment': '订单支付',
        'aftersale': '订单完成'
    };
    
    // 更新标题
    if (pageTitle) {
        pageTitle.textContent = titles[pageName] || '美味餐厅';
    }
    
    // 显示/隐藏返回按钮
    if (backBtnNav) {
        if (pageName === 'menu') {
            backBtnNav.style.display = 'none';
        } else {
            backBtnNav.style.display = 'flex';
        }
    }
    
    // 显示/隐藏购物车图标
    if (cartIconNav) {
        if (pageName === 'menu') {
            cartIconNav.style.display = 'flex';
        } else {
            cartIconNav.style.display = 'none';
        }
    }
}

// 去预订
function goToBooking() {
    if (Object.keys(cart).length === 0) {
        alert('请先选择菜品');
        return;
    }
    
    closeCart();
    switchPage('booking');
}

// 渲染预订页面
function renderBookingPage() {
    const selectedItems = document.getElementById('selectedItems');
    const totalQuantity = document.getElementById('totalQuantity');
    const bookingTotal = document.getElementById('bookingTotal');
    const bookingBtn = document.querySelector('.btn-primary');
    
    // 计算总数量和总金额
    let totalQty = 0;
    let totalPrice = 0;
    
    Object.values(cart).forEach(item => {
        totalQty += item.quantity;
        totalPrice += item.price * item.quantity;
    });
    
    // 渲染已选菜品
    selectedItems.innerHTML = Object.values(cart).map(item => `
        <div class="list-item">
            <div class="list-item-image">
                <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=${encodeURIComponent(item.image)}&image_size=square" alt="${item.name}">
            </div>
            <div class="list-item-info">
                <h4 class="list-item-name">${item.name}</h4>
                <p class="list-item-price">¥${item.price} × ${item.quantity} = ¥${item.price * item.quantity}</p>
            </div>
            <div class="list-item-quantity">
                <button class="quantity-btn" onclick="decreaseQuantity(${item.id}); renderBookingPage(); updateCartDisplay();">-</button>
                <span class="quantity-value">${item.quantity}</span>
                <button class="quantity-btn add" onclick="increaseQuantity(${item.id}); renderBookingPage(); updateCartDisplay();">+</button>
            </div>
        </div>
    `).join('');
    
    // 更新总数量和总金额
    if (totalQuantity) {
        totalQuantity.textContent = `${totalQty} 件`;
    }
    
    if (bookingTotal) {
        bookingTotal.textContent = `¥${totalPrice.toFixed(2)}`;
    }
    
    // 更新按钮状态
    if (bookingBtn) {
        if (Object.keys(cart).length === 0) {
            bookingBtn.disabled = true;
        } else {
            bookingBtn.disabled = false;
        }
    }
}

// 去付款
function goToPayment() {
    if (Object.keys(cart).length === 0) {
        alert('请先选择菜品');
        return;
    }
    
    switchPage('payment');
}

// 渲染付款页面
function renderPaymentPage() {
    const paymentOrderItems = document.getElementById('paymentOrderItems');
    const orderTotalAmount = document.querySelector('.total-amount');
    const orderNumberElement = document.getElementById('orderNumber');
    
    // 计算总金额
    let totalPrice = 0;
    Object.values(cart).forEach(item => {
        totalPrice += item.price * item.quantity;
    });
    
    // 生成新的订单号
    generateOrderNumber();
    
    // 渲染订单菜品
    paymentOrderItems.innerHTML = Object.values(cart).map(item => `
        <div class="order-item">
            <span class="order-item-name">${item.name} × ${item.quantity}</span>
            <span class="order-item-total">¥${(item.price * item.quantity).toFixed(2)}</span>
        </div>
    `).join('');
    
    // 更新总金额
    if (orderTotalAmount) {
        orderTotalAmount.textContent = `¥${totalPrice.toFixed(2)}`;
    }
    
    // 更新订单号
    if (orderNumberElement) {
        orderNumberElement.textContent = currentOrderNumber;
    }
}

// 选择支付方式
function selectPayment(element) {
    // 移除所有选中状态
    const paymentMethods = document.querySelectorAll('.payment-option');
    paymentMethods.forEach(method => {
        method.classList.remove('active');
        const radioCircle = method.querySelector('.radio-circle');
        if (radioCircle) {
            radioCircle.classList.remove('checked');
        }
    });
    
    // 设置当前选中状态
    element.classList.add('active');
    const radioCircle = element.querySelector('.radio-circle');
    if (radioCircle) {
        radioCircle.classList.add('checked');
    }
    
    // 记录选中的支付方式
    const paymentName = element.querySelector('.payment-name');
    if (paymentName) {
        selectedPaymentMethod = paymentName.textContent;
    }
}

// 完成支付
function completePayment() {
    // 模拟支付处理
    const payBtn = document.querySelector('#payment .btn-primary');
    payBtn.textContent = '支付中...';
    payBtn.disabled = true;
    
    // 模拟支付延迟
    setTimeout(() => {
        // 支付成功，跳转到售后页面
        switchPage('aftersale');
        
        // 重置按钮状态
        payBtn.textContent = '立即支付';
        payBtn.disabled = false;
    }, 1500);
}

// 渲染售后页面
function renderAftersalePage() {
    const aftersaleOrderNumber = document.getElementById('aftersaleOrderNumber');
    const aftersaleAmount = document.getElementById('aftersaleAmount');
    const aftersalePaymentMethod = document.getElementById('aftersalePaymentMethod');
    const aftersaleTime = document.getElementById('aftersaleTime');
    
    // 计算总金额
    let totalPrice = 0;
    Object.values(cart).forEach(item => {
        totalPrice += item.price * item.quantity;
    });
    
    // 获取当前时间
    const now = new Date();
    const timeString = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    
    // 更新页面信息
    if (aftersaleOrderNumber) {
        aftersaleOrderNumber.textContent = currentOrderNumber;
    }
    
    if (aftersaleAmount) {
        aftersaleAmount.textContent = `¥${totalPrice.toFixed(2)}`;
    }
    
    if (aftersalePaymentMethod) {
        aftersalePaymentMethod.textContent = selectedPaymentMethod;
    }
    
    if (aftersaleTime) {
        aftersaleTime.textContent = timeString;
    }
}

// 提交配送信息
function submitDeliveryInfo() {
    const name = document.getElementById('customerName').value;
    const phone = document.getElementById('customerPhone').value;
    const address = document.getElementById('customerAddress').value;
    const deliveryTime = document.getElementById('deliveryTime').value;
    const remarks = document.getElementById('remarks').value;
    
    // 简单验证
    if (!name.trim()) {
        alert('请输入姓名');
        return;
    }
    
    if (!phone.trim()) {
        alert('请输入联系电话');
        return;
    }
    
    if (!address.trim()) {
        alert('请输入配送地址');
        return;
    }
    
    // 验证手机号格式
    const phoneRegex = /^1[3-9]\d{9}$/;
    if (!phoneRegex.test(phone.trim())) {
        alert('请输入正确的手机号码');
        return;
    }
    
    // 模拟提交
    const submitBtn = document.querySelector('#aftersale .btn-primary');
    submitBtn.textContent = '提交中...';
    submitBtn.disabled = true;
    
    setTimeout(() => {
        alert('配送信息提交成功！\n\n订单号：' + currentOrderNumber + '\n收货人：' + name + '\n联系电话：' + phone + '\n配送地址：' + address);
        
        // 重置按钮状态
        submitBtn.textContent = '提交配送信息';
        submitBtn.disabled = false;
    }, 1000);
}

// 继续购物
function continueShopping() {
    // 清空购物车
    cart = {};
    
    // 更新购物车显示
    updateCartDisplay();
    
    // 重新渲染菜单
    renderMenu('all');
    
    // 重置分类标签
    const tabs = document.querySelectorAll('.category-tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('onclick').includes("'all'")) {
            tab.classList.add('active');
        }
    });
    
    // 切换到菜单页面
    switchPage('menu');
}

// 点击弹窗外部关闭
document.addEventListener('click', function(event) {
    const modal = document.getElementById('cartModal');
    if (event.target === modal) {
        closeCart();
    }
});
