// 天气代码映射表（WMO天气代码）
const WEATHER_CODES = {
    0: { description: '晴朗', icon: '☀️', advice: '天气晴朗，非常适合户外活动' },
    1: { description: '大部晴朗', icon: '🌤️', advice: '大部晴朗，适合户外活动' },
    2: { description: '部分多云', icon: '⛅', advice: '部分多云，适宜出行' },
    3: { description: '多云', icon: '☁️', advice: '多云天气，注意早晚温差' },
    45: { description: '有雾', icon: '🌫️', advice: '有雾，出行请注意安全' },
    48: { description: '雾凇', icon: '🌫️', advice: '雾凇天气，注意保暖' },
    51: { description: '小毛毛雨', icon: '🌧️', advice: '小毛毛雨，建议带伞' },
    53: { description: '毛毛雨', icon: '🌧️', advice: '毛毛雨，建议带伞' },
    55: { description: '大毛毛雨', icon: '🌧️', advice: '大毛毛雨，建议带伞' },
    56: { description: '冻毛毛雨', icon: '🌧️', advice: '冻毛毛雨，注意保暖和防滑' },
    57: { description: '大冻毛毛雨', icon: '🌧️', advice: '大冻毛毛雨，注意保暖和防滑' },
    61: { description: '小雨', icon: '🌧️', advice: '小雨，建议带伞' },
    63: { description: '中雨', icon: '🌧️', advice: '中雨，建议带伞' },
    65: { description: '大雨', icon: '🌧️', advice: '大雨，出行请注意安全' },
    66: { description: '冻雨', icon: '🌧️', advice: '冻雨，注意保暖和防滑' },
    67: { description: '大冻雨', icon: '🌧️', advice: '大冻雨，注意保暖和防滑' },
    71: { description: '小雪', icon: '🌨️', advice: '小雪，注意保暖' },
    73: { description: '中雪', icon: '🌨️', advice: '中雪，注意保暖和防滑' },
    75: { description: '大雪', icon: '❄️', advice: '大雪，注意保暖和防滑' },
    77: { description: '雪粒', icon: '🌨️', advice: '雪粒，注意保暖' },
    80: { description: '小阵雨', icon: '🌦️', advice: '小阵雨，建议带伞' },
    81: { description: '阵雨', icon: '🌦️', advice: '阵雨，建议带伞' },
    82: { description: '大阵雨', icon: '🌦️', advice: '大阵雨，出行请注意安全' },
    85: { description: '小阵雪', icon: '🌨️', advice: '小阵雪，注意保暖' },
    86: { description: '大阵雪', icon: '❄️', advice: '大阵雪，注意保暖和防滑' },
    95: { description: '雷阵雨', icon: '⛈️', advice: '雷阵雨，避免户外活动' },
    96: { description: '雷阵雨伴冰雹', icon: '⛈️', advice: '雷阵雨伴冰雹，避免户外活动' },
    99: { description: '大雷阵雨伴冰雹', icon: '⛈️', advice: '大雷阵雨伴冰雹，避免户外活动' }
};

// 当前位置信息
let currentLocation = {
    lat: 39.9042, // 默认北京
    lon: 116.4074,
    name: '北京'
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('天气预报页面加载完成');
    
    // 初始化默认位置的天气
    getWeatherByCoords(currentLocation.lat, currentLocation.lon, currentLocation.name);
    
    // 绑定搜索框回车事件
    document.getElementById('cityInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchWeather();
        }
    });
});

// 搜索天气
function searchWeather() {
    const cityInput = document.getElementById('cityInput');
    const cityName = cityInput.value.trim();
    
    if (!cityName) {
        alert('请输入城市名称');
        return;
    }
    
    geocodeCity(cityName);
}

