package com.xxuniversity.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@ApiModel(value = "UserInfoVO", description = "用户信息响应对象")
public class UserInfoVO implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "数据库主键ID", example = "1", position = 1)
    private Long id;

    @ApiModelProperty(value = "用户ID/学号/工号", example = "2021001", position = 2)
    private String userId;

    @ApiModelProperty(value = "用户名", example = "zhangsan", position = 3)
    private String username;

    @ApiModelProperty(value = "真实姓名", example = "张三", position = 4)
    private String realName;

    @ApiModelProperty(value = "邮箱", example = "zhangsan@xxuniversity.edu.cn", position = 5)
    private String email;

    @ApiModelProperty(value = "手机号", example = "13800138000", position = 6)
    private String phone;

    @ApiModelProperty(value = "头像URL", position = 7)
    private String avatar;

    @ApiModelProperty(value = "性别：male-男, female-女", example = "male", position = 8)
    private String gender;

    @ApiModelProperty(value = "所属部门/学院", example = "计算机学院", position = 9)
    private String department;

    @ApiModelProperty(value = "角色：student-学生, teacher-教师, admin-管理员", 
              example = "student", position = 10)
    private String role;

    @ApiModelProperty(value = "入学/入职日期", example = "2021-09-01T00:00:00", position = 11)
    private LocalDateTime enrollDate;
}
