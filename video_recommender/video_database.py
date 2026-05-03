import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Video:
    id: str
    title: str
    description: str
    tags: List[str]
    category: str
    duration: int  # 秒
    views: int
    likes: int
    thumbnail_url: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class VideoDatabase:
    def __init__(self):
        self.videos: Dict[str, Video] = {}
        self._init_sample_videos()

    def _init_sample_videos(self):
        sample_videos = [
            # 科技类
            Video(
                id="v001",
                title="人工智能在日常生活中的应用",
                description="探索AI如何改变我们的日常生活，从智能家居到自动驾驶",
                tags=["人工智能", "AI", "科技", "智能生活"],
                category="科技",
                duration=600,
                views=150000,
                likes=12000
            ),
            Video(
                id="v002",
                title="Python编程入门教程",
                description="从零开始学习Python编程，适合新手入门",
                tags=["Python", "编程", "入门", "教程"],
                category="教育",
                duration=1800,
                views=250000,
                likes=20000
            ),
            Video(
                id="v003",
                title="最新智能手机深度评测",
                description="全面评测2024年最新旗舰智能手机的性能和功能",
                tags=["手机", "评测", "科技", "数码"],
                category="数码",
                duration=900,
                views=500000,
                likes=35000
            ),
            Video(
                id="v004",
                title="虚拟现实游戏体验",
                description="沉浸在最新的VR游戏世界中的真实体验",
                tags=["VR", "虚拟现实", "游戏", "科技"],
                category="游戏",
                duration=1200,
                views=180000,
                likes=15000
            ),
            Video(
                id="v005",
                title="大数据分析实战",
                description="使用Python进行数据分析和可视化的实战课程",
                tags=["数据分析", "Python", "大数据", "可视化"],
                category="教育",
                duration=2400,
                views=120000,
                likes=9500
            ),
            # 娱乐类
            Video(
                id="v006",
                title="热门电影深度解析",
                description="深入分析最新热门电影的剧情和幕后故事",
                tags=["电影", "解析", "娱乐", "影评"],
                category="娱乐",
                duration=1500,
                views=800000,
                likes=65000
            ),
            Video(
                id="v007",
                title="音乐制作全过程",
                description="从创作到发行，完整的音乐制作流程揭秘",
                tags=["音乐", "制作", "创作", "娱乐"],
                category="音乐",
                duration=1800,
                views=300000,
                likes=25000
            ),
            Video(
                id="v008",
                title="旅行vlog：探索日本京都",
                description="跟随我们的镜头，一起探索日本京都的美景和文化",
                tags=["旅行", "日本", "京都", "vlog"],
                category="旅游",
                duration=1200,
                views=450000,
                likes=40000
            ),
            Video(
                id="v009",
                title="美食探店：最正宗的川菜馆",
                description="寻找城市里最正宗的川菜馆，品尝地道的麻辣美食",
                tags=["美食", "川菜", "探店", "美食vlog"],
                category="美食",
                duration=900,
                views=600000,
                likes=50000
            ),
            Video(
                id="v010",
                title="游戏攻略：热门游戏通关技巧",
                description="分享最新热门游戏的通关技巧和隐藏彩蛋",
                tags=["游戏", "攻略", "技巧", "通关"],
                category="游戏",
                duration=2100,
                views=350000,
                likes=30000
            ),
            # 健康生活类
            Video(
                id="v011",
                title="居家健身30分钟",
                description="不需要器材，在家也能完成的高效健身训练",
                tags=["健身", "运动", "健康", "居家"],
                category="健身",
                duration=1800,
                views=900000,
                likes=75000
            ),
            Video(
                id="v012",
                title="健康饮食：营养搭配指南",
                description="学习如何科学搭配每日饮食，保持身体健康",
                tags=["饮食", "营养", "健康", "搭配"],
                category="健康",
                duration=1200,
                views=400000,
                likes=35000
            ),
            Video(
                id="v013",
                title="冥想减压入门",
                description="学习基础冥想技巧，缓解日常压力和焦虑",
                tags=["冥想", "减压", "心理健康", "放松"],
                category="健康",
                duration=900,
                views=250000,
                likes=20000
            ),
            Video(
                id="v014",
                title="瑜伽初学者教程",
                description="适合瑜伽初学者的基础动作教学",
                tags=["瑜伽", "健身", "柔韧", "入门"],
                category="健身",
                duration=1500,
                views=500000,
                likes=45000
            ),
            Video(
                id="v015",
                title="睡眠质量提升技巧",
                description="分享改善睡眠质量的实用方法和技巧",
                tags=["睡眠", "健康", "生活", "技巧"],
                category="生活",
                duration=600,
                views=300000,
                likes=25000
            ),
            # 更多科技类
            Video(
                id="v016",
                title="机器学习算法详解",
                description="深入理解机器学习核心算法的原理和应用",
                tags=["机器学习", "算法", "AI", "数据科学"],
                category="教育",
                duration=2400,
                views=180000,
                likes=16000
            ),
            Video(
                id="v017",
                title="前端开发：React实战",
                description="学习使用React构建现代化Web应用",
                tags=["React", "前端", "JavaScript", "Web开发"],
                category="教育",
                duration=3000,
                views=200000,
                likes=18000
            ),
            Video(
                id="v018",
                title="无人机摄影技巧",
                description="学习使用无人机拍摄震撼的航拍视频",
                tags=["无人机", "摄影", "航拍", "技巧"],
                category="摄影",
                duration=1200,
                views=350000,
                likes=30000
            ),
            Video(
                id="v019",
                title="网络安全基础",
                description="了解网络安全基础知识，保护个人信息安全",
                tags=["网络安全", "安全", "隐私", "技术"],
                category="科技",
                duration=1500,
                views=150000,
                likes=12000
            ),
            Video(
                id="v020",
                title="云计算入门",
                description="了解云计算的基本概念和主流云服务平台",
                tags=["云计算", "云服务", "AWS", "阿里云"],
                category="科技",
                duration=1800,
                views=120000,
                likes=10000
            ),
            # 更多娱乐类
            Video(
                id="v021",
                title="脱口秀精选合集",
                description="经典脱口秀表演精选，让你笑不停",
                tags=["脱口秀", "喜剧", "搞笑", "娱乐"],
                category="娱乐",
                duration=2400,
                views=1200000,
                likes=95000
            ),
            Video(
                id="v022",
                title="舞蹈教学：热门流行舞",
                description="学习当前最热门的流行舞蹈动作",
                tags=["舞蹈", "流行舞", "教学", "娱乐"],
                category="舞蹈",
                duration=1800,
                views=600000,
                likes=50000
            ),
            Video(
                id="v023",
                title="宠物日常：萌宠治愈瞬间",
                description="记录可爱宠物的日常瞬间，治愈你的心灵",
                tags=["宠物", "萌宠", "猫咪", "狗狗"],
                category="萌宠",
                duration=600,
                views=800000,
                likes=70000
            ),
            Video(
                id="v024",
                title="手工DIY：创意装饰品",
                description="学习制作精美的手工装饰品，点缀你的生活",
                tags=["手工", "DIY", "创意", "装饰"],
                category="生活",
                duration=1200,
                views=400000,
                likes=35000
            ),
            Video(
                id="v025",
                title="咖啡制作教程",
                description="从咖啡豆到一杯完美咖啡的全过程",
                tags=["咖啡", "制作", "教程", "生活"],
                category="美食",
                duration=900,
                views=250000,
                likes=20000
            )
        ]
        
        for video in sample_videos:
            self.videos[video.id] = video

    def get_video(self, video_id: str) -> Optional[Video]:
        return self.videos.get(video_id)

    def get_all_videos(self) -> List[Video]:
        return list(self.videos.values())

    def get_videos_by_ids(self, video_ids: List[str]) -> List[Video]:
        return [self.videos[vid] for vid in video_ids if vid in self.videos]

    def get_videos_by_category(self, category: str) -> List[Video]:
        return [v for v in self.videos.values() if v.category == category]

    def search_videos(self, query: str) -> List[Video]:
        query_lower = query.lower()
        results = []
        for video in self.videos.values():
            if (query_lower in video.title.lower() or
                query_lower in video.description.lower() or
                any(query_lower in tag.lower() for tag in video.tags) or
                query_lower in video.category.lower()):
                results.append(video)
        return results

    def get_popular_videos(self, limit: int = 10) -> List[Video]:
        sorted_videos = sorted(
            self.videos.values(),
            key=lambda v: (v.views, v.likes),
            reverse=True
        )
        return sorted_videos[:limit]

    def to_json(self) -> str:
        return json.dumps([v.to_dict() for v in self.videos.values()], ensure_ascii=False, indent=2)