// 地理编码：将城市名转换为经纬度
async function geocodeCity(cityName) {
    showLoading();
    hideError();
    hideWeatherContent();
    
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(cityName)}&limit=1&accept-language=zh-CN`,
            {
                headers: {
                    'User-Agent': 'WeatherApp/1.0'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error('地理编码请求失败');
        }
        
        const data = await response.json();
        
        if (data.length === 0) {
            throw new Error('未找到该城市，请检查城市名称是否正确');
        }
        
        const location = data[0];
        const lat = parseFloat(location.lat);
        const lon = parseFloat(location.lon);
        const name = location.display_name.split(',')[0];
        
        currentLocation = { lat, lon, name };
        getWeatherByCoords(lat, lon, name);
        
    } catch (error) {
        console.error('地理编码错误:', error);
        hideLoading();
        showError(error.message || '无法获取城市信息，请稍后重试');
    }
}

// 获取当前位置
function getLocation() {
    if (!navigator.geolocation) {
        alert('您的浏览器不支持地理定位');
        return;
    }
    
    showLoading();
    hideError();
    hideWeatherContent();
    
    navigator.geolocation.getCurrentPosition(
        async function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&accept-language=zh-CN`,
                    {
                        headers: {
                            'User-Agent': 'WeatherApp/1.0'
                        }
                    }
                );
                
                if (!response.ok) {
                    throw new Error('逆地理编码请求失败');
                }
                
                const data = await response.json();
                let name = '当前位置';
                
                if (data.address) {
                    if (data.address.city) {
                        name = data.address.city;
                    } else if (data.address.town) {
                        name = data.address.town;
                    } else if (data.address.county) {
                        name = data.address.county;
                    } else if (data.address.state) {
                        name = data.address.state;
                    }
                }
                
                currentLocation = { lat, lon, name };
                getWeatherByCoords(lat, lon, name);
                
            } catch (error) {
                console.error('逆地理编码错误:', error);
                currentLocation = { lat, lon, name: '当前位置' };
                getWeatherByCoords(lat, lon, '当前位置');
            }
        },
        function(error) {
            console.error('地理定位错误:', error);
            hideLoading();
            
            let errorMessage = '无法获取您的位置';
            switch (error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = '您拒绝了地理定位请求，请手动输入城市名称';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = '位置信息不可用';
                    break;
                case error.TIMEOUT:
                    errorMessage = '获取位置超时';
                    break;
            }
            
            showError(errorMessage);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}

// 根据经纬度获取天气信息
async function getWeatherByCoords(lat, lon, cityName) {
    showLoading();
    
    try {
        const response = await fetch(
            `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,cloud_cover,visibility&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&timezone=auto&forecast_days=7`
        );
        
        if (!response.ok) {
            throw new Error('天气API请求失败');
        }
        
        const data = await response.json();
        console.log('天气数据:', data);
        
        renderWeatherData(data, cityName);
        hideLoading();
        showWeatherContent();
        
    } catch (error) {
        console.error('获取天气信息错误:', error);
        hideLoading();
        showError('无法获取天气信息，请稍后重试');
    }
}

// 渲染天气数据
function renderWeatherData(data, cityName) {
    const current = data.current;
    const daily = data.daily;
    
    // 更新城市名称和日期
    document.getElementById('cityName').textContent = cityName;
    const now = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    document.getElementById('currentDate').textContent = now.toLocaleDateString('zh-CN', options);
    
    // 更新当前天气
    const currentWeatherCode = current.weather_code;
    const currentWeatherInfo = WEATHER_CODES[currentWeatherCode] || { description: '未知', icon: '❓', advice: '' };
    
    document.getElementById('currentWeatherIcon').textContent = currentWeatherInfo.icon;
    document.getElementById('currentTemp').textContent = `${Math.round(current.temperature_2m)}°`;
    document.getElementById('weatherDesc').textContent = currentWeatherInfo.description;
    
    // 更新天气详情
    document.getElementById('humidity').textContent = `${current.relative_humidity_2m}%`;
    document.getElementById('windSpeed').textContent = `${Math.round(current.wind_speed_10m)} km/h`;
    document.getElementById('feelsLike').textContent = `${Math.round(current.apparent_temperature)}°`;
    const visibility = current.visibility ? `${Math.round(current.visibility / 1000)} km` : 'N/A';
    document.getElementById('visibility').textContent = visibility;
    
    // 渲染7天预报
    renderForecast(daily);
    
    // 生成穿搭和出行建议
    generateAdvice(current, daily);
}

