package com.xxuniversity.dto;

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
public class PageResult<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    private List<T> list;
    private Long total;
    private Integer page;
    private Integer size;
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
