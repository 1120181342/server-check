package com.xxuniversity.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xxuniversity.common.Result;
import com.xxuniversity.dto.LoginDTO;
import com.xxuniversity.dto.LoginVO;
import com.xxuniversity.dto.UserInfoVO;
import com.xxuniversity.entity.User;
import com.xxuniversity.mapper.UserMapper;
import com.xxuniversity.service.AuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;
    private final UserMapper userMapper;

    @PostMapping("/login")
    public Result<LoginVO> login(@Validated @RequestBody LoginDTO loginDTO) {
        log.info("用户登录请求：{}", loginDTO.getUsername());
        LoginVO loginVO = authService.login(loginDTO);
        return Result.success("登录成功", loginVO);
    }

    @PostMapping("/logout")
    public Result<Void> logout(HttpServletRequest request) {
        String userId = (String) request.getAttribute("userId");
        if (userId != null) {
            authService.logout(userId);
        }
        return Result.success("退出登录成功", null);
    }

    @GetMapping("/captcha")
    public Result<Map<String, String>> getCaptcha(@RequestParam String key) {
        String captcha = authService.generateCaptcha(key);
        Map<String, String> result = new HashMap<>();
        result.put("captcha", captcha);
        result.put("key", key);
        return Result.success(result);
    }

    @GetMapping("/info")
    @Cacheable(value = "userInfo", key = "#userId")
    public Result<UserInfoVO> getUserInfo(HttpServletRequest request) {
        String userId = (String) request.getAttribute("userId");
        String username = (String) request.getAttribute("username");
        String role = (String) request.getAttribute("role");

        LambdaQueryWrapper<User> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(User::getUserId, userId);
        User user = userMapper.selectOne(queryWrapper);

        if (user == null) {
            user = new User();
            user.setUserId(userId);
            user.setUsername(username);
            user.setRealName(role.equals("student") ? "张三" : role.equals("teacher") ? "李老师" : "管理员");
            user.setRole(role);
            user.setDepartment(role.equals("student") ? "计算机学院" : role.equals("teacher") ? "电子工程学院" : "信息化管理处");
            user.setEmail(userId + "@xxuniversity.edu.cn");
            user.setPhone("13888888888");
        }

        UserInfoVO userInfoVO = new UserInfoVO();
        BeanUtils.copyProperties(user, userInfoVO);
        return Result.success(userInfoVO);
    }
}