// 渲染7天预报
function renderForecast(daily) {
    const forecastContainer = document.getElementById('forecastContainer');
    const today = new Date().toDateString();
    
    let forecastHTML = '';
    
    for (let i = 0; i < daily.time.length; i++) {
        const date = new Date(daily.time[i]);
        const isToday = date.toDateString() === today;
        
        const weatherCode = daily.weather_code[i];
        const weatherInfo = WEATHER_CODES[weatherCode] || { description: '未知', icon: '❓' };
        
        const maxTemp = Math.round(daily.temperature_2m_max[i]);
        const minTemp = Math.round(daily.temperature_2m_min[i]);
        
        const dayOptions = { month: 'short', day: 'numeric' };
        const weekOptions = { weekday: 'short' };
        
        const dateStr = date.toLocaleDateString('zh-CN', dayOptions);
        const weekDay = isToday ? '今天' : date.toLocaleDateString('zh-CN', weekOptions);
        
        const todayClass = isToday ? 'today' : '';
        
        forecastHTML += `
            <div class="forecast-day ${todayClass}">
                <div class="forecast-date">${dateStr}</div>
                <div class="forecast-weekday">${weekDay}</div>
                <div class="forecast-icon">${weatherInfo.icon}</div>
                <div class="forecast-temps">
                    <span class="forecast-temp-max">${maxTemp}°</span>
                    <span class="forecast-temp-min">${minTemp}°</span>
                </div>
                <div class="forecast-desc">${weatherInfo.description}</div>
            </div>
        `;
    }
    
    forecastContainer.innerHTML = forecastHTML;
}

