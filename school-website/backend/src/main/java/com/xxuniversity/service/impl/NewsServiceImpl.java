package com.xxuniversity.service.impl;

import com.xxuniversity.dto.NewsDTO;
import com.xxuniversity.dto.NewsDetailDTO;
import com.xxuniversity.dto.PageResult;
import com.xxuniversity.enums.NewsCategoryEnum;
import com.xxuniversity.service.NewsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

@Slf4j
@Service
@RequiredArgsConstructor
public class NewsServiceImpl implements NewsService {

    private static final List<NewsCategoryEnum> CATEGORIES = Arrays.asList(
            NewsCategoryEnum.RESEARCH,
            NewsCategoryEnum.ACADEMIC,
            NewsCategoryEnum.ADMISSION,
            NewsCategoryEnum.AWARD
    );

    private static final List<String> TITLES = Arrays.asList(
            "我校计算机学院团队在人工智能领域取得重大突破",
            "国际知名学术大师来校讲学并与博士生交流",
            "关于2025年博士生招生工作的重要通知",
            "我校博士生在国际顶级会议发表论文并获最佳论文奖"
    );

    @Override
    @Cacheable(value = "newsList", key = "#category + ':' + #page + ':' + #size")
    public PageResult<NewsDTO> getNewsList(String category, Integer page, Integer size) {
        log.info("查询新闻列表: category={}, page={}, size={}", category, page, size);

        List<NewsDTO> newsList = IntStream.range(0, size)
                .mapToObj(i -> createNewsDTO(i, page, size))
                .filter(news -> "all".equals(category) || news.getCategory().equals(category))
                .collect(Collectors.toList());

        long total = "all".equals(category) ? 50L : 15L;

        return PageResult.of(newsList, total, page, size);
    }

    @Override
    @Cacheable(value = "newsDetail", key = "#id")
    public NewsDetailDTO getNewsDetail(Long id) {
        log.info("查询新闻详情: id={}", id);

        return NewsDetailDTO.builder()
                .id(id)
                .title("关于2025年博士生招生工作的重要通知")
                .summary("根据教育部有关文件精神，结合我校实际情况，现将2025年博士研究生招生工作安排如下...")
                .content(buildNewsContent())
                .category(NewsCategoryEnum.ADMISSION.getCode())
                .categoryName(NewsCategoryEnum.ADMISSION.getName())
                .date("2024-07-20")
                .views(6789)
                .source("研究生院")
                .author("招生办公室")
                .createTime(LocalDateTime.now().minusDays(5))
                .updateTime(LocalDateTime.now().minusDays(3))
                .build();
    }

    @Override
    @Cacheable(value = "featuredNews", key = "'featured'")
    public List<NewsDTO> getFeaturedNews() {
        log.info("查询头条新闻");

        return Arrays.asList(
                createFeaturedNews(1L, "我校计算机学院团队在人工智能领域取得重大突破",
                        NewsCategoryEnum.RESEARCH, "2024-07-25", 8560, true),
                createFeaturedNews(2L, "关于2025年博士生招生工作的重要通知",
                        NewsCategoryEnum.ADMISSION, "2024-07-20", 6789, false),
                createFeaturedNews(3L, "我校博士生在国际顶级会议发表论文并获最佳论文奖",
                        NewsCategoryEnum.AWARD, "2024-07-18", 5432, false)
        );
    }

    private NewsDTO createNewsDTO(int index, int page, int size) {
        int categoryIndex = index % CATEGORIES.size();
        NewsCategoryEnum category = CATEGORIES.get(categoryIndex);
        long id = (long) ((page - 1) * size + index + 1);

        return NewsDTO.builder()
                .id(id)
                .title(TITLES.get(categoryIndex) + " - 第" + id + "条")
                .summary("这是新闻内容的摘要描述，展示新闻的主要内容和亮点信息，帮助用户快速了解新闻的核心要点...")
                .category(category.getCode())
                .categoryName(category.getName())
                .date(LocalDate.now().minusDays(index).toString())
                .views((int) (Math.random() * 10000))
                .source("计算机学院")
                .isFeatured(false)
                .build();
    }

    private NewsDTO createFeaturedNews(Long id, String title, NewsCategoryEnum category,
                                        String date, Integer views, Boolean isFeatured) {
        return NewsDTO.builder()
                .id(id)
                .title(title)
                .category(category.getCode())
                .categoryName(category.getName())
                .date(date)
                .views(views)
                .isFeatured(isFeatured)
                .build();
    }

    private String buildNewsContent() {
        return "<p>根据教育部有关文件精神，结合我校实际情况，现将2025年博士研究生招生工作安排如下：</p>" +
                "<h3>一、招生计划</h3>" +
                "<p>2025年我校计划招收博士研究生约500人，具体招生人数以教育部正式下达的招生计划为准。</p>" +
                "<h3>二、招生方式</h3>" +
                "<p>1. 申请-考核制：面向全日制硕士毕业生</p>" +
                "<p>2. 硕博连读：面向在读优秀硕士生</p>" +
                "<p>3. 直博生：面向应届优秀本科生</p>" +
                "<h3>三、报名时间</h3>" +
                "<p>申请-考核制：2024年9月1日-9月30日</p>" +
                "<p>硕博连读：2024年10月1日-10月15日</p>";
    }
}
