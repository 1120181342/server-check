package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import com.xxuniversity.dto.LoginDTO;
import com.xxuniversity.dto.LoginVO;
import com.xxuniversity.dto.UserInfoVO;
import com.xxuniversity.service.AuthService;
import com.xxuniversity.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController extends BaseController {

    private final AuthService authService;
    private final UserService userService;

    @PostMapping("/login")
    public Result<LoginVO> login(@Validated @RequestBody LoginDTO loginDTO) {
        log.info("用户登录请求：{}", loginDTO.getUsername());
        LoginVO loginVO = authService.login(loginDTO);
        return success("登录成功", loginVO);
    }

    @PostMapping("/logout")
    public Result<Void> logout() {
        String userId = getCurrentUserId();
        if (userId != null) {
            authService.logout(userId);
        }
        return success("退出登录成功", null);
    }

    @GetMapping("/captcha")
    public Result<Map<String, String>> getCaptcha(@RequestParam String key) {
        String captcha = authService.generateCaptcha(key);
        return success(Map.of("captcha", captcha, "key", key));
    }

    @GetMapping("/info")
    public Result<UserInfoVO> getUserInfo() {
        String userId = getCurrentUserId();
        UserInfoVO userInfo = userService.getUserInfo(userId);
        return success(userInfo);
    }
}
