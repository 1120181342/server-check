from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(20), unique=True, nullable=False, comment='角色名称')
    description = db.Column(db.String(100), comment='角色描述')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'role_name': self.role_name,
            'description': self.description
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column('password', db.String(255), nullable=False, comment='密码')
    real_name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, comment='角色ID')
    phone = db.Column(db.String(20), comment='联系电话')
    email = db.Column(db.String(100), comment='邮箱')
    gender = db.Column(db.Enum('male', 'female', 'unknown'), default='unknown', comment='性别')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1-启用，0-禁用')
    last_login = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'role_id': self.role_id,
            'role_name': self.role.role_name if self.role else None,
            'phone': self.phone,
            'email': self.email,
            'gender': self.gender,
            'status': self.status,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Coach(db.Model):
    __tablename__ = 'coaches'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, comment='用户ID')
    speciality = db.Column(db.String(200), comment='专长领域')
    experience_years = db.Column(db.Integer, default=0, comment='从业年限')
    certification = db.Column(db.String(200), comment='资质证书')
    bio = db.Column(db.Text, comment='个人简介')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='coach_info', uselist=False)
    students = db.relationship('Student', backref='coach', lazy='dynamic')
    courses = db.relationship('Course', backref='coach', lazy='dynamic')
    schedules = db.relationship('CourseSchedule', backref='coach', lazy='dynamic')
    grades = db.relationship('Grade', backref='coach', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'speciality': self.speciality,
            'experience_years': self.experience_years,
            'certification': self.certification,
            'bio': self.bio,
            'user': self.user.to_dict() if self.user else None
        }

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, comment='用户ID')
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'), nullable=True, comment='教练ID')
    birth_date = db.Column(db.Date, comment='出生日期')
    height = db.Column(db.Numeric(5, 2), comment='身高(cm)')
    weight = db.Column(db.Numeric(5, 2), comment='体重(kg)')
    membership_level = db.Column(db.Enum('basic', 'premium', 'vip'), default='basic', comment='会员等级')
    join_date = db.Column(db.Date, comment='入会日期')
    expire_date = db.Column(db.Date, comment='会员到期日期')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='student_info', uselist=False)
    student_courses = db.relationship('StudentCourse', backref='student', lazy='dynamic')
    check_ins = db.relationship('CheckIn', backref='student', lazy='dynamic', foreign_keys='CheckIn.user_id')
    grades = db.relationship('Grade', backref='student', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'coach_id': self.coach_id,
            'birth_date': str(self.birth_date) if self.birth_date else None,
            'height': float(self.height) if self.height else None,
            'weight': float(self.weight) if self.weight else None,
            'membership_level': self.membership_level,
            'join_date': str(self.join_date) if self.join_date else None,
            'expire_date': str(self.expire_date) if self.expire_date else None,
            'user': self.user.to_dict() if self.user else None,
            'coach': self.coach.user.real_name if self.coach and self.coach.user else None
        }

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_name = db.Column(db.String(100), nullable=False, comment='课程名称')
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'), nullable=False, comment='教练ID')
    course_type = db.Column(db.Enum('private', 'group'), default='private', comment='课程类型')
    description = db.Column(db.Text, comment='课程描述')
    duration = db.Column(db.Integer, default=60, comment='课程时长（分钟）')
    max_students = db.Column(db.Integer, default=1, comment='最大人数')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1-启用，0-禁用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    schedules = db.relationship('CourseSchedule', backref='course', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_name': self.course_name,
            'coach_id': self.coach_id,
            'coach_name': self.coach.user.real_name if self.coach and self.coach.user else None,
            'course_type': self.course_type,
            'description': self.description,
            'duration': self.duration,
            'max_students': self.max_students,
            'status': self.status
        }

