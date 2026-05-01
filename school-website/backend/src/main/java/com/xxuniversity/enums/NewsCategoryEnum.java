package com.xxuniversity.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum NewsCategoryEnum {

    RESEARCH("research", "科研成果"),
    ACADEMIC("academic", "学术动态"),
    ADMISSION("admission", "招生资讯"),
    AWARD("award", "获奖荣誉");

    private final String code;
    private final String name;

    public static String getNameByCode(String code) {
        for (NewsCategoryEnum category : values()) {
            if (category.getCode().equals(code)) {
                return category.getName();
            }
        }
        return "未知分类";
    }

    public static boolean isValid(String code) {
        for (NewsCategoryEnum category : values()) {
            if (category.getCode().equals(code)) {
                return true;
            }
        }
        return false;
    }
}
