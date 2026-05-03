import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from video_database import Video, VideoDatabase
from recommendation_engine import ContentBasedRecommender


@dataclass
class UserSession:
    user_id: str
    current_round: int = 0
    initial_preference: str = ""
    liked_video_ids: List[str] = field(default_factory=list)
    disliked_video_ids: List[str] = field(default_factory=list)
    seen_video_ids: List[str] = field(default_factory=list)
    recommendation_history: Dict[int, List[Dict]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class VideoRecommenderApp:
    def __init__(self):
        self.video_db = VideoDatabase()
        self.recommender = ContentBasedRecommender(self.video_db)
        self.sessions: Dict[str, UserSession] = {}

    def create_session(self, user_id: str) -> UserSession:
        if user_id in self.sessions:
            return self.sessions[user_id]
        
        session = UserSession(user_id=user_id)
        self.sessions[user_id] = session
        return session

    def get_session(self, user_id: str) -> Optional[UserSession]:
        return self.sessions.get(user_id)

    def format_video_info(self, video: Video, score: float = 0.0, index: int = 0) -> Dict:
        minutes = video.duration // 60
        seconds = video.duration % 60
        
        return {
            "index": index,
            "id": video.id,
            "title": video.title,
            "description": video.description[:100] + "..." if len(video.description) > 100 else video.description,
            "tags": video.tags,
            "category": video.category,
            "duration": f"{minutes}:{seconds:02d}",
            "views": f"{video.views:,}",
            "likes": f"{video.likes:,}",
            "relevance_score": round(score, 4)
        }

    def start_first_round(self, user_id: str, preference: str) -> Dict:
        session = self.create_session(user_id)
        session.initial_preference = preference
        session.current_round = 1

        recommendations = self.recommender.recommend_by_query(
            query=preference,
            exclude_ids=session.seen_video_ids,
            limit=6
        )

        video_list = []
        for i, (video, score) in enumerate(recommendations, 1):
            video_info = self.format_video_info(video, score, i)
            video_list.append(video_info)
            session.seen_video_ids.append(video.id)

        session.recommendation_history[session.current_round] = video_list

        return {
            "success": True,
            "user_id": user_id,
            "round": session.current_round,
            "is_first_round": True,
            "initial_preference": preference,
            "recommendations": video_list,
            "message": f"第 {session.current_round} 轮推荐已生成，请选择您喜欢的视频（至少选择1个）"
        }

    def process_selection(self, user_id: str, selected_indices: List[int]) -> Dict:
        session = self.get_session(user_id)
        
        if not session:
            return {
                "success": False,
                "message": "用户会话不存在，请先开始推荐"
            }

        if session.current_round not in session.recommendation_history:
            return {
                "success": False,
                "message": "当前轮次没有推荐记录"
            }

        current_recommendations = session.recommendation_history[session.current_round]

        if not selected_indices:
            available_indices = [v["index"] for v in current_recommendations]
            return {
                "success": False,
                "message": f"请至少选择1个视频，可用编号: {available_indices}"
            }

        valid_indices = [v["index"] for v in current_recommendations]
        invalid_indices = [idx for idx in selected_indices if idx not in valid_indices]
        
        if invalid_indices:
            return {
                "success": False,
                "message": f"无效的选择编号: {invalid_indices}，请从以下编号中选择: {valid_indices}"
            }

        selected_videos = [v for v in current_recommendations if v["index"] in selected_indices]
        
        for video in selected_videos:
            if video["id"] not in session.liked_video_ids:
                session.liked_video_ids.append(video["id"])

        return {
            "success": True,
            "user_id": user_id,
            "round": session.current_round,
            "selected_videos": selected_videos,
            "total_liked_count": len(session.liked_video_ids),
            "message": f"已选择 {len(selected_videos)} 个视频，正在为您生成下一轮推荐..."
        }

    def generate_next_round(self, user_id: str) -> Dict:
        session = self.get_session(user_id)
        
        if not session:
            return {
                "success": False,
                "message": "用户会话不存在"
            }

        if not session.liked_video_ids:
            return {
                "success": False,
                "message": "没有已选择的视频记录，请先选择您喜欢的视频"
            }

        session.current_round += 1

        recommendations = self.recommender.recommend_by_history(
            liked_video_ids=session.liked_video_ids,
            exclude_ids=session.seen_video_ids,
            limit=6
        )

        if not recommendations:
            recommendations = self.recommender.recommend_by_query(
                query=session.initial_preference,
                exclude_ids=session.seen_video_ids,
                limit=6
            )

        video_list = []
        for i, (video, score) in enumerate(recommendations, 1):
            video_info = self.format_video_info(video, score, i)
            video_list.append(video_info)
            session.seen_video_ids.append(video.id)

        session.recommendation_history[session.current_round] = video_list

        user_profile = self._analyze_user_profile(session)

        return {
            "success": True,
            "user_id": user_id,
            "round": session.current_round,
            "is_first_round": False,
            "recommendations": video_list,
            "user_profile": user_profile,
            "message": f"第 {session.current_round} 轮推荐已生成（基于您的喜好），请选择您喜欢的视频（至少选择1个）"
        }

    def _analyze_user_profile(self, session: UserSession) -> Dict:
        liked_videos = self.video_db.get_videos_by_ids(session.liked_video_ids)
        
        categories = []
        tags = []
        
        for video in liked_videos:
            categories.append(video.category)
            tags.extend(video.tags)
        
        from collections import Counter
        
        category_counter = Counter(categories)
        tag_counter = Counter(tags)
        
        top_categories = category_counter.most_common(3)
        top_tags = tag_counter.most_common(5)
        
        return {
            "total_liked": len(liked_videos),
            "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
            "favorite_category": top_categories[0][0] if top_categories else None
        }

    def get_user_history(self, user_id: str) -> Dict:
        session = self.get_session(user_id)
        
        if not session:
            return {
                "success": False,
                "message": "用户会话不存在"
            }

        user_profile = self._analyze_user_profile(session)

        return {
            "success": True,
            "user_id": user_id,
            "current_round": session.current_round,
            "initial_preference": session.initial_preference,
            "user_profile": user_profile,
            "liked_videos": [
                self.format_video_info(self.video_db.get_video(vid), 1.0, i+1)
                for i, vid in enumerate(session.liked_video_ids)
                if self.video_db.get_video(vid)
            ],
            "recommendation_history": session.recommendation_history
        }

    def reset_session(self, user_id: str) -> Dict:
        if user_id in self.sessions:
            del self.sessions[user_id]
        
        return {
            "success": True,
            "message": f"用户 {user_id} 的会话已重置，可以重新开始推荐"
        }


class CLInterface:
    def __init__(self):
        self.app = VideoRecommenderApp()

    def print_recommendations(self, recommendations: List[Dict]):
        print("\n" + "="*80)
        print("推荐视频列表:")
        print("="*80)
        
        for video in recommendations:
            print(f"\n【{video['index']}】 {video['title']}")
            print(f"    分类: {video['category']} | 时长: {video['duration']}")
            print(f"    播放: {video['views']} | 点赞: {video['likes']}")
            print(f"    标签: {', '.join(video['tags'])}")
            print(f"    简介: {video['description']}")
            print(f"    相关度: {video['relevance_score']}")

    def print_user_profile(self, profile: Dict):
        print("\n" + "-"*80)
        print("您的用户画像:")
        print("-"*80)
        print(f"已喜欢视频数量: {profile['total_liked']}")
        print(f"最喜欢的分类: {profile['favorite_category']}")
        
        if profile['top_categories']:
            print("\n热门分类:")
            for cat in profile['top_categories']:
                print(f"  - {cat['category']}: {cat['count']}个视频")
        
        if profile['top_tags']:
            print("\n热门标签:")
            for tag in profile['top_tags']:
                print(f"  - {tag['tag']}: {tag['count']}次")

    def run(self):
        print("="*80)
        print("         视频推荐系统")
        print("="*80)
        print("\n欢迎使用视频推荐系统！")
        print("系统将根据您的喜好进行多轮视频推荐。")
        print("每轮将推荐至少5个视频，您需要至少选择1个喜欢的视频。")
        
        user_id = input("\n请输入您的用户ID: ").strip()
        if not user_id:
            user_id = "default_user"

        print("\n" + "="*80)
        print("第1轮 - 初始推荐")
        print("="*80)
        
        preference = input("\n请描述您喜欢的视频类型（例如：'我喜欢看科技类视频，特别是人工智能相关的'）: ").strip()
        
        while not preference:
            preference = input("请输入有效的视频偏好描述: ").strip()

        result = self.app.start_first_round(user_id, preference)
        
        if not result["success"]:
            print(f"错误: {result['message']}")
            return

        self.print_recommendations(result["recommendations"])

        while True:
            print("\n" + "-"*80)
            print(f"当前轮次: 第 {result['round']} 轮")
            print("-"*80)
            
            selection_input = input("\n请选择您喜欢的视频编号（用逗号分隔，例如: 1,3,5）: ").strip()
            
            while not selection_input:
                selection_input = input("请至少选择1个视频编号: ").strip()

            try:
                selected_indices = [int(idx.strip()) for idx in selection_input.split(",") if idx.strip()]
            except ValueError:
                print("输入格式错误，请输入数字，用逗号分隔")
                continue

            select_result = self.app.process_selection(user_id, selected_indices)
            
            if not select_result["success"]:
                print(f"错误: {select_result['message']}")
                continue

            print(f"\n✓ {select_result['message']}")
            print(f"已选择的视频: {[v['title'] for v in select_result['selected_videos']]}")

            next_result = self.app.generate_next_round(user_id)
            
            if not next_result["success"]:
                print(f"错误: {next_result['message']}")
                break

            result = next_result
            self.print_user_profile(result["user_profile"])
            self.print_recommendations(result["recommendations"])

            continue_choice = input("\n是否继续下一轮推荐？(y/n): ").strip().lower()
            
            if continue_choice != 'y':
                print("\n" + "="*80)
                print("推荐结束")
                print("="*80)
                
                history = self.app.get_user_history(user_id)
                if history["success"]:
                    self.print_user_profile(history["user_profile"])
                    
                    print("\n您喜欢的所有视频:")
                    for video in history["liked_videos"]:
                        print(f"  - {video['title']} ({video['category']})")
                
                print("\n感谢使用视频推荐系统！")
                break


if __name__ == "__main__":
    cli = CLInterface()
    cli.run()
