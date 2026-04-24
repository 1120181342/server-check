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

// VIP标签切换
function switchVipTab(tabType) {
    const tabBtns = document.querySelectorAll('.search-tabs .tab-btn');
    const premiumPackages = document.getElementById('premium-packages');
    const discountPackages = document.getElementById('discount-packages');
    
    tabBtns.forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (tabType === 'premium') {
        tabBtns[0].classList.add('active');
        premiumPackages.style.display = 'flex';
        discountPackages.style.display = 'none';
    } else {
        tabBtns[1].classList.add('active');
        premiumPackages.style.display = 'none';
        discountPackages.style.display = 'flex';
    }
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

// 景点详情数据
const attractionsData = [
    {
        id: 0,
        title: '万里长城',
        location: '📍 北京市延庆区八达岭镇',
        rating: '⭐ 4.9分 (2856人评价)',
        description: '长城是中国古代的伟大防御工程，被誉为世界七大奇迹之一。八达岭长城是最具代表性的一段，也是游客最多的地方。登上长城，可以俯瞰群山连绵的壮丽景色，感受中华民族的伟大智慧和创造力。\n\n长城始建于春秋战国时期，秦统一六国后将各段长城连接起来，形成了万里长城的雏形。明长城是保存最完整的一段，八达岭长城就属于明长城的一部分。',
        time: '旺季（4月1日-10月31日）：06:30-19:00\n淡季（11月1日-3月31日）：07:30-18:00',
        price: '成人票：¥40（旺季）/ ¥35（淡季）\n学生/老人票：¥20（旺季）/ ¥17.5（淡季）\n\n缆车：单程¥80，往返¥140\n滑车：单程¥60，往返¥100',
        transport: '公共交通：\n1. 乘坐地铁2号线到积水潭站，出站后步行至德胜门公交站，乘坐877路直达八达岭长城。\n2. 在北京北站乘坐S2线城际列车，直达八达岭长城站。\n\n自驾：从市区出发，沿京藏高速（G6）行驶，在八达岭长城出口下高速，全程约70公里。',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=雄伟%20的%20长城%20风景%2C%20阳光%20明媚%2C%20青山%20环绕%2C%20旅行%20摄影&image_size=landscape_4_3'
    },
    {
        id: 1,
        title: '杭州西湖',
        location: '📍 浙江省杭州市西湖区',
        rating: '⭐ 4.8分 (5632人评价)',
        description: '西湖是中国最著名的湖泊之一，被誉为"人间天堂"。一湖秀水，三面云山，历代文人墨客留下了无数赞美西湖的诗篇。西湖四季皆宜，春有苏堤春晓，夏有曲院风荷，秋有平湖秋月，冬有断桥残雪。\n\n西湖景区内有著名的"西湖十景"，其中断桥因《白蛇传》的故事而闻名遐迩，雷峰塔则见证了千年的历史变迁。',
        time: '全天开放（景区内各景点开放时间有所不同）\n\n主要景点开放时间：\n- 雷峰塔：08:00-19:30\n- 岳王庙：07:00-17:30\n- 灵隐寺：07:00-18:00',
        price: '西湖景区免费开放\n\n收费景点：\n- 雷峰塔：¥40\n- 岳王庙：¥25\n- 灵隐寺（含飞来峰）：¥75\n\n游船：手划船¥150/小时，电动船¥55/人',
        transport: '公共交通：\n1. 地铁1号线到龙翔桥站，出站后步行10分钟可到西湖。\n2. 乘坐7路、27路、51路等公交车可直达西湖周边景点。\n\n骑行：西湖周边有大量共享单车租赁点，骑行游西湖是非常受欢迎的方式。\n\n游船：可在湖滨二公园、断桥、岳王庙等码头乘坐游船游览西湖。',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=西湖%20断桥%20风景%2C%20烟雨%20蒙蒙%2C%20荷花%20盛开%2C%20杭州%20旅行&image_size=landscape_4_3'
    },
    {
        id: 2,
        title: '张家界国家森林公园',
        location: '📍 湖南省张家界市武陵源区',
        rating: '⭐ 4.9分 (3256人评价)',
        description: '张家界国家森林公园是中国第一个国家森林公园，以其独特的石英砂岩峰林地貌闻名于世。这里是电影《阿凡达》中"悬浮山"的取景地，奇峰三千，秀水八百，自然奇观令人叹为观止。\n\n景区内有金鞭溪、袁家界、杨家界、天子山等主要景区，每一处都有独特的风景。特别是在雨后初晴时，云海缭绕，仿佛置身仙境。',
        time: '旺季（3月1日-11月30日）：07:00-18:00\n淡季（12月1日-2月28日）：08:00-17:00\n\n环保车运营时间：\n旺季：07:00-19:00\n淡季：08:00-18:00',
        price: '门票：¥225（4天有效）\n优惠票：¥113（学生、60岁以上老人）\n\n索道费用：\n- 百龙天梯：单程¥72\n- 黄石寨索道：单程¥68，往返¥118\n- 天子山索道：单程¥72\n- 杨家界索道：单程¥76',
        transport: '飞机：张家界荷花国际机场，可直达国内多个城市。\n\n火车：张家界站和张家界西站，高铁可直达长沙、武汉、广州等城市。\n\n景区内部交通：\n- 环保车：免费，连接各主要景区\n- 索道/天梯：自愿选择，节省体力\n- 徒步：多条徒步路线，适合户外爱好者',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=张家界%20天门山%2C%20云海%20缭绕%2C%20奇峰%20异石%2C%20壮丽%20自然%20风光&image_size=landscape_4_3'
    },
    {
        id: 3,
        title: '丽江古城',
        location: '📍 云南省丽江市古城区',
        rating: '⭐ 4.7分 (4123人评价)',
        description: '丽江古城是纳西族的古老家园，世界文化遗产，小桥流水，古朴典雅。古城依山傍水，青石板路蜿蜒曲折，纳西族传统建筑保存完好。白天可以漫步古城，感受历史的韵味；夜晚则可以在四方街的酒吧小酌，体验别样的风情。\n\n古城内有木府、黑龙潭、万古楼等著名景点，周边还有玉龙雪山、束河古镇、泸沽湖等值得一游的地方。',
        time: '全天开放\n\n主要景点开放时间：\n- 木府：08:30-17:30\n- 黑龙潭公园：07:00-19:00\n- 万古楼：09:00-22:00\n\n酒吧街：19:00-24:00（部分酒吧营业至凌晨）',
        price: '古城维护费：¥50（有效期7天，部分景点需要查验）\n\n收费景点：\n- 木府：¥60\n- 黑龙潭：免费（需查验古城维护费）\n- 万古楼：¥50\n\n注：进入古城本身不需要门票，但建议购买古城维护费以便游览各景点。',
        transport: '飞机：丽江三义国际机场，距离古城约28公里，有机场大巴直达。\n\n火车：丽江站，距离古城约10公里，可乘坐公交车或出租车。\n\n古城内部：\n- 禁止机动车通行，只能步行\n- 部分路段有电瓶车，可乘坐代步\n\n周边景点：\n- 玉龙雪山：包车或参加一日游\n- 束河古镇：乘坐11路公交车\n- 泸沽湖：约4小时车程，建议参加两日游',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=丽江%20古城%20夜景%2C%20灯火%20阑珊%2C%20纳西%20风格%20建筑%2C%20云南%20旅行&image_size=landscape_4_3'
    }
];

// 套餐详情数据
const packagesData = [
    {
        id: 0,
        title: '三亚5日4晚豪华游',
        duration: '⏰ 5天4晚',
        rating: '⭐ 4.8分 (1256人评价)',
        originalPrice: '¥8999',
        currentPrice: '¥6999',
        features: [
            '全程入住五星级海景酒店，含双早',
            '亚龙湾、蜈支洲岛、天涯海角全涵盖',
            '赠送亚特兰蒂斯水世界门票',
            '含三亚凤凰机场接送机服务',
            '专业导游全程陪同，无强制消费'
        ],
        itinerary: [
            {
                day: 1,
                title: '抵达三亚 - 入住酒店',
                content: '抵达三亚凤凰国际机场，专车接机，前往亚龙湾五星级海景酒店办理入住。下午自由活动，可在酒店海滩休闲。晚餐赠送海鲜BBQ。'
            },
            {
                day: 2,
                title: '蜈支洲岛一日游',
                content: '全天游览蜈支洲岛，体验各种海上娱乐项目（费用自理）。岛上享用自助午餐。下午返回酒店，傍晚可在亚龙湾沙滩欣赏日落。'
            },
            {
                day: 3,
                title: '南山文化区 + 天涯海角',
                content: '上午游览南山文化旅游区，瞻仰108米高的南海观音像。午餐享用素斋。下午游览天涯海角景区，在"天涯""海角"石刻前拍照留念。'
            },
            {
                day: 4,
                title: '亚特兰蒂斯水世界',
                content: '全天自由活动，可选择前往亚特兰蒂斯水世界（门票已含）或免税店购物。晚餐安排海鲜大餐。'
            },
            {
                day: 5,
                title: '自由活动 - 返程',
                content: '上午自由活动，可在酒店享受设施或前往附近海滩。中午办理退房，专车送机，结束愉快旅程。'
            }
        ],
        includes: '【费用包含】\n1. 交通：三亚凤凰机场接送机服务\n2. 住宿：4晚亚龙湾五星级海景酒店（标准间，含双早）\n3. 门票：行程中所列景点首道大门票、蜈支洲岛船票、亚特兰蒂斯水世界门票\n4. 用餐：4早餐3正餐（含海鲜BBQ、海鲜大餐、南山素斋）\n5. 导游：当地优秀导游全程讲解服务\n6. 保险：旅行社责任险及旅游意外险',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=三亚%20海滩%20度假%2C%20阳光%20沙滩%20海浪%2C%20热带%20天堂%2C%20豪华%20酒店&image_size=landscape_4_3'
    },
    {
        id: 1,
        title: '云南大理丽江7日深度游',
        duration: '⏰ 7天6晚',
        rating: '⭐ 4.9分 (856人评价)',
        originalPrice: '¥12999',
        currentPrice: '¥9999',
        features: [
            '昆明、大理、丽江三地深度游览',
            '赠送玉龙雪山大索道门票',
            '一晚入住洱海景特色客栈',
            '含丽江千古情演出门票',
            '24小时管家服务，行程无忧'
        ],
        itinerary: [
            {
                day: 1,
                title: '抵达昆明 - 接机入住',
                content: '抵达昆明长水国际机场，专车接机，入住昆明五星级酒店。晚上可自行前往南屏步行街品尝云南特色小吃。'
            },
            {
                day: 2,
                title: '昆明石林 - 前往大理',
                content: '上午游览世界自然遗产——石林风景区，欣赏"阿诗玛"等奇特造型。午餐后乘高铁前往大理，入住洱海景特色客栈。'
            },
            {
                day: 3,
                title: '大理一日游',
                content: '上午游览大理古城、洋人街，感受千年古城魅力。下午乘坐洱海游船，欣赏苍山洱海美景，游览南诏风情岛。'
            },
            {
                day: 4,
                title: '大理 - 前往丽江',
                content: '上午游览崇圣寺三塔，这是大理的标志性建筑。午餐后乘高铁前往丽江，入住古城附近特色酒店。晚上赠送《丽江千古情》演出。'
            },
            {
                day: 5,
                title: '玉龙雪山一日游',
                content: '全天游览玉龙雪山，乘坐大索道登顶（海拔4680米），观赏壮丽雪景。下午游览蓝月谷，欣赏翡翠般的湖水。'
            },
            {
                day: 6,
                title: '丽江古城 - 束河古镇',
                content: '上午自由漫步丽江古城，四方街、木府、黑龙潭等景点可自由选择。下午游览束河古镇，体验更宁静的纳西族风情。'
            },
            {
                day: 7,
                title: '返程 - 送机',
                content: '根据航班时间，专车送往丽江三义国际机场，结束愉快的云南之旅。'
            }
        ],
        includes: '【费用包含】\n1. 交通：昆明接机、丽江送机，昆明-大理-丽江高铁二等座，当地旅游大巴\n2. 住宿：2晚昆明五星酒店 + 2晚大理海景客栈 + 2晚丽江特色酒店\n3. 门票：石林、洱海游船、崇圣寺三塔、玉龙雪山（含大索道）、蓝月谷、丽江千古情\n4. 用餐：6早餐5正餐（含云南特色餐食）\n5. 导游：当地优秀导游全程讲解\n6. 保险：旅行社责任险及旅游意外险\n7. 服务：24小时管家服务',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=云南%20大理%20丽江%20风景%2C%20玉龙雪山%2C%20古城%20风光%2C%20多彩%20民族%20文化&image_size=landscape_4_3'
    },
    {
        id: 2,
        title: '成都4日3晚美食文化游',
        duration: '⏰ 4天3晚',
        rating: '⭐ 4.8分 (2134人评价)',
        originalPrice: '¥5999',
        currentPrice: '¥4599',
        features: [
            '近距离接触国宝大熊猫',
            '正宗川菜美食体验课程',
            '赠送川剧变脸表演门票',
            '一晚入住青城山温泉酒店',
            '含成都双流机场接送机'
        ],
        itinerary: [
            {
                day: 1,
                title: '抵达成都 - 自由活动',
                content: '抵达成都双流国际机场，专车接机，入住市区五星级酒店。晚上可自行前往锦里古街或宽窄巷子，品尝成都特色小吃。'
            },
            {
                day: 2,
                title: '大熊猫基地 - 都江堰',
                content: '上午游览成都大熊猫繁育研究基地，近距离观看国宝大熊猫。午餐后前往都江堰，参观千年水利工程，感受古人的智慧。晚上入住青城山温泉酒店，享受温泉。'
            },
            {
                day: 3,
                title: '青城山 - 返回成都',
                content: '上午游览青城山，这是道教发源地之一，素有"青城天下幽"的美誉。午餐后返回成都，下午参加川菜烹饪课程，学习制作麻婆豆腐、宫保鸡丁等经典川菜。晚上赠送川剧变脸表演。'
            },
            {
                day: 4,
                title: '自由活动 - 返程',
                content: '上午自由活动，可选择前往春熙路商圈购物，或前往武侯祠、杜甫草堂等人文景点。根据航班时间，专车送机，结束成都美食文化之旅。'
            }
        ],
        includes: '【费用包含】\n1. 交通：成都双流机场接送机服务，当地旅游大巴\n2. 住宿：2晚成都市区五星酒店 + 1晚青城山温泉酒店\n3. 门票：大熊猫繁育研究基地、都江堰、青城山、川剧变脸表演\n4. 用餐：3早餐2正餐（含特色川菜体验）\n5. 活动：川菜烹饪课程体验\n6. 导游：当地优秀导游全程讲解服务\n7. 保险：旅行社责任险及旅游意外险',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=成都%20美食%20之旅%2C%20火锅%20串串%2C%20宽窄%20巷子%2C%20熊猫%20基地&image_size=landscape_4_3'
    }
];

// 显示景点详情弹窗
function showAttractionDetail(index) {
    const attraction = attractionsData[index];
    const modal = document.getElementById('attraction-modal');
    
    document.getElementById('detail-image').src = attraction.image;
    document.getElementById('detail-title').textContent = attraction.title;
    document.getElementById('detail-location').textContent = attraction.location;
    document.getElementById('detail-rating').textContent = attraction.rating;
    document.getElementById('detail-description').textContent = attraction.description;
    document.getElementById('detail-time').textContent = attraction.time;
    document.getElementById('detail-price').textContent = attraction.price;
    document.getElementById('detail-transport').textContent = attraction.transport;
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// 关闭景点详情弹窗
function closeAttractionModal() {
    const modal = document.getElementById('attraction-modal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// 显示套餐详情弹窗
function showPackageDetail(index) {
    const pkg = packagesData[index];
    const modal = document.getElementById('package-modal');
    
    document.getElementById('package-detail-image').src = pkg.image;
    document.getElementById('package-detail-title').textContent = pkg.title;
    document.getElementById('package-detail-duration').textContent = pkg.duration;
    document.getElementById('package-detail-rating').textContent = pkg.rating;
    document.getElementById('package-original-price').textContent = pkg.originalPrice;
    document.getElementById('package-current-price').textContent = pkg.currentPrice;
    
    const featuresList = document.getElementById('package-features');
    featuresList.innerHTML = pkg.features.map(feature => `<li>${feature}</li>`).join('');
    
    const itineraryList = document.getElementById('package-itinerary');
    itineraryList.innerHTML = pkg.itinerary.map(day => `
        <div class="itinerary-day">
            <div class="day-number">${day.day}</div>
            <div class="day-content">
                <h4>${day.title}</h4>
                <p>${day.content}</p>
            </div>
        </div>
    `).join('');
    
    document.getElementById('package-includes').textContent = pkg.includes;
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// 关闭套餐详情弹窗
function closePackageModal() {
    const modal = document.getElementById('package-modal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// 点击弹窗外部关闭
document.addEventListener('click', function(event) {
    const attractionModal = document.getElementById('attraction-modal');
    const packageModal = document.getElementById('package-modal');
    
    if (event.target === attractionModal) {
        closeAttractionModal();
    }
    
    if (event.target === packageModal) {
        closePackageModal();
    }
});

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
