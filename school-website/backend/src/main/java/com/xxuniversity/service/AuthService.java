package com.xxuniversity.service;

import com.xxuniversity.dto.LoginDTO;
import com.xxuniversity.dto.LoginVO;

public interface AuthService {

    LoginVO login(LoginDTO loginDTO);

    void logout(String userId);

    String generateCaptcha(String key);

    boolean verifyCaptcha(String key, String captcha);
}
