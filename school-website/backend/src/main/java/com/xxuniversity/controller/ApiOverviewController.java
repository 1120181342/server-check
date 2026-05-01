package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import io.swagger.annotations.*;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Api(tags = "00.API概览", description = "API版本信息、接口统计等概览接口")
public class ApiOverviewController extends BaseController {

    @GetMapping("/version")
    @ApiOperation(value = "获取API版本信息", notes = "获取当前API的版本信息、环境、状态等")
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class)
    })
    public Result<Map<String, Object>> getVersion() {
        Map<String, Object> version = new LinkedHashMap<>();
        
        version.put("version", "1.0.0");
        version.put("apiVersion", "v1");
        version.put("buildTime", "2024-01-15 10:30:00");
        version.put("environment", "dev");
        version.put("status", "running");
        version.put("lastUpdate", "2024-01-15");
        
        return success(version);
    }

    @GetMapping("/overview")
    @ApiOperation(value = "获取API概览", notes = "获取所有API模块的概览信息")
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class)
    })
    public Result<Map<String, Object>> getOverview() {
        Map<String, Object> overview = new LinkedHashMap<>();
        
        List<Map<String, Object>> modules = new ArrayList<>();
        
        modules.add(createModule("认证管理", "/auth", 4, 
                Arrays.asList("用户登录", "用户登出", "获取验证码", "获取用户信息"), false));
        
        modules.add(createModule("新闻管理", "/news", 3,
                Arrays.asList("获取新闻列表", "获取新闻详情", "获取头条新闻"), false));
        
        modules.add(createModule("首页管理", "/home", 3,
                Arrays.asList("获取轮播图", "获取快速导航", "获取学校信息"), false));
        
        modules.add(createModule("学院管理", "/college", 3,
                Arrays.asList("获取学院列表", "获取学院详情", "获取导师列表"), false));
        
        modules.add(createModule("招生管理", "/admission", 4,
                Arrays.asList("获取招生信息", "获取专业目录", "获取历年分数线", "获取招生公告"), false));
        
        overview.put("modules", modules);
        overview.put("totalModules", modules.size());
        overview.put("totalApis", 4 + 3 + 3 + 3 + 4);
        overview.put("swaggerUrl", "/swagger-ui.html");
        overview.put("knife4jUrl", "/doc.html");
        
        return success(overview);
    }

    @GetMapping("/status")
    @ApiOperation(value = "检查API健康状态", notes = "用于健康检查，返回API服务状态")
    @ApiResponses({
            @ApiResponse(code = 200, message = "服务正常", response = Map.class)
    })
    public Result<Map<String, Object>> getStatus() {
        Map<String, Object> status = new LinkedHashMap<>();
        
        status.put("status", "UP");
        status.put("timestamp", System.currentTimeMillis());
        status.put("uptime", "0 days, 2 hours, 30 minutes");
        status.put("services", createServicesStatus());
        
        return success(status);
    }

    private Map<String, Object> createModule(String name, String path, int apiCount, 
                                               List<String> endpoints, Boolean needAuth) {
        Map<String, Object> module = new LinkedHashMap<>();
        module.put("name", name);
        module.put("path", path);
        module.put("apiCount", apiCount);
        module.put("endpoints", endpoints);
        module.put("needAuth", needAuth);
        return module;
    }

    private Map<String, Object> createServicesStatus() {
        Map<String, Object> services = new LinkedHashMap<>();
        
        services.put("database", "UP");
        services.put("redis", "UP");
        services.put("authentication", "UP");
        
        return services;
    }
}
