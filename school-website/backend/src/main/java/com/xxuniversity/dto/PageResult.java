package com.xxuniversity.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@ApiModel(value = "PageResult", description = "分页结果对象")
public class PageResult<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "数据列表", position = 1)
    private List<T> list;

    @ApiModelProperty(value = "总记录数", position = 2)
    private Long total;

    @ApiModelProperty(value = "当前页码", position = 3)
    private Integer page;

    @ApiModelProperty(value = "每页大小", position = 4)
    private Integer size;

    @ApiModelProperty(value = "总页数", position = 5)
    private Integer totalPages;

    public static <T> PageResult<T> of(List<T> list, Long total, Integer page, Integer size) {
        return PageResult.<T>builder()
                .list(list)
                .total(total)
                .page(page)
                .size(size)
                .totalPages((int) Math.ceil((double) total / size))
                .build();
    }

    public static <T> PageResult<T> empty(Integer page, Integer size) {
        return PageResult.<T>builder()
                .list(List.of())
                .total(0L)
                .page(page)
                .size(size)
                .totalPages(0)
                .build();
    }
}
