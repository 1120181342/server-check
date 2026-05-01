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
@ApiModel(value = "LoginVO", description = "用户登录响应数据")
public class LoginVO implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "JWT Token，请求时需加前缀 'Bearer '", 
              example = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", position = 1)
    private String token;

    @ApiModelProperty(value = "用户信息", position = 2)
    private UserInfoVO userInfo;
}
