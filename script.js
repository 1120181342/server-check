// 页面切换功能
function switchPage(pageName) {
    const pages = document.querySelectorAll('.page');
    const navItems = document.querySelectorAll('.nav-item');
    
    pages.forEach(page => {
        page.classList.remove('active');
    });
    
    navItems.forEach(item => {
        item.classList.remove('active');
    });
    
    document.getElementById(pageName).classList.add('active');
    
    const navTexts = {
        'attractions': '热门景点',
        'packages': '旅行套餐',
        'vip': 'VIP专享',
        'profile': '个人中心'
    };
    
    navItems.forEach(item => {
        if (item.querySelector('.nav-label').textContent === navTexts[pageName]) {
            item.classList.add('active');
        }
    });
}

// 订单标签切换
function switchOrderTab(tabType) {
    const orderTabs = document.querySelectorAll('.order-tab');
    
    orderTabs.forEach(tab => {
        tab.classList.remove('active');
    });
    
    event.target.classList.add('active');
    
    console.log('切换到订单标签:', tabType);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('旅行推荐App加载完成');
    
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach((item, index) => {
        item.addEventListener('click', function() {
            const pages = ['attractions', 'packages', 'vip', 'profile'];
            switchPage(pages[index]);
        });
    });
});
