package com.xxuniversity.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xxuniversity.dto.UserInfoVO;
import com.xxuniversity.entity.User;
import com.xxuniversity.mapper.UserMapper;
import com.xxuniversity.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;

    @Override
    @Cacheable(value = "userInfo", key = "#userId")
    public UserInfoVO getUserInfo(String userId) {
        log.info("查询用户信息: userId={}", userId);

        LambdaQueryWrapper<User> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(User::getUserId, userId);
        User user = userMapper.selectOne(queryWrapper);

        if (user == null) {
            user = createMockUser(userId);
        }

        UserInfoVO userInfoVO = new UserInfoVO();
        BeanUtils.copyProperties(user, userInfoVO);
        return userInfoVO;
    }

    private User createMockUser(String userId) {
        User user = new User();
        user.setUserId(userId);
        user.setUsername(userId);
        user.setRealName("用户" + userId.substring(Math.max(0, userId.length() - 4)));
        user.setEmail(userId + "@xxuniversity.edu.cn");
        user.setPhone("138****" + userId.substring(Math.max(0, userId.length() - 4)));
        user.setDepartment("未知部门");
        user.setRole("user");
        user.setGender("未知");
        return user;
    }
}