class CourseSchedule(db.Model):
    __tablename__ = 'course_schedules'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, comment='课程ID')
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'), nullable=False, comment='教练ID')
    schedule_date = db.Column(db.Date, nullable=False, comment='上课日期')
    start_time = db.Column(db.Time, nullable=False, comment='开始时间')
    end_time = db.Column(db.Time, nullable=False, comment='结束时间')
    location = db.Column(db.String(100), comment='上课地点')
    current_students = db.Column(db.Integer, default=0, comment='当前报名人数')
    status = db.Column(db.Enum('scheduled', 'ongoing', 'completed', 'cancelled'), default='scheduled', comment='状态')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    student_courses = db.relationship('StudentCourse', backref='schedule', lazy='dynamic')
    check_ins = db.relationship('CheckIn', backref='schedule', lazy='dynamic')
    grades = db.relationship('Grade', backref='schedule', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'course_name': self.course.course_name if self.course else None,
            'coach_id': self.coach_id,
            'coach_name': self.coach.user.real_name if self.coach and self.coach.user else None,
            'schedule_date': str(self.schedule_date),
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'location': self.location,
            'current_students': self.current_students,
            'max_students': self.course.max_students if self.course else 0,
            'status': self.status
        }

class StudentCourse(db.Model):
    __tablename__ = 'student_courses'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    schedule_id = db.Column(db.Integer, db.ForeignKey('course_schedules.id'), nullable=False, comment='排期ID')
    enroll_time = db.Column(db.DateTime, default=datetime.utcnow, comment='报名时间')
    status = db.Column(db.Enum('enrolled', 'attended', 'absent', 'cancelled'), default='enrolled', comment='状态')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'schedule_id', name='uk_student_schedule'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'schedule_id': self.schedule_id,
            'enroll_time': self.enroll_time.strftime('%Y-%m-%d %H:%M:%S') if self.enroll_time else None,
            'status': self.status,
            'schedule': self.schedule.to_dict() if self.schedule else None
        }

class CheckIn(db.Model):
    __tablename__ = 'check_ins'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow, comment='打卡时间')
    check_type = db.Column(db.Enum('class', 'gym', 'leave'), default='class', comment='打卡类型')
    schedule_id = db.Column(db.Integer, db.ForeignKey('course_schedules.id'), nullable=True, comment='排期ID')
    status = db.Column(db.Enum('success', 'late', 'early', 'absent'), default='success', comment='状态')
    remarks = db.Column(db.String(255), comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'check_in_time': self.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if self.check_in_time else None,
            'check_type': self.check_type,
            'schedule_id': self.schedule_id,
            'status': self.status,
            'remarks': self.remarks,
            'schedule': self.schedule.to_dict() if self.schedule else None
        }

class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'), nullable=False, comment='教练ID')
    schedule_id = db.Column(db.Integer, db.ForeignKey('course_schedules.id'), nullable=True, comment='排期ID')
    grade_type = db.Column(db.Enum('physical', 'skill', 'overall', 'attendance'), default='overall', comment='成绩类型')
    score = db.Column(db.Numeric(5, 2), nullable=False, comment='分数')
    max_score = db.Column(db.Numeric(5, 2), default=100.00, comment='满分')
    evaluation = db.Column(db.Text, comment='评价内容')
    evaluate_date = db.Column(db.Date, nullable=False, comment='评价日期')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.real_name if self.student and self.student.user else None,
            'coach_id': self.coach_id,
            'coach_name': self.coach.user.real_name if self.coach and self.coach.user else None,
            'schedule_id': self.schedule_id,
            'grade_type': self.grade_type,
            'score': float(self.score),
            'max_score': float(self.max_score),
            'evaluation': self.evaluation,
            'evaluate_date': str(self.evaluate_date),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    operation = db.Column(db.String(100), nullable=False, comment='操作名称')
    module = db.Column(db.String(50), comment='模块名称')
    detail = db.Column(db.Text, comment='操作详情')
    ip_address = db.Column(db.String(50), comment='IP地址')
    user_agent = db.Column(db.String(255), comment='用户代理')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'operation': self.operation,
            'module': self.module,
            'detail': self.detail,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
