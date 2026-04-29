import re
import math
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
from video_database import Video, VideoDatabase


class TextProcessor:
    def __init__(self):
        self.stop_words = set([
            "的", "是", "在", "了", "和", "与", "或", "这", "那", 
            "有", "为", "以", "及", "等", "上", "下", "中", "里",
            "我", "你", "他", "她", "它", "们", "就", "都", "也",
            "很", "太", "更", "最", "还", "又", "再", "不", "没",
            "吗", "呢", "啊", "吧", "呀", "哦", "嗯", "哈", "嘿",
            "一个", "一些", "一种", "这个", "那个", "什么", "怎么",
            "如何", "为什么", "因为", "所以", "但是", "然而", "如果",
            "就是", "只是", "已经", "正在", "将要", "可以", "能够",
            "会", "要", "想", "看", "听", "说", "做", "来", "去",
            "从", "到", "向", "往", "对于", "关于", "根据", "按照",
            "通过", "经过", "由于", "作为", "成为", "变成", "使用"
        ])

    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
        return tokens

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        return [token for token in tokens if token not in self.stop_words and len(token) > 1]

    def process(self, text: str) -> List[str]:
        tokens = self.tokenize(text)
        return self.remove_stopwords(tokens)


class ContentBasedRecommender:
    def __init__(self, video_db: VideoDatabase):
        self.video_db = video_db
        self.text_processor = TextProcessor()
        self.video_profiles: Dict[str, Dict[str, float]] = {}
        self.idf: Dict[str, float] = {}
        self._build_video_profiles()

    def _build_video_profiles(self):
        all_videos = self.video_db.get_all_videos()
        
        doc_count = defaultdict(int)
        
        for video in all_videos:
            text = f"{video.title} {video.description} {' '.join(video.tags)} {video.category}"
            tokens = self.text_processor.process(text)
            token_set = set(tokens)
            for token in token_set:
                doc_count[token] += 1
        
        n_videos = len(all_videos)
        for token, count in doc_count.items():
            self.idf[token] = math.log(n_videos / (count + 1))
        
        for video in all_videos:
            text = f"{video.title} {video.description} {' '.join(video.tags)} {video.category}"
            tokens = self.text_processor.process(text)
            token_counts = Counter(tokens)
            
            profile = {}
            max_tf = max(token_counts.values()) if token_counts else 1
            
            for token, count in token_counts.items():
                tf = 0.5 + 0.5 * (count / max_tf)
                idf = self.idf.get(token, 0)
                profile[token] = tf * idf
            
            self.video_profiles[video.id] = profile

    def _build_query_profile(self, query: str) -> Dict[str, float]:
        tokens = self.text_processor.process(query)
        token_counts = Counter(tokens)
        
        profile = {}
        max_tf = max(token_counts.values()) if token_counts else 1
        
        for token, count in token_counts.items():
            tf = 0.5 + 0.5 * (count / max_tf)
            idf = self.idf.get(token, 0)
            profile[token] = tf * idf
        
        return profile

    def _cosine_similarity(self, profile1: Dict[str, float], profile2: Dict[str, float]) -> float:
        common_tokens = set(profile1.keys()) & set(profile2.keys())
        
        if not common_tokens:
            return 0.0
        
        dot_product = sum(profile1[token] * profile2[token] for token in common_tokens)
        
        norm1 = math.sqrt(sum(val ** 2 for val in profile1.values()))
        norm2 = math.sqrt(sum(val ** 2 for val in profile2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def _build_user_profile(self, liked_video_ids: List[str]) -> Dict[str, float]:
        user_profile = defaultdict(float)
        
        for video_id in liked_video_ids:
            if video_id in self.video_profiles:
                video_profile = self.video_profiles[video_id]
                for token, weight in video_profile.items():
                    user_profile[token] += weight
        
        if liked_video_ids:
            for token in user_profile:
                user_profile[token] /= len(liked_video_ids)
        
        return dict(user_profile)

    def recommend_by_query(self, query: str, exclude_ids: List[str] = None, limit: int = 5) -> List[Tuple[Video, float]]:
        if exclude_ids is None:
            exclude_ids = []
        
        query_profile = self._build_query_profile(query)
        
        all_videos = self.video_db.get_all_videos()
        candidates = []
        
        for video in all_videos:
            if video.id in exclude_ids:
                continue
            
            if video.id in self.video_profiles:
                similarity = self._cosine_similarity(query_profile, self.video_profiles[video.id])
                
                popularity_score = (video.views / 1000000) + (video.likes / 10000)
                final_score = similarity * 0.7 + popularity_score * 0.3
                
                candidates.append((video, final_score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]

    def recommend_by_history(self, liked_video_ids: List[str], exclude_ids: List[str] = None, limit: int = 5) -> List[Tuple[Video, float]]:
        if exclude_ids is None:
            exclude_ids = []
        
        if not liked_video_ids:
            popular_videos = self.video_db.get_popular_videos(limit)
            return [(v, 1.0) for v in popular_videos if v.id not in exclude_ids]
        
        user_profile = self._build_user_profile(liked_video_ids)
        
        liked_categories = []
        liked_tags = []
        for video_id in liked_video_ids:
            video = self.video_db.get_video(video_id)
            if video:
                liked_categories.append(video.category)
                liked_tags.extend(video.tags)
        
        category_counter = Counter(liked_categories)
        tag_counter = Counter(liked_tags)
        
        all_videos = self.video_db.get_all_videos()
        candidates = []
        
        for video in all_videos:
            if video.id in exclude_ids:
                continue
            
            if video.id in self.video_profiles:
                similarity = self._cosine_similarity(user_profile, self.video_profiles[video.id])
                
                category_bonus = category_counter.get(video.category, 0) / len(liked_video_ids)
                
                common_tags = set(video.tags) & set(liked_tags)
                tag_bonus = len(common_tags) / max(len(liked_tags), 1) if liked_tags else 0
                
                popularity_score = (video.views / 1000000) + (video.likes / 10000)
                
                final_score = (
                    similarity * 0.5 +
                    category_bonus * 0.2 +
                    tag_bonus * 0.2 +
                    popularity_score * 0.1
                )
                
                candidates.append((video, final_score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]

    def get_similar_videos(self, video_id: str, exclude_ids: List[str] = None, limit: int = 5) -> List[Tuple[Video, float]]:
        if exclude_ids is None:
            exclude_ids = [video_id]
        
        if video_id not in self.video_profiles:
            return []
        
        target_profile = self.video_profiles[video_id]
        target_video = self.video_db.get_video(video_id)
        
        all_videos = self.video_db.get_all_videos()
        candidates = []
        
        for video in all_videos:
            if video.id in exclude_ids:
                continue
            
            if video.id in self.video_profiles:
                similarity = self._cosine_similarity(target_profile, self.video_profiles[video.id])
                
                category_bonus = 0.3 if video.category == target_video.category else 0
                
                final_score = similarity * 0.7 + category_bonus
                
                candidates.append((video, final_score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]
