package com.xxuniversity.service;

import com.xxuniversity.dto.NewsDTO;
import com.xxuniversity.dto.NewsDetailDTO;
import com.xxuniversity.dto.PageResult;

import java.util.List;

public interface NewsService {

    PageResult<NewsDTO> getNewsList(String category, Integer page, Integer size);

    NewsDetailDTO getNewsDetail(Long id);

    List<NewsDTO> getFeaturedNews();
}
