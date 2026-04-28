package com.xxuniversity.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.io.Serializable;

@Data
@ApiModel(value = "LoginDTO", description = "用户登录请求参数")
public class LoginDTO implements Serializable {

    private static final long serialVersionUID = 1L;

    @NotBlank(message = "用户名不能为空")
    @ApiModelProperty(value = "用户名/学号/工号", required = true, example = "2021001", position = 1)
    private String username;

    @NotBlank(message = "密码不能为空")
    @ApiModelProperty(value = "密码", required = true, example = "123456", position = 2)
    private String password;

    @NotBlank(message = "验证码不能为空")
    @ApiModelProperty(value = "验证码", required = true, example = "1234", position = 3)
    private String captcha;

    @NotNull(message = "用户类型不能为空")
    @ApiModelProperty(value = "用户类型：student-学生, teacher-教师, admin-管理员", required = true, 
              allowableValues = "student,teacher,admin", example = "student", position = 4)
    private String userType;

    @ApiModelProperty(value = "是否记住密码", example = "false", position = 5)
    private Boolean rememberMe;
}
