package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/news")
@RequiredArgsConstructor
public class NewsController {

    @GetMapping("/list")
    @Cacheable(value = "newsList", key = "#category + ':' + #page + ':' + #size")
    public Result<Map<String, Object>> getNewsList(
            @RequestParam(required = false, defaultValue = "all") String category,
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @RequestParam(required = false, defaultValue = "10") Integer size) {

        List<Map<String, Object>> newsList = new ArrayList<>();

        String[] categories = {"research", "academic", "admission", "award"};
        String[] categoryNames = {"科研成果", "学术动态", "招生资讯", "获奖荣誉"};
        String[] titles = {
                "我校计算机学院团队在人工智能领域取得重大突破",
                "国际知名学术大师来校讲学并与博士生交流",
                "关于2025年博士生招生工作的重要通知",
                "我校博士生在国际顶级会议发表论文并获最佳论文奖"
        };

        for (int i = 0; i < size; i++) {
            Map<String, Object> news = new HashMap<>();
            int idx = i % 4;
            news.put("id", (long) ((page - 1) * size + i + 1));
            news.put("title", titles[idx] + " - 第" + ((page - 1) * size + i + 1) + "条");
            news.put("category", categories[idx]);
            news.put("categoryName", categoryNames[idx]);
            news.put("date", LocalDateTime.now().minusDays(i).toLocalDate().toString());
            news.put("views", (int) (Math.random() * 10000));
            news.put("source", "计算机学院");
            news.put("summary", "这是新闻内容的摘要描述，展示新闻的主要内容和亮点信息，帮助用户快速了解新闻的核心要点...");
            newsList.add(news);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("list", newsList);
        result.put("total", 50);
        result.put("page", page);
        result.put("size", size);

        return Result.success(result);
    }

    @GetMapping("/detail/{id}")
    @Cacheable(value = "newsDetail", key = "#id")
    public Result<Map<String, Object>> getNewsDetail(@PathVariable Long id) {
        Map<String, Object> news = new HashMap<>();
        news.put("id", id);
        news.put("title", "关于2025年博士生招生工作的重要通知");
        news.put("category", "admission");
        news.put("categoryName", "招生资讯");
        news.put("date", "2024-07-20");
        news.put("views", 6789);
        news.put("source", "研究生院");
        news.put("author", "招生办公室");
        news.put("content", "<p>根据教育部有关文件精神，结合我校实际情况，现将2025年博士研究生招生工作安排如下：</p>" +
                "<h3>一、招生计划</h3><p>2025年我校计划招收博士研究生约500人，具体招生人数以教育部正式下达的招生计划为准。</p>" +
                "<h3>二、招生方式</h3><p>1. 申请-考核制：面向全日制硕士毕业生</p><p>2. 硕博连读：面向在读优秀硕士生</p><p>3. 直博生：面向应届优秀本科生</p>");
        news.put("createTime", LocalDateTime.now().minusDays(5));
        news.put("updateTime", LocalDateTime.now().minusDays(3));

        return Result.success(news);
    }

    @GetMapping("/featured")
    @Cacheable(value = "featuredNews", key = "'featured'")
    public Result<List<Map<String, Object>>> getFeaturedNews() {
        List<Map<String, Object>> newsList = new ArrayList<>();

        Map<String, Object> news1 = new HashMap<>();
        news1.put("id", 1L);
        news1.put("title", "我校计算机学院团队在人工智能领域取得重大突破");
        news1.put("category", "research");
        news1.put("categoryName", "科研成果");
        news1.put("date", "2024-07-25");
        news1.put("views", 8560);
        news1.put("isFeatured", true);
        newsList.add(news1);

        Map<String, Object> news2 = new HashMap<>();
        news2.put("id", 2L);
        news2.put("title", "关于2025年博士生招生工作的重要通知");
        news2.put("category", "admission");
        news2.put("categoryName", "招生资讯");
        news2.put("date", "2024-07-20");
        news2.put("views", 6789);
        news2.put("isFeatured", false);
        newsList.add(news2);

        Map<String, Object> news3 = new HashMap<>();
        news3.put("id", 3L);
        news3.put("title", "我校博士生在国际顶级会议发表论文并获最佳论文奖");
        news3.put("category", "award");
        news3.put("categoryName", "获奖荣誉");
        news3.put("date", "2024-07-18");
        news3.put("views", 5432);
        news3.put("isFeatured", false);
        newsList.add(news3);

        return Result.success(newsList);
    }
}
