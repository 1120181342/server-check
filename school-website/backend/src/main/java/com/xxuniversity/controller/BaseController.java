package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import com.xxuniversity.util.UserContext;
import org.springframework.web.bind.annotation.ModelAttribute;

public class BaseController {

    @ModelAttribute
    public void preHandle() {
    }

    protected String getCurrentUserId() {
        return UserContext.getUserId();
    }

    protected String getCurrentUsername() {
        return UserContext.getUsername();
    }

    protected String getCurrentUserRole() {
        return UserContext.getRole();
    }

    protected String getCurrentToken() {
        return UserContext.getToken();
    }

    protected UserContext.UserInfo getCurrentUser() {
        return UserContext.getUserInfo();
    }

    protected <T> Result<T> success() {
        return Result.success();
    }

    protected <T> Result<T> success(T data) {
        return Result.success(data);
    }

    protected <T> Result<T> success(String message, T data) {
        return Result.success(message, data);
    }

    protected <T> Result<T> error() {
        return Result.error();
    }

    protected <T> Result<T> error(String message) {
        return Result.error(message);
    }

    protected <T> Result<T> error(Integer code, String message) {
        return Result.error(code, message);
    }
}
