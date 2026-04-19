-- 健身房人员信息登记系统数据库初始化脚本
-- 数据库名: gym_system

-- 创建数据库
CREATE DATABASE IF NOT EXISTS gym_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE gym_system;

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(20) NOT NULL UNIQUE COMMENT '角色名称：admin, coach, student',
    description VARCHAR(100) COMMENT '角色描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名/账号',
    password VARCHAR(255) NOT NULL COMMENT '密码（加密存储）',
    real_name VARCHAR(50) NOT NULL COMMENT '真实姓名',
    role_id INT NOT NULL COMMENT '角色ID',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '邮箱',
    gender ENUM('male', 'female', 'unknown') DEFAULT 'unknown' COMMENT '性别',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    last_login TIMESTAMP NULL COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT,
    INDEX idx_username (username),
    INDEX idx_role_id (role_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 教练信息表
CREATE TABLE IF NOT EXISTS coaches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE COMMENT '关联用户ID',
    speciality VARCHAR(200) COMMENT '专长领域',
    experience_years INT DEFAULT 0 COMMENT '从业年限',
    certification VARCHAR(200) COMMENT '资质证书',
    bio TEXT COMMENT '个人简介',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教练信息表';

-- 学员信息表
CREATE TABLE IF NOT EXISTS students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE COMMENT '关联用户ID',
    coach_id INT COMMENT '所属教练ID',
    birth_date DATE COMMENT '出生日期',
    height DECIMAL(5,2) COMMENT '身高(cm)',
    weight DECIMAL(5,2) COMMENT '体重(kg)',
    membership_level ENUM('basic', 'premium', 'vip') DEFAULT 'basic' COMMENT '会员等级',
    join_date DATE COMMENT '入会日期',
    expire_date DATE COMMENT '会员到期日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_membership_level (membership_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学员信息表';

-- 课程表
CREATE TABLE IF NOT EXISTS courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_name VARCHAR(100) NOT NULL COMMENT '课程名称',
    coach_id INT NOT NULL COMMENT '授课教练ID',
    course_type ENUM('private', 'group') DEFAULT 'private' COMMENT '课程类型：私教/团课',
    description TEXT COMMENT '课程描述',
    duration INT DEFAULT 60 COMMENT '课程时长（分钟）',
    max_students INT DEFAULT 1 COMMENT '最大人数',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE RESTRICT,
    INDEX idx_coach_id (coach_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程表';

-- 课程排期表
CREATE TABLE IF NOT EXISTS course_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_id INT NOT NULL COMMENT '课程ID',
    coach_id INT NOT NULL COMMENT '教练ID',
    schedule_date DATE NOT NULL COMMENT '上课日期',
    start_time TIME NOT NULL COMMENT '开始时间',
    end_time TIME NOT NULL COMMENT '结束时间',
    location VARCHAR(100) COMMENT '上课地点',
    current_students INT DEFAULT 0 COMMENT '当前报名人数',
    status ENUM('scheduled', 'ongoing', 'completed', 'cancelled') DEFAULT 'scheduled' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
    INDEX idx_schedule_date (schedule_date),
    INDEX idx_coach_id (coach_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程排期表';

-- 学员课程报名表
CREATE TABLE IF NOT EXISTS student_courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学员ID',
    schedule_id INT NOT NULL COMMENT '排期ID',
    enroll_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '报名时间',
    status ENUM('enrolled', 'attended', 'absent', 'cancelled') DEFAULT 'enrolled' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES course_schedules(id) ON DELETE CASCADE,
    UNIQUE KEY uk_student_schedule (student_id, schedule_id),
    INDEX idx_student_id (student_id),
    INDEX idx_schedule_id (schedule_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学员课程报名表';

-- 打卡记录表
CREATE TABLE IF NOT EXISTS check_ins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '用户ID',
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '打卡时间',
    check_type ENUM('class', 'gym', 'leave') DEFAULT 'class' COMMENT '打卡类型',
    schedule_id INT NULL COMMENT '关联课程排期ID（上课打卡时）',
    status ENUM('success', 'late', 'early', 'absent') DEFAULT 'success' COMMENT '状态',
    remarks VARCHAR(255) COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES course_schedules(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_check_in_time (check_in_time),
    INDEX idx_schedule_id (schedule_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打卡记录表';

-- 成绩表
CREATE TABLE IF NOT EXISTS grades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学员ID',
    coach_id INT NOT NULL COMMENT '评分教练ID',
    schedule_id INT NULL COMMENT '关联课程排期ID',
    grade_type ENUM('physical', 'skill', 'overall', 'attendance') DEFAULT 'overall' COMMENT '成绩类型',
    score DECIMAL(5,2) NOT NULL COMMENT '分数',
    max_score DECIMAL(5,2) DEFAULT 100.00 COMMENT '满分',
    evaluation TEXT COMMENT '评价内容',
    evaluate_date DATE NOT NULL COMMENT '评价日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES course_schedules(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_evaluate_date (evaluate_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成绩表';

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '操作用户ID',
    operation VARCHAR(100) NOT NULL COMMENT '操作名称',
    module VARCHAR(50) COMMENT '模块名称',
    detail TEXT COMMENT '操作详情',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent VARCHAR(255) COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- 初始化角色数据
INSERT INTO roles (role_name, description) VALUES
('admin', '系统管理员'),
('coach', '教练'),
('student', '学员');

-- 初始化管理员账号（密码：admin123，需要在应用中重新加密）
INSERT INTO users (username, password, real_name, role_id, phone, email, gender, status) VALUES
('admin', 'will_be_encrypted', '系统管理员', 1, '13800138000', 'admin@gym.com', 'male', 1);

-- 创建数据库用户并授权（用于应用连接）
-- 请根据实际情况修改密码
-- CREATE USER IF NOT EXISTS 'gym_user'@'localhost' IDENTIFIED BY 'gym_password_2024';
-- GRANT ALL PRIVILEGES ON gym_system.* TO 'gym_user'@'localhost';
-- FLUSH PRIVILEGES;
