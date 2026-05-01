-- 创建数据库
CREATE DATABASE IF NOT EXISTS school_website DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE school_website;

-- 用户表
CREATE TABLE IF NOT EXISTS t_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id VARCHAR(50) NOT NULL COMMENT '用户ID(学号/工号)',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(BCrypt加密)',
    real_name VARCHAR(50) COMMENT '真实姓名',
    email VARCHAR(100) COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    avatar VARCHAR(500) COMMENT '头像URL',
    gender VARCHAR(10) COMMENT '性别',
    department VARCHAR(100) COMMENT '学院/部门',
    role VARCHAR(20) NOT NULL COMMENT '角色:student/teacher/admin',
    enroll_date DATETIME COMMENT '入学/入职日期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '是否删除:0-否,1-是',
    UNIQUE KEY uk_user_id (user_id),
    KEY idx_username (username),
    KEY idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 新闻表
CREATE TABLE IF NOT EXISTS t_news (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    title VARCHAR(200) NOT NULL COMMENT '新闻标题',
    summary VARCHAR(500) COMMENT '新闻摘要',
    content TEXT COMMENT '新闻内容',
    category VARCHAR(50) COMMENT '分类:research/academic/admission/award',
    image_url VARCHAR(500) COMMENT '图片URL',
    author VARCHAR(50) COMMENT '作者',
    source VARCHAR(50) COMMENT '来源',
    views INT DEFAULT 0 COMMENT '浏览量',
    is_featured TINYINT DEFAULT 0 COMMENT '是否头条:0-否,1-是',
    publish_time DATETIME COMMENT '发布时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '是否删除:0-否,1-是',
    KEY idx_category (category),
    KEY idx_publish_time (publish_time),
    KEY idx_is_featured (is_featured)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻表';

-- 学院表
CREATE TABLE IF NOT EXISTS t_college (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    name VARCHAR(100) NOT NULL COMMENT '学院名称',
    description TEXT COMMENT '学院简介',
    image_url VARCHAR(500) COMMENT '学院图片',
    supervisor_count INT DEFAULT 0 COMMENT '导师数量',
    major_count INT DEFAULT 0 COMMENT '专业数量',
    student_count INT DEFAULT 0 COMMENT '学生数量',
    sort INT DEFAULT 0 COMMENT '排序',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '是否删除:0-否,1-是'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学院表';

-- 专业表
CREATE TABLE IF NOT EXISTS t_major (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    college_id BIGINT COMMENT '学院ID',
    code VARCHAR(20) NOT NULL COMMENT '专业代码',
    name VARCHAR(100) NOT NULL COMMENT '专业名称',
    description TEXT COMMENT '专业简介',
    education_level VARCHAR(20) COMMENT '培养层次:undergraduate/graduate/doctoral',
    duration VARCHAR(20) COMMENT '学制',
    is_top TINYINT DEFAULT 0 COMMENT '是否一流专业:0-否,1-是',
    sort INT DEFAULT 0 COMMENT '排序',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '是否删除:0-否,1-是',
    KEY idx_college_id (college_id),
    KEY idx_education_level (education_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='专业表';

-- 导师表
CREATE TABLE IF NOT EXISTS t_supervisor (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id VARCHAR(50) COMMENT '用户ID',
    college_id BIGINT COMMENT '学院ID',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    title VARCHAR(100) COMMENT '职称',
    research VARCHAR(500) COMMENT '研究方向',
    avatar VARCHAR(500) COMMENT '头像',
    tags VARCHAR(500) COMMENT '标签(逗号分隔)',
    sort INT DEFAULT 0 COMMENT '排序',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '是否删除:0-否,1-是',
    KEY idx_college_id (college_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='导师表';

-- 招生公告表
CREATE TABLE IF NOT EXISTS t_admission_notice (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    summary VARCHAR(500) COMMENT '摘要',
    content TEXT COMMENT '内容',
    education_level VARCHAR(20) COMMENT '培养层次:undergraduate/graduate/doctoral',
    notice_type TINYINT COMMENT '类型:1-重要通知,2-招生政策,3-常见问题',
    publish_time DATETIME COMMENT '发布时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '是否删除:0-否,1-是',
    KEY idx_education_level (education_level),
    KEY idx_publish_time (publish_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='招生公告表';

-- 初始化用户数据(密码:123456, BCrypt加密)
INSERT INTO t_user (user_id, username, password, real_name, email, phone, gender, department, role, enroll_date) VALUES
('2021001', '2021001', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5E', '张三', '2021001@xxuniversity.edu.cn', '13888888881', '男', '计算机学院', 'student', '2021-09-01 00:00:00'),
('2021002', '2021002', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5E', '李四', '2021002@xxuniversity.edu.cn', '13888888882', '女', '电子工程学院', 'student', '2021-09-01 00:00:00'),
('T001', 'T001', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5E', '李老师', 'teacher1@xxuniversity.edu.cn', '13988888881', '男', '电子工程学院', 'teacher', '2015-09-01 00:00:00'),
('A001', 'A001', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5E', '管理员', 'admin@xxuniversity.edu.cn', '13988888899', '男', '信息化管理处', 'admin', '2020-01-01 00:00:00');

-- 初始化新闻数据
INSERT INTO t_news (title, summary, content, category, author, source, views, is_featured, publish_time) VALUES
('我校计算机学院团队在人工智能领域取得重大突破', '近日，我校计算机学院张院士团队在自然语言处理领域取得重大突破，相关研究成果发表于国际顶级期刊《Nature Machine Intelligence》。', '<p>详细内容...</p>', 'research', '张院士团队', '计算机学院', 8560, 1, '2024-07-25 10:00:00'),
('关于2025年博士生招生工作的重要通知', '根据教育部有关文件精神，结合我校实际情况，现将2025年博士研究生招生工作安排如下。', '<p>详细内容...</p>', 'admission', '招生办公室', '研究生院', 6789, 0, '2024-07-20 09:00:00'),
('我校博士生在国际顶级会议发表论文并获最佳论文奖', '在近日召开的第45届国际计算机体系结构会议(ISCA 2024)上，我校电子工程学院李教授指导的博士生王同学的论文荣获最佳论文奖。', '<p>详细内容...</p>', 'award', '李教授团队', '电子工程学院', 5432, 0, '2024-07-18 14:00:00');

-- 初始化学院数据
INSERT INTO t_college (name, description, supervisor_count, major_count, student_count, sort) VALUES
('计算机学院', '培养计算机科学与技术、软件工程、人工智能等领域的高素质工程技术人才', 45, 6, 3500, 1),
('电子工程学院', '专注于电子信息、通信工程、微电子技术等前沿领域的人才培养', 38, 5, 2800, 2),
('机械工程学院', '面向智能制造、先进制造等国家重大需求培养创新型工程人才', 42, 7, 3200, 3),
('经济管理学院', '培养具有国际视野和创新精神的经济管理人才和企业家', 55, 10, 4000, 4);

-- 初始化导师数据
INSERT INTO t_supervisor (college_id, name, title, research, tags, sort) VALUES
(1, '张院士', '中国工程院院士、博士生导师', '人工智能、机器学习、计算机视觉', '长江学者,国家杰青', 1),
(1, '李教授', '国家杰出青年基金获得者、博士生导师', '数据科学、大数据分析、云计算', '千人计划,长江学者', 2),
(2, '王教授', '长江学者特聘教授、博士生导师', '网络安全、密码学、信息安全', '国家杰青,创新团队负责人', 1);
