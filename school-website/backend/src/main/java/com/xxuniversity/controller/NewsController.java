package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import com.xxuniversity.dto.NewsDTO;
import com.xxuniversity.dto.NewsDetailDTO;
import com.xxuniversity.dto.PageResult;
import com.xxuniversity.service.NewsService;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/news")
@RequiredArgsConstructor
public class NewsController extends BaseController {

    private final NewsService newsService;

    @GetMapping("/list")
    @Cacheable(value = "newsList", key = "#category + ':' + #page + ':' + #size")
    public Result<PageResult<NewsDTO>> getNewsList(
            @RequestParam(required = false, defaultValue = "all") String category,
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @RequestParam(required = false, defaultValue = "10") Integer size) {
        return success(newsService.getNewsList(category, page, size));
    }

    @GetMapping("/detail/{id}")
    @Cacheable(value = "newsDetail", key = "#id")
    public Result<NewsDetailDTO> getNewsDetail(@PathVariable Long id) {
        return success(newsService.getNewsDetail(id));
    }

    @GetMapping("/featured")
    @Cacheable(value = "featuredNews", key = "'featured'")
    public Result<List<NewsDTO>> getFeaturedNews() {
        return success(newsService.getFeaturedNews());
    }
}
