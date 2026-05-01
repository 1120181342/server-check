package com.xxuniversity.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@ApiModel(value = "NewsDetailDTO", description = "新闻详情对象")
public class NewsDetailDTO implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "新闻ID", example = "1", position = 1)
    private Long id;

    @ApiModelProperty(value = "新闻标题", example = "我校获批国家级实验室", position = 2)
    private String title;

    @ApiModelProperty(value = "新闻摘要", example = "我校计算机学院成功获批国家级重点实验室...", position = 3)
    private String summary;

    @ApiModelProperty(value = "新闻内容（HTML格式）", position = 4)
    private String content;

    @ApiModelProperty(value = "新闻分类编码：research-科研成果, academic-学术动态, admission-招生资讯, award-获奖荣誉", 
              example = "research", position = 5)
    private String category;

    @ApiModelProperty(value = "新闻分类名称", example = "科研成果", position = 6)
    private String categoryName;

    @ApiModelProperty(value = "发布日期", example = "2024-01-15", position = 7)
    private String date;

    @ApiModelProperty(value = "浏览次数", example = "1256", position = 8)
    private Integer views;

    @ApiModelProperty(value = "来源", example = "计算机学院", position = 9)
    private String source;

    @ApiModelProperty(value = "作者", example = "王老师", position = 10)
    private String author;

    @ApiModelProperty(value = "封面图片URL", position = 11)
    private String imageUrl;

    @ApiModelProperty(value = "创建时间", example = "2024-01-15T10:30:00", position = 12)
    private LocalDateTime createTime;

    @ApiModelProperty(value = "更新时间", example = "2024-01-15T14:20:00", position = 13)
    private LocalDateTime updateTime;
}
