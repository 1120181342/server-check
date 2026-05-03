package com.xxuniversity.interceptor;

import com.alibaba.fastjson2.JSON;
import com.xxuniversity.common.Result;
import com.xxuniversity.util.JwtUtil;
import com.xxuniversity.util.UserContext;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@Slf4j
@Component
@RequiredArgsConstructor
public class LoginInterceptor implements HandlerInterceptor {

    private final JwtUtil jwtUtil;
    private final StringRedisTemplate stringRedisTemplate;

    private static final String TOKEN_PREFIX = "token:user:";

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
            String cachedToken = stringRedisTemplate.opsForValue().get(TOKEN_PREFIX + userId);

            if (cachedToken == null || !cachedToken.equals(token)) {
                return unauthorized(response);
            }

            String username = jwtUtil.getUsernameFromToken(token);
            String role = jwtUtil.getRoleFromToken(token);

            UserContext.setUserInfo(userId, username, role, token);

            return true;
        } catch (Exception e) {
            log.error("Token验证失败：", e);
            return unauthorized(response);
        }
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        UserContext.clear();
    }

    private boolean unauthorized(HttpServletResponse response) throws Exception {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(JSON.toJSONString(Result.unauthorized()));
        return false;
    }
}
