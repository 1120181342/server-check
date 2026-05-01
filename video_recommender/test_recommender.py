import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_database import VideoDatabase, Video
from recommendation_engine import ContentBasedRecommender, TextProcessor
from recommender_app import VideoRecommenderApp, UserSession


def test_video_database():
    print("="*60)
    print("测试视频数据库模块")
    print("="*60)
    
    db = VideoDatabase()
    
    print("\n1. 测试获取所有视频:")
    all_videos = db.get_all_videos()
    print(f"   视频总数: {len(all_videos)}")
    assert len(all_videos) >= 20, "视频数量不足"
    print("   ✓ 通过")
    
    print("\n2. 测试按ID获取视频:")
    video = db.get_video("v001")
    print(f"   视频标题: {video.title}")
    assert video is not None, "未找到视频v001"
    print("   ✓ 通过")
    
    print("\n3. 测试搜索视频:")
    results = db.search_videos("人工智能")
    print(f"   搜索'人工智能'结果数: {len(results)}")
    assert len(results) >= 1, "搜索结果为空"
    print("   ✓ 通过")
    
    print("\n4. 测试按分类获取视频:")
    tech_videos = db.get_videos_by_category("科技")
    print(f"   科技分类视频数: {len(tech_videos)}")
    assert len(tech_videos) >= 1, "科技分类视频为空"
    print("   ✓ 通过")
    
    print("\n5. 测试获取热门视频:")
    popular = db.get_popular_videos(5)
    print(f"   热门视频数: {len(popular)}")
    assert len(popular) == 5, "热门视频数量不正确"
    print("   ✓ 通过")
    
    print("\n✓ 视频数据库模块测试通过!")


def test_text_processor():
    print("\n" + "="*60)
    print("测试文本处理模块")
    print("="*60)
    
    processor = TextProcessor()
    
    print("\n1. 测试分词:")
    text = "我喜欢看人工智能和编程相关的视频"
    tokens = processor.tokenize(text)
    print(f"   原始文本: {text}")
    print(f"   分词结果: {tokens}")
    assert len(tokens) > 0, "分词失败"
    print("   ✓ 通过")
    
    print("\n2. 测试停用词过滤:")
    filtered = processor.remove_stopwords(tokens)
    print(f"   过滤停用词后: {filtered}")
    assert "的" not in filtered, "停用词未过滤"
    print("   ✓ 通过")
    
    print("\n3. 测试完整处理流程:")
    processed = processor.process(text)
    print(f"   完整处理结果: {processed}")
    assert len(processed) > 0, "处理失败"
    print("   ✓ 通过")
    
    print("\n✓ 文本处理模块测试通过!")


def test_recommendation_engine():
    print("\n" + "="*60)
    print("测试推荐引擎模块")
    print("="*60)
    
    db = VideoDatabase()
    recommender = ContentBasedRecommender(db)
    
    print("\n1. 测试基于查询的推荐:")
    results = recommender.recommend_by_query("人工智能 编程", limit=6)
    print(f"   推荐视频数: {len(results)}")
    assert len(results) >= 5, "推荐数量不足5个"
    
    print("\n   推荐结果:")
    for i, (video, score) in enumerate(results, 1):
        print(f"   {i}. {video.title} (相关度: {score:.4f})")
    print("   ✓ 通过")
    
    print("\n2. 测试基于历史的推荐:")
    liked_ids = ["v001", "v002"]
    results = recommender.recommend_by_history(liked_ids, exclude_ids=liked_ids, limit=6)
    print(f"   推荐视频数: {len(results)}")
    assert len(results) >= 5, "推荐数量不足5个"
    
    print("\n   推荐结果:")
    for i, (video, score) in enumerate(results, 1):
        print(f"   {i}. {video.title} (相关度: {score:.4f})")
    print("   ✓ 通过")
    
    print("\n3. 测试相似视频推荐:")
    similar = recommender.get_similar_videos("v001", limit=5)
    print(f"   相似视频数: {len(similar)}")
    assert len(similar) >= 1, "相似视频推荐失败"
    
    print("\n   与v001相似的视频:")
    for i, (video, score) in enumerate(similar, 1):
        print(f"   {i}. {video.title} (相似度: {score:.4f})")
    print("   ✓ 通过")
    
    print("\n✓ 推荐引擎模块测试通过!")


