package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import com.xxuniversity.dto.LoginDTO;
import com.xxuniversity.dto.LoginVO;
import com.xxuniversity.dto.UserInfoVO;
import com.xxuniversity.service.AuthService;
import com.xxuniversity.service.UserService;
import io.swagger.annotations.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import springfox.documentation.annotations.ApiIgnore;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
@Api(tags = "01.认证管理", description = "用户登录、登出、获取用户信息等认证相关接口")
public class AuthController extends BaseController {

    private final AuthService authService;
    private final UserService userService;

    @PostMapping("/login")
    @ApiOperation(value = "用户登录", notes = "用户登录接口，支持学生、教师、管理员三种用户类型")
    @ApiResponses({
            @ApiResponse(code = 200, message = "登录成功", response = LoginVO.class),
            @ApiResponse(code = 400, message = "参数错误"),
            @ApiResponse(code = 401, message = "用户名或密码错误"),
            @ApiResponse(code = 500, message = "服务器内部错误")
    })
    public Result<LoginVO> login(
            @ApiParam(value = "登录参数", required = true)
            @Validated @RequestBody LoginDTO loginDTO) {
        log.info("用户登录请求：{}", loginDTO.getUsername());
        LoginVO loginVO = authService.login(loginDTO);
        return success("登录成功", loginVO);
    }

    @PostMapping("/logout")
    @ApiOperation(value = "用户登出", notes = "退出登录，清除Token")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "Authorization", value = "JWT Token", 
                              paramType = "header", dataType = "String", example = "Bearer xxx")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "退出成功"),
            @ApiResponse(code = 401, message = "未授权")
    })
    public Result<Void> logout() {
        String userId = getCurrentUserId();
        if (userId != null) {
            authService.logout(userId);
        }
        return success("退出登录成功", null);
    }

    @GetMapping("/captcha")
    @ApiOperation(value = "获取验证码", notes = "获取图形验证码，用于登录时验证")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "key", value = "验证码标识(一般用用户名或随机UUID)", 
                              required = true, paramType = "query", dataType = "String", example = "2021001")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class)
    })
    @ApiOperationSupport(
            order = 3,
            author = "XX大学信息化中心",
            ignoreParameters = {}
    )
    public Result<Map<String, String>> getCaptcha(
            @ApiParam(value = "验证码标识", required = true, example = "2021001")
            @RequestParam String key) {
        String captcha = authService.generateCaptcha(key);
        return success(Map.of("captcha", captcha, "key", key));
    }

    @GetMapping("/info")
    @ApiOperation(value = "获取当前用户信息", notes = "获取当前登录用户的详细信息，需要登录状态")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "Authorization", value = "JWT Token", 
                              paramType = "header", dataType = "String", example = "Bearer xxx")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = UserInfoVO.class),
            @ApiResponse(code = 401, message = "未授权，请先登录")
    })
    public Result<UserInfoVO> getUserInfo() {
        String userId = getCurrentUserId();
        UserInfoVO userInfo = userService.getUserInfo(userId);
        return success(userInfo);
    }
}
