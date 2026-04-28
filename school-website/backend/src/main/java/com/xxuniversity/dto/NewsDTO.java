package com.xxuniversity.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NewsDTO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private String title;
    private String summary;
    private String category;
    private String categoryName;
    private String date;
    private Integer views;
    private String source;
    private String author;
    private String imageUrl;
    private Boolean isFeatured;
}
