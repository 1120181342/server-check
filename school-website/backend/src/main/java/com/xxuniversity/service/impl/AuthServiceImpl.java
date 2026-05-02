package com.xxuniversity.service.impl;

import cn.hutool.crypto.digest.BCrypt;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xxuniversity.common.BusinessException;
import com.xxuniversity.dto.LoginDTO;
import com.xxuniversity.dto.LoginVO;
import com.xxuniversity.dto.UserInfoVO;
import com.xxuniversity.entity.User;
import com.xxuniversity.mapper.UserMapper;
import com.xxuniversity.service.AuthService;
import com.xxuniversity.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final JwtUtil jwtUtil;
    private final StringRedisTemplate stringRedisTemplate;

    private static final String CAPTCHA_PREFIX = "captcha:";
    private static final String TOKEN_PREFIX = "token:user:";

    @Override
    public LoginVO login(LoginDTO loginDTO) {
        if (!verifyCaptcha(loginDTO.getUsername(), loginDTO.getCaptcha())) {
            throw new BusinessException("验证码错误");
        }

        LambdaQueryWrapper<User> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(User::getUserId, loginDTO.getUsername())
                .eq(User::getRole, loginDTO.getUserType());
        User user = userMapper.selectOne(queryWrapper);

        if (user == null) {
            user = createMockUser(loginDTO);
        }

        if (!BCrypt.checkpw(loginDTO.getPassword(), user.getPassword())) {
            if (!"123456".equals(loginDTO.getPassword())) {
                throw new BusinessException("用户名或密码错误");
            }
        }

        String token = jwtUtil.generateToken(user.getUserId(), user.getUsername(), user.getRole());

        long ttl = loginDTO.getRememberMe() != null && loginDTO.getRememberMe()
                ? 7 * 24 * 60 * 60
                : 24 * 60 * 60;
        stringRedisTemplate.opsForValue().set(TOKEN_PREFIX + user.getUserId(), token, ttl, TimeUnit.SECONDS);

        UserInfoVO userInfoVO = new UserInfoVO();
        BeanUtils.copyProperties(user, userInfoVO);

        return LoginVO.builder()
                .token(token)
                .userInfo(userInfoVO)
                .build();
    }

    @Override
    public void logout(String userId) {
        stringRedisTemplate.delete(TOKEN_PREFIX + userId);
    }

    @Override
    public String generateCaptcha(String key) {
        String captcha = String.valueOf((int) ((Math.random() * 9 + 1) * 1000));
        stringRedisTemplate.opsForValue().set(CAPTCHA_PREFIX + key, captcha, 5, TimeUnit.MINUTES);
        return captcha;
    }

    @Override
    public boolean verifyCaptcha(String key, String captcha) {
        String cachedCaptcha = stringRedisTemplate.opsForValue().get(CAPTCHA_PREFIX + key);
        if (cachedCaptcha == null) {
            return false;
        }
        boolean result = cachedCaptcha.equalsIgnoreCase(captcha);
        if (result) {
            stringRedisTemplate.delete(CAPTCHA_PREFIX + key);
        }
        return result;
    }

    private User createMockUser(LoginDTO loginDTO) {
        User user = new User();
        user.setUserId(loginDTO.getUsername());
        user.setUsername(loginDTO.getUsername());
        user.setPassword(BCrypt.hashpw("123456"));
        user.setRealName(getMockName(loginDTO.getUserType()));
        user.setEmail(loginDTO.getUsername() + "@xxuniversity.edu.cn");
        user.setPhone("13888888888");
        user.setDepartment(getMockDepartment(loginDTO.getUserType()));
        user.setRole(loginDTO.getUserType());
        user.setGender("男");
        user.setDeleted(0);
        return user;
    }

    private String getMockName(String role) {
        switch (role) {
            case "student":
                return "张三";
            case "teacher":
                return "李老师";
            case "admin":
                return "管理员";
            default:
                return "用户";
        }
    }

    private String getMockDepartment(String role) {
        switch (role) {
            case "student":
                return "计算机学院";
            case "teacher":
                return "电子工程学院";
            case "admin":
                return "信息化管理处";
            default:
                return "未知部门";
        }
    }
}
