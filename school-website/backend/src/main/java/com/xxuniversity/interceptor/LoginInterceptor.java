package com.xxuniversity.interceptor;

import com.alibaba.fastjson2.JSON;
import com.xxuniversity.common.Result;
import com.xxuniversity.util.JwtUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

@Slf4j
@Component
public class LoginInterceptor implements HandlerInterceptor {

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String token = request.getHeader(jwtUtil.getHeader());

        if (token == null || token.isEmpty()) {
            return unauthorized(response);
        }

        if (token.startsWith(jwtUtil.getPrefix() + " ")) {
            token = token.substring(jwtUtil.getPrefix().length() + 1);
        }

        try {
            if (!jwtUtil.validateToken(token)) {
                return unauthorized(response);
            }

            String userId = jwtUtil.getUserIdFromToken(token);
            String cachedToken = stringRedisTemplate.opsForValue().get("token:user:" + userId);
            
            if (cachedToken == null || !cachedToken.equals(token)) {
                return unauthorized(response);
            }

            request.setAttribute("userId", userId);
            request.setAttribute("username", jwtUtil.getUsernameFromToken(token));
            request.setAttribute("role", jwtUtil.getRoleFromToken(token));
            request.setAttribute("token", token);

            return true;
        } catch (Exception e) {
            log.error("Token验证失败：", e);
            return unauthorized(response);
        }
    }

    private boolean unauthorized(HttpServletResponse response) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(JSON.toJSONString(Result.unauthorized()));
        return false;
    }
}
