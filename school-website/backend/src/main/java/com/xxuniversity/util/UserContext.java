package com.xxuniversity.util;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

public class UserContext {

    private static final ThreadLocal<UserInfo> USER_THREAD_LOCAL = new ThreadLocal<>();

    public static void setUserInfo(String userId, String username, String role, String token) {
        USER_THREAD_LOCAL.set(UserInfo.builder()
                .userId(userId)
                .username(username)
                .role(role)
                .token(token)
                .build());
    }

    public static UserInfo getUserInfo() {
        return USER_THREAD_LOCAL.get();
    }

    public static String getUserId() {
        UserInfo userInfo = USER_THREAD_LOCAL.get();
        return userInfo != null ? userInfo.getUserId() : null;
    }

    public static String getUsername() {
        UserInfo userInfo = USER_THREAD_LOCAL.get();
        return userInfo != null ? userInfo.getUsername() : null;
    }

    public static String getRole() {
        UserInfo userInfo = USER_THREAD_LOCAL.get();
        return userInfo != null ? userInfo.getRole() : null;
    }

    public static String getToken() {
        UserInfo userInfo = USER_THREAD_LOCAL.get();
        return userInfo != null ? userInfo.getToken() : null;
    }

    public static void clear() {
        USER_THREAD_LOCAL.remove();
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserInfo {
        private String userId;
        private String username;
        private String role;
        private String token;
    }
}
