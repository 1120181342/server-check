package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import com.xxuniversity.dto.NewsDTO;
import com.xxuniversity.dto.NewsDetailDTO;
import com.xxuniversity.dto.PageResult;
import com.xxuniversity.service.NewsService;
import io.swagger.annotations.*;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/news")
@RequiredArgsConstructor
@Api(tags = "02.新闻管理", description = "新闻列表、新闻详情、头条新闻等接口")
public class NewsController extends BaseController {

    private final NewsService newsService;

    @GetMapping("/list")
    @Cacheable(value = "newsList", key = "#category + ':' + #page + ':' + #size")
    @ApiOperation(value = "获取新闻列表", notes = "分页获取新闻列表，支持按分类筛选")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "category", value = "新闻分类：all-全部, research-科研成果, academic-学术动态, admission-招生资讯, award-获奖荣誉",
                              defaultValue = "all", allowableValues = "all,research,academic,admission,award",
                              paramType = "query", dataType = "String"),
            @ApiImplicitParam(name = "page", value = "页码，从1开始", defaultValue = "1", 
                              paramType = "query", dataType = "int", example = "1"),
            @ApiImplicitParam(name = "size", value = "每页大小", defaultValue = "10", 
                              paramType = "query", dataType = "int", example = "10")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = PageResult.class)
    })
    public Result<PageResult<NewsDTO>> getNewsList(
            @ApiParam(value = "新闻分类")
            @RequestParam(required = false, defaultValue = "all") String category,
            @ApiParam(value = "页码", example = "1")
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @ApiParam(value = "每页大小", example = "10")
            @RequestParam(required = false, defaultValue = "10") Integer size) {
        return success(newsService.getNewsList(category, page, size));
    }

    @GetMapping("/detail/{id}")
    @Cacheable(value = "newsDetail", key = "#id")
    @ApiOperation(value = "获取新闻详情", notes = "根据新闻ID获取新闻详情")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "id", value = "新闻ID", required = true, 
                              paramType = "path", dataType = "long", example = "1")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = NewsDetailDTO.class),
            @ApiResponse(code = 404, message = "新闻不存在")
    })
    public Result<NewsDetailDTO> getNewsDetail(
            @ApiParam(value = "新闻ID", required = true, example = "1")
            @PathVariable Long id) {
        return success(newsService.getNewsDetail(id));
    }

    @GetMapping("/featured")
    @Cacheable(value = "featuredNews", key = "'featured'")
    @ApiOperation(value = "获取头条新闻", notes = "获取推荐的头条新闻列表")
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = NewsDTO.class, responseContainer = "List")
    })
    public Result<List<NewsDTO>> getFeaturedNews() {
        return success(newsService.getFeaturedNews());
    }
}
