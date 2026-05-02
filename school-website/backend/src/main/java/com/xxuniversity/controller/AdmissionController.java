package com.xxuniversity.controller;

import com.xxuniversity.common.Result;
import io.swagger.annotations.*;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/admission")
@RequiredArgsConstructor
@Api(tags = "05.招生管理", description = "招生信息、专业目录、历年分数线、招生公告等接口")
public class AdmissionController extends BaseController {

    @GetMapping("/info/{educationType}")
    @Cacheable(value = "admissionInfo", key = "#educationType")
    @ApiOperation(value = "获取招生信息", notes = "根据培养类型获取招生信息")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "educationType", 
                              value = "培养类型：undergraduate-本科, graduate-研究生, doctoral-博士生",
                              required = true, allowableValues = "undergraduate,graduate,doctoral",
                              paramType = "path", dataType = "String")
    })
    @ApiResponses({
            @ApiResponse(code = 200, message = "获取成功", response = Map.class)
    })
    public Result<Map<String, Object>> getAdmissionInfo(
            @ApiParam(value = "培养类型", required = true, example = "undergraduate")
            @PathVariable String educationType) {
        
        Map<String, Object> info = new LinkedHashMap<>();
        
        String title = getEducationTitle(educationType);
        info.put("title", title);
        info.put("description", getAdmissionDescription(educationType));
        
        info.put("bannerImage", "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20admission%20banner%20students%20walking%20campus%20modern%20buildings%20sunny%20day&image_size=landscape_16_9");
        
        List<Map<String, Object>> highlights = getAdmissionHighlights(educationType);
        info.put("highlights", highlights);
        
        List<Map<String, Object>> stats = getAdmissionStats(educationType);
        info.put("stats", stats);
        
        return success(info);
    }

    @GetMapping("/majors/{educationType}")
    @Cacheable(value = "admissionMajors", key = "#educationType")
    @ApiOperation(value = "获取招生专业目录", notes = "根据培养类型获取招生专业目录")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "educationType", 
                              value = "培养类型：undergraduate-本科, graduate-研究生, doctoral-博士生",
                              required = true, allowableValues = "undergraduate,graduate,doctoral",
                              paramType = "path", dataType = "String")
    })
    public Result<List<Map<String, Object>>> getMajorList(
            @ApiParam(value = "培养类型", required = true, example = "undergraduate")
            @PathVariable String educationType) {
        
        List<Map<String, Object>> majors = new ArrayList<>();
        
        if ("undergraduate".equals(educationType)) {
            majors.add(createUndergraduateMajor("计算机科学与技术", "080901", "工学", 4, 120,
                    "培养掌握计算机软硬件基础理论与应用技能的高级专门人才",
                    new String[]{"双一流建设", "国家重点学科", "国家级特色专业"}));
            majors.add(createUndergraduateMajor("软件工程", "080902", "工学", 4, 90,
                    "培养具备软件设计、开发、测试能力的工程技术人才",
                    new String[]{"工程教育认证", "省级特色专业"}));
            majors.add(createUndergraduateMajor("人工智能", "080901T", "工学", 4, 60,
                    "研究人工智能理论与技术的新兴学科",
                    new String[]{"新工科专业", "双一流建设"}));
            majors.add(createUndergraduateMajor("电子信息工程", "080701", "工学", 4, 100,
                    "培养电子信息领域的工程技术人才",
                    new String[]{"国家级特色专业"}));
        } else if ("graduate".equals(educationType)) {
            majors.add(createGraduateMajor("计算机科学与技术", "081200", "学术型", 3,
                    "研究计算机理论与技术的前沿方向",
                    new String[]{"国家重点学科", "一级学科博士点"},
                    Arrays.asList(
                            createResearchDirection("人工智能与机器学习", "研究深度学习、强化学习、计算机视觉等前沿技术"),
                            createResearchDirection("数据科学与大数据", "研究数据挖掘、知识图谱、大数据处理技术"),
                            createResearchDirection("网络与信息安全", "研究密码学、网络安全、信息对抗技术")
                    )));
            majors.add(createGraduateMajor("软件工程", "083500", "学术型", 3,
                    "研究软件工程理论与实践",
                    new String[]{"国家重点学科", "一级学科博士点"},
                    Arrays.asList(
                            createResearchDirection("软件理论与形式化方法", "研究程序语言、形式化验证、编译技术"),
                            createResearchDirection("软件系统与架构", "研究分布式系统、微服务、云计算架构")
                    )));
            majors.add(createGraduateMajor("电子信息", "085400", "专业型", 2,
                    "电子信息领域工程硕士",
                    new String[]{"国家级专业学位改革试点"},
                    Arrays.asList(
                            createResearchDirection("人工智能工程", "人工智能技术在工程领域的应用"),
                            createResearchDirection("软件工程", "大型软件系统开发与管理")
                    )));
        } else if ("doctoral".equals(educationType)) {
            majors.add(createDoctoralMajor("计算机科学与技术", "081200", 4,
                    "培养计算机领域的高层次研究人才",
                    new String[]{"国家重点学科", "博士后流动站"},
                    Arrays.asList(
                            createResearchDirection("人工智能理论与技术", "研究人工智能基础理论、机器学习理论、深度神经网络理论"),
                            createResearchDirection("网络空间安全", "研究密码学、网络安全、可信计算、数据隐私保护"),
                            createResearchDirection("计算机系统结构", "研究高性能计算、分布式系统、云计算、边缘计算")
                    )));
            majors.add(createDoctoralMajor("软件工程", "083500", 4,
                    "培养软件工程领域的学术领军人才",
                    new String[]{"国家重点学科", "博士后流动站"},
                    Arrays.asList(
                            createResearchDirection("软件理论与形式化方法", "研究程序语义、形式化验证、模型检测、定理证明"),
                            createResearchDirection("智能软件工程", "研究AI驱动的软件工程、智能代码生成、自动化测试")
                    )));
        }
        
        return success(majors);
    }

    @GetMapping("/scores/{educationType}")
    @Cacheable(value = "admissionScores", key = "#educationType")
    @ApiOperation(value = "获取历年分数线", notes = "根据培养类型获取历年分数线")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "educationType", 
                              value = "培养类型：undergraduate-本科, graduate-研究生, doctoral-博士生",
                              required = true, allowableValues = "undergraduate,graduate,doctoral",
                              paramType = "path", dataType = "String")
    })
    public Result<List<Map<String, Object>>> getScoreLines(
            @ApiParam(value = "培养类型", required = true, example = "undergraduate")
            @PathVariable String educationType) {
        
        List<Map<String, Object>> scores = new ArrayList<>();
        
        if ("undergraduate".equals(educationType)) {
            scores.add(createUndergraduateScore(2023, 620, 605, 580));
            scores.add(createUndergraduateScore(2022, 615, 598, 575));
            scores.add(createUndergraduateScore(2021, 610, 592, 570));
            scores.add(createUndergraduateScore(2020, 605, 588, 565));
        } else if ("graduate".equals(educationType)) {
            scores.add(createGraduateScore(2024, 315, 300, 340, 320, 290, 270));
            scores.add(createGraduateScore(2023, 310, 295, 335, 315, 285, 265));
            scores.add(createGraduateScore(2022, 305, 290, 330, 310, 280, 260));
        } else if ("doctoral".equals(educationType)) {
            scores.add(createDoctoralScore(2024, "申请-考核制", "60%", "80分"));
            scores.add(createDoctoralScore(2023, "申请-考核制", "58%", "78分"));
            scores.add(createDoctoralScore(2022, "申请-考核制", "55%", "75分"));
        }
        
        return success(scores);
    }

    @GetMapping("/notices")
    @Cacheable(value = "admissionNotices", key = "#educationType + ':' + #page")
    @ApiOperation(value = "获取招生公告", notes = "根据培养类型获取招生公告列表")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "educationType", 
                              value = "培养类型：undergraduate-本科, graduate-研究生, doctoral-博士生, all-全部",
                              defaultValue = "all", allowableValues = "all,undergraduate,graduate,doctoral",
                              paramType = "query", dataType = "String"),
            @ApiImplicitParam(name = "page", value = "页码", defaultValue = "1", 
                              paramType = "query", dataType = "int", example = "1")
    })
    public Result<Map<String, Object>> getNotices(
            @ApiParam(value = "培养类型")
            @RequestParam(required = false, defaultValue = "all") String educationType,
            @ApiParam(value = "页码", example = "1")
            @RequestParam(required = false, defaultValue = "1") Integer page) {
        
        List<Map<String, Object>> notices = new ArrayList<>();
        
        notices.add(createNotice("XX大学2024年硕士研究生招生简章", 
                "2024年硕士研究生招生工作即将开始，现将招生简章公布如下...",
                "2024-09-15", "graduate", "重要"));
        notices.add(createNotice("XX大学2024年博士研究生申请-考核制招生办法",
                "为进一步完善博士研究生招生选拔机制，提高招生质量...",
                "2024-09-10", "doctoral", "重要"));
        notices.add(createNotice("XX大学2024年本科招生章程",
                "为规范全日制普通本科招生工作，维护学校和考生的合法权益...",
                "2024-05-20", "undergraduate", "最新"));
        notices.add(createNotice("2024年硕士研究生招生专业目录",
                "2024年各学院硕士研究生招生专业目录已发布，请考生查阅...",
                "2024-09-08", "graduate", "通知"));
        notices.add(createNotice("关于2024年推免生接收工作的通知",
                "2024年推荐免试研究生接收工作即将开始，现将有关事项通知如下...",
                "2024-09-05", "graduate", "重要"));
        
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("list", notices);
        result.put("total", 25L);
        result.put("page", page);
        result.put("size", 10);
        result.put("totalPages", 3);
        
        return success(result);
    }

    private String getEducationTitle(String type) {
        switch (type) {
            case "undergraduate": return "本科生招生";
            case "graduate": return "研究生招生";
            case "doctoral": return "博士生招生";
            default: return "招生信息";
        }
    }

    private String getAdmissionDescription(String type) {
        switch (type) {
            case "undergraduate":
                return "XX大学是教育部直属全国重点大学，是国家\"双一流\"建设高校。学校面向全国招收本科生，培养具有创新精神和实践能力的高素质人才。";
            case "graduate":
                return "学校拥有完善的研究生培养体系，现有博士学位授权一级学科25个，硕士学位授权一级学科40个。我们致力于培养具有国际视野的高层次学术人才和工程技术人才。";
            case "doctoral":
                return "学校秉承\"厚德载物、自强不息\"的校训精神，致力于培养具有创新能力、国际视野和学术领军潜质的高层次人才。博士生招生采用申请-考核制、硕博连读、直博生等多种选拔方式。";
            default:
                return "";
        }
    }

    private List<Map<String, Object>> getAdmissionHighlights(String type) {
        List<Map<String, Object>> highlights = new ArrayList<>();
        
        if ("doctoral".equals(type)) {
            highlights.add(createHighlight("申请-考核制", "全面实施申请-考核制选拔，注重综合素质和科研潜力"));
            highlights.add(createHighlight("硕博连读", "面向优秀在读硕士生开放硕博连读通道"));
            highlights.add(createHighlight("直博生", "面向优秀应届本科生招收直博生"));
            highlights.add(createHighlight("优厚奖学金", "提供国家奖学金、学业奖学金、助教助研岗位等"));
        } else {
            highlights.add(createHighlight("双一流建设", "学校是国家\"双一流\"建设高校，学科实力雄厚"));
            highlights.add(createHighlight("优质师资", "两院院士15人，国家级教学名师20余人"));
            highlights.add(createHighlight("国际化培养", "与全球100余所知名大学建立合作交流关系"));
            highlights.add(createHighlight("就业前景", "毕业生就业率保持在95%以上，就业质量高"));
        }
        
        return highlights;
    }

    private List<Map<String, Object>> getAdmissionStats(String type) {
        List<Map<String, Object>> stats = new ArrayList<>();
        
        if ("undergraduate".equals(type)) {
            stats.add(createStat("5000+", "人/年", "本科招生计划"));
            stats.add(createStat("80+", "个", "本科专业"));
            stats.add(createStat("95%+", "就业率", "毕业生就业率"));
            stats.add(createStat("40%+", "继续深造率", "考研/出国深造比例"));
        } else if ("graduate".equals(type)) {
            stats.add(createStat("3000+", "人/年", "硕士招生计划"));
            stats.add(createStat("40+", "个", "一级学科"));
            stats.add(createStat("25+", "个", "博士点"));
            stats.add(createStat("500+", "名", "博士生导师"));
        } else if ("doctoral".equals(type)) {
            stats.add(createStat("800+", "人/年", "博士招生计划"));
            stats.add(createStat("25+", "个", "一级学科博士点"));
            stats.add(createStat("30+", "个", "博士后流动站"));
            stats.add(createStat("100%", "奖学金覆盖率", "全奖覆盖"));
        }
        
        return stats;
    }

    private Map<String, Object> createHighlight(String title, String description) {
        Map<String, Object> highlight = new LinkedHashMap<>();
        highlight.put("title", title);
        highlight.put("description", description);
        return highlight;
    }

    private Map<String, Object> createStat(String value, String unit, String label) {
        Map<String, Object> stat = new LinkedHashMap<>();
        stat.put("value", value);
        stat.put("unit", unit);
        stat.put("label", label);
        return stat;
    }

    private Map<String, Object> createUndergraduateMajor(String name, String code, String degree, 
                                                          int duration, int plan, String description, String[] tags) {
        Map<String, Object> major = new LinkedHashMap<>();
        major.put("name", name);
        major.put("code", code);
        major.put("degree", degree);
        major.put("duration", duration + "年");
        major.put("plan", plan);
        major.put("description", description);
        major.put("tags", tags);
        return major;
    }

    private Map<String, Object> createGraduateMajor(String name, String code, String type, 
                                                     int duration, String description, String[] tags,
                                                     List<Map<String, Object>> directions) {
        Map<String, Object> major = new LinkedHashMap<>();
        major.put("name", name);
        major.put("code", code);
        major.put("type", type);
        major.put("duration", duration + "年");
        major.put("description", description);
        major.put("tags", tags);
        major.put("directions", directions);
        return major;
    }

    private Map<String, Object> createDoctoralMajor(String name, String code, 
                                                      int duration, String description, String[] tags,
                                                      List<Map<String, Object>> directions) {
        Map<String, Object> major = new LinkedHashMap<>();
        major.put("name", name);
        major.put("code", code);
        major.put("duration", duration + "年");
        major.put("description", description);
        major.put("tags", tags);
        major.put("directions", directions);
        return major;
    }

    private Map<String, Object> createResearchDirection(String name, String description) {
        Map<String, Object> direction = new LinkedHashMap<>();
        direction.put("name", name);
        direction.put("description", description);
        return direction;
    }

    private Map<String, Object> createUndergraduateScore(int year, int score1, int score2, int score3) {
        Map<String, Object> score = new LinkedHashMap<>();
        score.put("year", year);
        score.put("scienceScore", score1);
        score.put("engineeringScore", score2);
        score.put("liberalArtsScore", score3);
        return score;
    }

    private Map<String, Object> createGraduateScore(int year, int academicTotal, int academicSubject,
                                                     int professionalTotal, int professionalSubject,
                                                     int english, int politics) {
        Map<String, Object> score = new LinkedHashMap<>();
        score.put("year", year);
        score.put("academicTotal", academicTotal);
        score.put("academicSubject", academicSubject);
        score.put("professionalTotal", professionalTotal);
        score.put("professionalSubject", professionalSubject);
        score.put("english", english);
        score.put("politics", politics);
        return score;
    }

    private Map<String, Object> createDoctoralScore(int year, String mode, String passRate, String avgScore) {
        Map<String, Object> score = new LinkedHashMap<>();
        score.put("year", year);
        score.put("mode", mode);
        score.put("passRate", passRate);
        score.put("avgScore", avgScore);
        return score;
    }

    private Map<String, Object> createNotice(String title, String summary, String date, 
                                               String category, String tag) {
        Map<String, Object> notice = new LinkedHashMap<>();
        notice.put("title", title);
        notice.put("summary", summary);
        notice.put("date", date);
        notice.put("category", category);
        notice.put("tag", tag);
        return notice;
    }
}
