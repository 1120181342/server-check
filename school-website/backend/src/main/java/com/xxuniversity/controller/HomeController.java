package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import com.xxuniversity.dto.CollegeDTO;
import com.xxuniversity.dto.NewsDTO;
import io.swagger.annotations.*;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/home")
@RequiredArgsConstructor
@Api(tags = "03.首页管理", description = "首页轮播图、学校简介、快速导航等接口")
public class HomeController extends BaseController {

    @GetMapping("/banners")
    @Cacheable(value = "homeBanners", key = "'banners'")
    @ApiOperation(value = "获取首页轮播图", notes = "获取首页顶部轮播图列表")
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class, responseContainer = "List")
    })
    public Result<List<Map<String, Object>>> getBanners() {
        List<Map<String, Object>> banners = new ArrayList<>();
        
        banners.add(createBanner("XX大学", "厚德载物 自强不息", 
                "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=beautiful%20university%20campus%20entrance%20gate%20with%20modern%20architecture%20and%20green%20trees%20sunny%20day%20photorealistic&image_size=landscape_16_9"));
        
        banners.add(createBanner("欢迎2024级新同学", "开启你的学术之旅", 
                "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=students%20walking%20on%20beautiful%20university%20campus%20with%20modern%20library%20building%20and%20lawn%20spring%20season&image_size=landscape_16_9"));
        
        banners.add(createBanner("研究生招生进行中", "追求卓越 成就梦想", 
                "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20laboratory%20with%20modern%20equipment%20researchers%20working%20professional%20scientific%20environment&image_size=landscape_16_9"));
        
        return success(banners);
    }

    @GetMapping("/quick-nav")
    @Cacheable(value = "homeQuickNav", key = "'quickNav'")
    @ApiOperation(value = "获取首页快速导航", notes = "获取首页快速导航菜单")
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class, responseContainer = "List")
    })
    public Result<List<Map<String, Object>>> getQuickNav() {
        List<Map<String, Object>> navs = new ArrayList<>();
        
        navs.add(createQuickNav("研究生教育", "探索前沿研究，培养学术精英", "User", "/graduate/admission"));
        navs.add(createQuickNav("本科生教育", "夯实基础，培养创新型人才", "Avatar", "/undergraduate/admission"));
        navs.add(createQuickNav("博士生教育", "攀登学术高峰，引领科技创新", "Trophy", "/doctoral/admission"));
        
        return success(navs);
    }

    @GetMapping("/school-info")
    @Cacheable(value = "homeSchoolInfo", key = "'schoolInfo'")
    @ApiOperation(value = "获取学校基本信息", notes = "获取学校简介、数据统计等基本信息")
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class)
    })
    public Result<Map<String, Object>> getSchoolInfo() {
        Map<String, Object> info = new LinkedHashMap<>();
        
        info.put("intro", "XX大学是一所历史悠久、学科齐全的综合性研究型大学。学校坐落于风景秀丽的XX市，占地面积近5000亩，建筑面积超过200万平方米。学校秉承\"厚德载物、自强不息\"的校训精神，致力于培养具有创新精神和实践能力的高素质人才。");
        
        info.put("history", "学校创建于1920年，历经百年发展，已成为一所以工为主、理工结合、多学科协调发展的全国重点大学。学校现有教职工近4000人，其中两院院士15人，国家级教学名师20余人。全日制在校学生约5万人，其中研究生近2万人。");
        
        List<Map<String, Object>> stats = new ArrayList<>();
        stats.add(createStat("100+", "年", "办学历史"));
        stats.add(createStat("5", "万+", "在校学生"));
        stats.add(createStat("4000", "+", "教职工"));
        stats.add(createStat("15", "位", "两院院士"));
        info.put("stats", stats);
        
        List<Map<String, Object>> campusImages = new ArrayList<>();
        campusImages.add(createCampusImage("主教学楼", "现代化的教学设施，先进的多媒体教室", 
                "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20teaching%20building%20with%20glass%20facade%20students%20entering%20clean%20and%20bright&image_size=square_hd"));
        campusImages.add(createCampusImage("图书馆", "藏书丰富，安静舒适的学习环境", 
                "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20library%20interior%20with%20rows%20of%20books%20students%20studying%20natural%20light%20large%20windows&image_size=square_hd"));
        campusImages.add(createCampusImage("体育馆", "多功能运动场馆，完善的体育设施", 
                "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20indoor%20gymnasium%20with%20basketball%20court%20bright%20lighting%20spectator%20seats&image_size=square_hd"));
        campusImages.add(createCampusImage("实验楼", "先进的科研设备，一流的实验条件", 
                "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20science%20laboratory%20with%20advanced%20equipment%20researchers%20conducting%20experiments%20clean%20and%20professional&image_size=square_hd"));
        info.put("campusImages", campusImages);
        
        return success(info);
    }

    private Map<String, Object> createBanner(String title, String subtitle, String image) {
        Map<String, Object> banner = new LinkedHashMap<>();
        banner.put("title", title);
        banner.put("subtitle", subtitle);
        banner.put("image", image);
        return banner;
    }

    private Map<String, Object> createQuickNav(String title, String description, String icon, String path) {
        Map<String, Object> nav = new LinkedHashMap<>();
        nav.put("title", title);
        nav.put("description", description);
        nav.put("icon", icon);
        nav.put("path", path);
        return nav;
    }

    private Map<String, Object> createStat(String value, String unit, String label) {
        Map<String, Object> stat = new LinkedHashMap<>();
        stat.put("value", value);
        stat.put("unit", unit);
        stat.put("label", label);
        return stat;
    }

    private Map<String, Object> createCampusImage(String title, String description, String image) {
        Map<String, Object> img = new LinkedHashMap<>();
        img.put("title", title);
        img.put("description", description);
        img.put("image", image);
        return img;
    }
}