def test_recommender_app():
    print("\n" + "="*60)
    print("测试推荐应用模块")
    print("="*60)
    
    app = VideoRecommenderApp()
    user_id = "test_user_001"
    
    print("\n1. 测试创建会话:")
    session = app.create_session(user_id)
    print(f"   用户ID: {session.user_id}")
    print(f"   当前轮次: {session.current_round}")
    assert session.user_id == user_id, "用户ID不正确"
    print("   ✓ 通过")
    
    print("\n2. 测试第一轮推荐:")
    result = app.start_first_round(user_id, "我喜欢看人工智能和编程相关的视频")
    print(f"   轮次: {result['round']}")
    print(f"   推荐视频数: {len(result['recommendations'])}")
    assert result["success"], "第一轮推荐失败"
    assert len(result["recommendations"]) >= 5, "推荐数量不足5个"
    
    print("\n   推荐视频:")
    for video in result["recommendations"]:
        print(f"   [{video['index']}] {video['title']}")
    print("   ✓ 通过")
    
    print("\n3. 测试选择视频:")
    selected_indices = [1, 3]
    select_result = app.process_selection(user_id, selected_indices)
    print(f"   选择成功: {select_result['success']}")
    print(f"   已选视频数: {len(select_result['selected_videos'])}")
    assert select_result["success"], "选择失败"
    assert len(select_result["selected_videos"]) == 2, "选择数量不正确"
    print("   ✓ 通过")
    
    print("\n4. 测试生成下一轮推荐:")
    next_result = app.generate_next_round(user_id)
    print(f"   轮次: {next_result['round']}")
    print(f"   推荐视频数: {len(next_result['recommendations'])}")
    assert next_result["success"], "下一轮推荐失败"
    assert len(next_result["recommendations"]) >= 5, "推荐数量不足5个"
    assert next_result["round"] == 2, "轮次不正确"
    
    print("\n   第二轮推荐视频:")
    for video in next_result["recommendations"]:
        print(f"   [{video['index']}] {video['title']}")
    
    print("\n   用户画像:")
    profile = next_result["user_profile"]
    print(f"   已喜欢视频数: {profile['total_liked']}")
    print(f"   最喜欢的分类: {profile['favorite_category']}")
    print("   ✓ 通过")
    
    print("\n5. 测试获取用户历史:")
    history = app.get_user_history(user_id)
    print(f"   当前轮次: {history['current_round']}")
    print(f"   已喜欢视频数: {len(history['liked_videos'])}")
    assert history["success"], "获取历史失败"
    print("   ✓ 通过")
    
    print("\n6. 测试重置会话:")
    reset_result = app.reset_session(user_id)
    print(f"   重置成功: {reset_result['success']}")
    assert reset_result["success"], "重置失败"
    print("   ✓ 通过")
    
    print("\n✓ 推荐应用模块测试通过!")


def test_edge_cases():
    print("\n" + "="*60)
    print("测试边界情况")
    print("="*60)
    
    app = VideoRecommenderApp()
    user_id = "edge_case_user"
    
    print("\n1. 测试空选择:")
    app.start_first_round(user_id, "科技视频")
    result = app.process_selection(user_id, [])
    print(f"   空选择结果: {result['success']} (预期: False)")
    assert not result["success"], "空选择应该失败"
    print("   ✓ 通过")
    
    print("\n2. 测试无效选择编号:")
    result = app.process_selection(user_id, [999, 1000])
    print(f"   无效编号结果: {result['success']} (预期: False)")
    assert not result["success"], "无效编号应该失败"
    print("   ✓ 通过")
    
    print("\n3. 测试不存在的用户:")
    result = app.get_user_history("non_existent_user")
    print(f"   不存在用户结果: {result['success']} (预期: False)")
    assert not result["success"], "不存在用户应该失败"
    print("   ✓ 通过")
    
    print("\n4. 测试每轮推荐数量:")
    app.reset_session(user_id)
    result = app.start_first_round(user_id, "编程教程")
    print(f"   第一轮推荐数量: {len(result['recommendations'])} (预期: >=5)")
    assert len(result["recommendations"]) >= 5, "每轮推荐应不少于5个"
    
    app.process_selection(user_id, [1])
    next_result = app.generate_next_round(user_id)
    print(f"   第二轮推荐数量: {len(next_result['recommendations'])} (预期: >=5)")
    assert len(next_result["recommendations"]) >= 5, "每轮推荐应不少于5个"
    print("   ✓ 通过")
    
    print("\n✓ 边界情况测试通过!")


def main():
    print("\n" + "#"*60)
    print("#" + " "*58 + "#")
    print("#      视频推荐系统单元测试")
    print("#" + " "*58 + "#")
    print("#"*60)
    
    try:
        test_video_database()
        test_text_processor()
        test_recommendation_engine()
        test_recommender_app()
        test_edge_cases()
        
        print("\n" + "#"*60)
        print("#" + " "*58 + "#")
        print("#      ✓ 所有测试通过!")
        print("#" + " "*58 + "#")
        print("#"*60)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
