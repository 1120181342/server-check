package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import com.xxuniversity.dto.CollegeDTO;
import io.swagger.annotations.*;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/college")
@RequiredArgsConstructor
@Api(tags = "04.学院管理", description = "学院列表、学院详情、导师信息等接口")
public class CollegeController extends BaseController {

    @GetMapping("/list")
    @Cacheable(value = "collegeList", key = "#educationLevel")
    @ApiOperation(value = "获取学院列表", notes = "根据培养层次获取学院列表")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "educationLevel", 
                              value = "培养层次：all-全部, undergraduate-本科, graduate-研究生, doctoral-博士生",
                              defaultValue = "all", allowableValues = "all,undergraduate,graduate,doctoral",
                              paramType = "query", dataType = "String")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = CollegeDTO.class, responseContainer = "List")
    })
    public Result<List<CollegeDTO>> getCollegeList(
            @ApiParam(value = "培养层次")
            @RequestParam(required = false, defaultValue = "all") String educationLevel) {
        
        List<CollegeDTO> colleges = new ArrayList<>();
        
        colleges.add(createCollege(1L, "计算机学院", 
                "培养计算机科学与技术、软件工程、人工智能等领域的高素质工程技术人才",
                45, 6, 3500,
                new String[]{"双一流建设", "国家级重点学科"}));
        
        colleges.add(createCollege(2L, "电子工程学院",
                "专注于电子信息、通信工程、微电子技术等前沿领域的人才培养",
                38, 5, 2800,
                new String[]{"省级重点学院", "校企合作基地"}));
        
        colleges.add(createCollege(3L, "机械工程学院",
                "面向智能制造、先进制造等国家重大需求培养创新型工程人才",
                42, 7, 3200,
                new String[]{"国家级特色专业", "工程教育认证"}));
        
        colleges.add(createCollege(4L, "经济管理学院",
                "培养具有国际视野和创新精神的经济管理人才和企业家",
                55, 10, 4000,
                new String[]{"省级重点学院", "MBA授权点"}));
        
        colleges.add(createCollege(5L, "材料科学与工程学院",
                "探索新材料研发和应用的前沿学科",
                35, 4, 1800,
                new String[]{"双一流建设", "国家重点实验室"}));
        
        colleges.add(createCollege(6L, "人文学院",
                "传承文化，培养人文精神与社会责任感",
                30, 8, 2500,
                new String[]{"省级人文基地", "特色专业"}));
        
        return success(colleges);
    }

    @GetMapping("/detail/{id}")
    @Cacheable(value = "collegeDetail", key = "#id")
    @ApiOperation(value = "获取学院详情", notes = "根据学院ID获取学院详情")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "id", value = "学院ID", required = true, 
                              paramType = "path", dataType = "long", example = "1")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class)
    })
    public Result<Map<String, Object>> getCollegeDetail(
            @ApiParam(value = "学院ID", required = true, example = "1")
            @PathVariable Long id) {
        
        Map<String, Object> detail = new LinkedHashMap<>();
        
        detail.put("id", id);
        detail.put("name", "计算机学院");
        detail.put("description", "计算机学院成立于1958年，是我国最早设立计算机专业的院校之一。学院现有教职工150余人，其中教授45人，副教授60人，博士生导师30人。学院拥有计算机科学与技术一级学科博士点、博士后流动站，是国家级重点学科。");
        detail.put("imageUrl", "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20computer%20science%20building%20exterior%20with%20students%20entering%20tech%20university%20campus&image_size=landscape_4_3");
        
        List<Map<String, Object>> supervisors = new ArrayList<>();
        supervisors.add(createSupervisor("张院士", "中国工程院院士、博士生导师", 
                new String[]{"长江学者", "国家杰青"}, "人工智能、机器学习、计算机视觉"));
        supervisors.add(createSupervisor("李教授", "国家杰出青年基金获得者、博士生导师",
                new String[]{"千人计划", "长江学者"}, "数据科学、大数据分析、云计算"));
        supervisors.add(createSupervisor("王教授", "长江学者特聘教授、博士生导师",
                new String[]{"国家杰青", "创新团队负责人"}, "网络安全、密码学、信息安全"));
        detail.put("supervisors", supervisors);
        
        List<Map<String, Object>> majors = new ArrayList<>();
        majors.add(createMajor("计算机科学与技术", "080901", "培养掌握计算机软硬件基础理论与应用技能的高级专门人才", true, 4));
        majors.add(createMajor("软件工程", "080902", "培养具备软件设计、开发、测试能力的工程技术人才", true, 4));
        majors.add(createMajor("人工智能", "080901T", "研究人工智能理论与技术的新兴学科", false, 4));
        detail.put("majors", majors);
        
        return success(detail);
    }

    @GetMapping("/supervisors")
    @Cacheable(value = "supervisorList", key = "#collegeId + ':' + #page + ':' + #size")
    @ApiOperation(value = "获取导师列表", notes = "分页获取导师列表")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "collegeId", value = "学院ID，不传则获取全部", 
                              paramType = "query", dataType = "long", example = "1"),
            @ApiImplicitParam(name = "page", value = "页码", defaultValue = "1", 
                              paramType = "query", dataType = "int", example = "1"),
            @ApiImplicitParam(name = "size", value = "每页大小", defaultValue = "10", 
                              paramType = "query", dataType = "int", example = "10")
    })
    public Result<Map<String, Object>> getSupervisorList(
            @ApiParam(value = "学院ID")
            @RequestParam(required = false) Long collegeId,
            @ApiParam(value = "页码", example = "1")
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @ApiParam(value = "每页大小", example = "10")
            @RequestParam(required = false, defaultValue = "10") Integer size) {
        
        List<Map<String, Object>> supervisors = new ArrayList<>();
        
        supervisors.add(createSupervisor("张院士", "中国工程院院士、博士生导师",
                new String[]{"长江学者", "国家杰青"}, "人工智能、机器学习、计算机视觉"));
        supervisors.add(createSupervisor("李教授", "国家杰出青年基金获得者、博士生导师",
                new String[]{"千人计划", "长江学者"}, "数据科学、大数据分析、云计算"));
        supervisors.add(createSupervisor("王教授", "长江学者特聘教授、博士生导师",
                new String[]{"国家杰青", "创新团队负责人"}, "网络安全、密码学、信息安全"));
        supervisors.add(createSupervisor("陈教授", "国家优秀青年基金获得者、博士生导师",
                new String[]{"青年拔尖", "新世纪人才"}, "计算机图形学、虚拟现实、人机交互"));
        supervisors.add(createSupervisor("刘教授", "教育部新世纪优秀人才、博士生导师",
                new String[]{"省级特聘", "学术带头人"}, "软件工程、形式化方法、程序验证"));
        supervisors.add(createSupervisor("赵教授", "国家自然科学基金重点项目负责人、博士生导师",
                new String[]{"创新人才", "省级名师"}, "分布式系统、边缘计算、物联网"));
        
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("list", supervisors);
        result.put("total", 50L);
        result.put("page", page);
        result.put("size", size);
        result.put("totalPages", (int) Math.ceil(50.0 / size));
        
        return success(result);
    }

    private CollegeDTO createCollege(Long id, String name, String description,
                                       Integer supervisorCount, Integer majorCount, Integer studentCount,
                                       String[] tags) {
        return CollegeDTO.builder()
                .id(id)
                .name(name)
                .description(description)
                .supervisorCount(supervisorCount)
                .majorCount(majorCount)
                .studentCount(studentCount)
                .tags(tags)
                .build();
    }

    private Map<String, Object> createSupervisor(String name, String title, String[] tags, String research) {
        Map<String, Object> supervisor = new LinkedHashMap<>();
        supervisor.put("name", name);
        supervisor.put("title", title);
        supervisor.put("tags", tags);
        supervisor.put("research", research);
        supervisor.put("avatar", "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20senior%20asian%20male%20professor%20portrait%20academic%20style%20with%20glasses&image_size=square");
        return supervisor;
    }

    private Map<String, Object> createMajor(String name, String code, String description, 
                                               Boolean isTop, Integer duration) {
        Map<String, Object> major = new LinkedHashMap<>();
        major.put("name", name);
        major.put("code", code);
        major.put("description", description);
        major.put("isTop", isTop);
        major.put("duration", duration + "年");
        return major;
    }
}
