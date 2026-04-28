package com.xxuniversity.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@ApiModel(value = "CollegeDTO", description = "学院信息对象")
public class CollegeDTO implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "学院ID", example = "1", position = 1)
    private Long id;

    @ApiModelProperty(value = "学院名称", example = "计算机学院", position = 2)
    private String name;

    @ApiModelProperty(value = "学院简介", example = "培养计算机科学与技术领域的高层次人才...", position = 3)
    private String description;

    @ApiModelProperty(value = "学院图片URL", position = 4)
    private String imageUrl;

    @ApiModelProperty(value = "导师数量", example = "45", position = 5)
    private Integer supervisorCount;

    @ApiModelProperty(value = "专业数量", example = "6", position = 6)
    private Integer majorCount;

    @ApiModelProperty(value = "学生数量", example = "3500", position = 7)
    private Integer studentCount;

    @ApiModelProperty(value = "标签列表", example = "[\"双一流建设\", \"国家级重点学科\"]", position = 8)
    private String[] tags;

    @ApiModelProperty(value = "培养层次：undergraduate-本科, graduate-研究生, doctoral-博士生, all-全部", 
              example = "all", position = 9)
    private String educationLevel;
}