// 生成穿搭和出行建议
function generateAdvice(current, daily) {
    const currentTemp = current.temperature_2m;
    const weatherCode = current.weather_code;
    const humidity = current.relative_humidity_2m;
    const windSpeed = current.wind_speed_10m;
    
    const weatherInfo = WEATHER_CODES[weatherCode] || { advice: '' };
    
    // 穿搭建议
    let clothingAdvice = '';
    if (currentTemp < 5) {
        clothingAdvice = '天气寒冷，建议穿着羽绒服、厚棉衣、厚毛衣等保暖衣物。佩戴帽子、围巾、手套，注意防寒保暖。';
    } else if (currentTemp < 15) {
        clothingAdvice = '天气较凉，建议穿着厚外套、毛衣、风衣等。早晚温差较大，可随身携带薄外套。';
    } else if (currentTemp < 25) {
        clothingAdvice = '天气舒适，建议穿着轻薄外套、长袖衬衫或卫衣。早晚稍凉，可搭配薄外套。';
    } else if (currentTemp < 32) {
        clothingAdvice = '天气温暖，建议穿着短袖衬衫、T恤、短裤等夏季衣物。注意防晒和补水。';
    } else {
        clothingAdvice = '天气炎热，建议穿着清凉透气的衣物，如无袖上衣、短裤、凉鞋等。避免长时间暴晒，注意防暑降温。';
    }
    
    // 特殊天气调整
    if (weatherCode >= 51 && weatherCode <= 67) { // 雨天
        clothingAdvice += ' 建议携带雨具，穿着防水鞋服。';
    }
    if (weatherCode >= 71 && weatherCode <= 86) { // 雪天
        clothingAdvice += ' 下雪天气，注意保暖防滑，穿着防滑鞋。';
    }
    if (windSpeed > 30) {
        clothingAdvice += ' 风力较大，注意防风。';
    }
    
    document.getElementById('clothingAdvice').textContent = clothingAdvice;
    
    // 出行建议
    let travelAdvice = '';
    if (weatherCode === 0 || weatherCode === 1 || weatherCode === 2) { // 晴天或多云
        travelAdvice = '天气良好，非常适合户外活动和出行。建议携带太阳镜、涂抹防晒霜，注意补水。';
    } else if (weatherCode === 3) { // 多云
        travelAdvice = '多云天气，适宜出行。建议随身携带薄外套，注意早晚温差。';
    } else if (weatherCode >= 51 && weatherCode <= 67) { // 雨天
        travelAdvice = '降雨天气，出行请携带雨具。路面湿滑，注意交通安全。尽量减少户外活动。';
    } else if (weatherCode >= 71 && weatherCode <= 86) { // 雪天
        travelAdvice = '降雪天气，出行请注意安全。路面可能结冰，建议选择公共交通。注意保暖防滑。';
    } else if (weatherCode >= 95) { // 雷阵雨
        travelAdvice = '雷雨天气，避免户外活动。远离高大建筑物、树木和水域。注意防雷安全。';
    } else if (weatherCode === 45 || weatherCode === 48) { // 雾天
        travelAdvice = '有雾，能见度较低，出行请注意安全。驾驶车辆请减速慢行，开启雾灯。';
    } else {
        travelAdvice = weatherInfo.advice || '请关注天气变化，合理安排出行。';
    }
    
    if (currentTemp > 35) {
        travelAdvice += ' 高温天气，注意防暑降温，避免长时间暴晒。';
    }
    if (currentTemp < 0) {
        travelAdvice += ' 低温天气，注意防寒保暖。';
    }
    
    document.getElementById('travelAdvice').textContent = travelAdvice;
    
    // 天气提醒
    let weatherAlert = '';
    
    // 计算未来7天的天气趋势
    let hasRain = false;
    let hasSnow = false;
    let hasHighTemp = false;
    let hasLowTemp = false;
    
    for (let i = 0; i < daily.temperature_2m_max.length; i++) {
        if (daily.weather_code[i] >= 51 && daily.weather_code[i] <= 67) {
            hasRain = true;
        }
        if (daily.weather_code[i] >= 71 && daily.weather_code[i] <= 86) {
            hasSnow = true;
        }
        if (daily.temperature_2m_max[i] > 35) {
            hasHighTemp = true;
        }
        if (daily.temperature_2m_min[i] < 0) {
            hasLowTemp = true;
        }
    }
    
    const alerts = [];
    
    if (humidity > 80) {
        alerts.push('空气湿度较高，请注意防潮防霉');
    } else if (humidity < 30) {
        alerts.push('空气干燥，注意补水保湿');
    }
    
    if (windSpeed > 20) {
        alerts.push('风力较大，请注意防风');
    }
    
    if (hasRain) {
        alerts.push('未来几天可能有降雨，建议随身携带雨具');
    }
    
    if (hasSnow) {
        alerts.push('未来几天可能有降雪，注意保暖防滑');
    }
    
    if (hasHighTemp) {
        alerts.push('未来几天高温，注意防暑降温');
    }
    
    if (hasLowTemp) {
        alerts.push('未来几天低温，注意防寒保暖');
    }
    
    // 昼夜温差提醒
    const maxTemp = daily.temperature_2m_max[0];
    const minTemp = daily.temperature_2m_min[0];
    const tempDiff = maxTemp - minTemp;
    
    if (tempDiff > 10) {
        alerts.push(`昼夜温差较大（${Math.round(tempDiff)}°C），请注意适时增减衣物`);
    }
    
    if (alerts.length === 0) {
        alerts.push('未来几天天气稳定，适宜正常活动');
    }
    
    weatherAlert = alerts.join('。') + '。';
    document.getElementById('weatherAlert').textContent = weatherAlert;
}

// 重试搜索
function retrySearch() {
    const cityInput = document.getElementById('cityInput');
    const cityName = cityInput.value.trim();
    
    if (cityName) {
        searchWeather();
    } else {
        getWeatherByCoords(currentLocation.lat, currentLocation.lon, currentLocation.name);
    }
}

// 显示加载状态
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

// 隐藏加载状态
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// 显示错误信息
function showError(message) {
    document.getElementById('error').style.display = 'flex';
    document.getElementById('errorText').textContent = message;
}

// 隐藏错误信息
function hideError() {
    document.getElementById('error').style.display = 'none';
}

// 显示天气内容
function showWeatherContent() {
    document.getElementById('weatherContent').style.display = 'block';
}

// 隐藏天气内容
function hideWeatherContent() {
    document.getElementById('weatherContent').style.display = 'none';
}