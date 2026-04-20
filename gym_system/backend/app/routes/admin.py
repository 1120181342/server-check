from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import User, Role, Coach, Student, Course, CourseSchedule, StudentCourse, CheckIn, Grade, OperationLog
from app import db
from routes import role_required, log_operation, get_current_user
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        role_id = request.args.get('role_id', type=int)
        status = request.args.get('status', type=int)
        
        query = User.query
        
        if keyword:
            query = query.filter(
                or_(
                    User.real_name.like(f'%{keyword}%'),
                    User.username.like(f'%{keyword}%'),
                    User.phone.like(f'%{keyword}%'),
                    User.email.like(f'%{keyword}%')
                )
            )
        if role_id:
            query = query.filter(User.role_id == role_id)
        if status is not None:
            query = query.filter(User.status == status)
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = [u.to_dict() for u in pagination.items]
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'users': users,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取用户列表失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_user_detail(user_id):
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        result = user.to_dict()
        
        if user.role.role_name == 'coach':
            coach = Coach.query.filter_by(user_id=user.id).first()
            if coach:
                result['coach_info'] = coach.to_dict()
                result['coach_info']['student_count'] = coach.students.count()
                result['coach_info']['course_count'] = coach.courses.count()
        elif user.role.role_name == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                result['student_info'] = student.to_dict()
                result['student_info']['grade_count'] = student.grades.count()
                result['student_info']['check_in_count'] = student.check_ins.count()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取用户详情失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_user():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        username = data.get('username')
        password = data.get('password', '123456')
        real_name = data.get('real_name')
        role_id = data.get('role_id')
        phone = data.get('phone')
        email = data.get('email')
        gender = data.get('gender', 'unknown')
        
        if not username or not real_name or not role_id:
            return jsonify({
                'code': 400,
                'message': '用户名、真实姓名和角色不能为空',
                'data': None
            }), 400
        
        existing = User.query.filter_by(username=username).first()
        if existing:
            return jsonify({
                'code': 400,
                'message': '用户名已存在',
                'data': None
            }), 400
        
        user = User(
            username=username,
            real_name=real_name,
            role_id=role_id,
            phone=phone,
            email=email,
            gender=gender,
            status=1
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        role = Role.query.get(role_id)
        if role:
            if role.role_name == 'coach':
                coach = Coach(
                    user_id=user.id,
                    speciality=data.get('speciality'),
                    experience_years=data.get('experience_years', 0),
                    certification=data.get('certification'),
                    bio=data.get('bio')
                )
                db.session.add(coach)
            elif role.role_name == 'student':
                student = Student(
                    user_id=user.id,
                    coach_id=data.get('coach_id'),
                    membership_level=data.get('membership_level', 'basic'),
                    join_date=date.today()
                )
                if data.get('birth_date'):
                    student.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
                if data.get('height'):
                    student.height = data['height']
                if data.get('weight'):
                    student.weight = data['weight']
                if data.get('expire_date'):
                    student.expire_date = datetime.strptime(data['expire_date'], '%Y-%m-%d').date()
                
                db.session.add(student)
        
        db.session.commit()
        
        log_operation(
            user_id=current_user.id,
            operation='创建用户',
            module='用户管理',
            detail=f'管理员 {current_user.real_name} 创建了用户 {username}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '用户创建成功',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'创建用户失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_user(user_id):
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        if 'real_name' in data:
            user.real_name = data['real_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'email' in data:
            user.email = data['email']
        if 'gender' in data:
            user.gender = data['gender']
        if 'status' in data:
            user.status = data['status']
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        if user.role.role_name == 'coach':
            coach = Coach.query.filter_by(user_id=user.id).first()
            if coach:
                if 'speciality' in data:
                    coach.speciality = data['speciality']
                if 'experience_years' in data:
                    coach.experience_years = data['experience_years']
                if 'certification' in data:
                    coach.certification = data['certification']
                if 'bio' in data:
                    coach.bio = data['bio']
        
        elif user.role.role_name == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                if 'coach_id' in data:
                    student.coach_id = data['coach_id']
                if 'membership_level' in data:
                    student.membership_level = data['membership_level']
                if 'birth_date' in data:
                    if data['birth_date']:
                        student.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
                    else:
                        student.birth_date = None
                if 'height' in data:
                    student.height = data['height']
                if 'weight' in data:
                    student.weight = data['weight']
                if 'expire_date' in data:
                    if data['expire_date']:
                        student.expire_date = datetime.strptime(data['expire_date'], '%Y-%m-%d').date()
                    else:
                        student.expire_date = None
        
        db.session.commit()
        
        log_operation(
            user_id=current_user.id,
            operation='更新用户',
            module='用户管理',
            detail=f'管理员 {current_user.real_name} 更新了用户 {user.username}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '用户更新成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新用户失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_user(user_id):
    try:
        current_user = get_current_user()
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        if user.id == current_user.id:
            return jsonify({
                'code': 400,
                'message': '不能删除自己的账号',
                'data': None
            }), 400
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        log_operation(
            user_id=current_user.id,
            operation='删除用户',
            module='用户管理',
            detail=f'管理员 {current_user.real_name} 删除了用户 {username}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '用户删除成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除用户失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/coaches', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_coaches():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        
        query = Coach.query
        
        if keyword:
            query = query.join(User, Coach.user_id == User.id).filter(
                or_(
                    User.real_name.like(f'%{keyword}%'),
                    User.username.like(f'%{keyword}%'),
                    User.phone.like(f'%{keyword}%')
                )
            )
        
        pagination = query.order_by(Coach.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        coaches = []
        for coach in pagination.items:
            coach_dict = coach.to_dict()
            coach_dict['student_count'] = coach.students.count()
            coach_dict['course_count'] = coach.courses.count()
            coaches.append(coach_dict)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'coaches': coaches,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取教练列表失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/students', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_students():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        coach_id = request.args.get('coach_id', type=int)
        membership_level = request.args.get('membership_level')
        
        query = Student.query
        
        if keyword:
            query = query.join(User, Student.user_id == User.id).filter(
                or_(
                    User.real_name.like(f'%{keyword}%'),
                    User.username.like(f'%{keyword}%'),
                    User.phone.like(f'%{keyword}%')
                )
            )
        if coach_id:
            query = query.filter(Student.coach_id == coach_id)
        if membership_level:
            query = query.filter(Student.membership_level == membership_level)
        
        pagination = query.order_by(Student.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        students = [s.to_dict() for s in pagination.items]
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'students': students,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取学员列表失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/courses', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_courses():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        coach_id = request.args.get('coach_id', type=int)
        course_type = request.args.get('course_type')
        status = request.args.get('status', type=int)
        
        query = Course.query
        
        if keyword:
            query = query.filter(Course.course_name.like(f'%{keyword}%'))
        if coach_id:
            query = query.filter(Course.coach_id == coach_id)
        if course_type:
            query = query.filter(Course.course_type == course_type)
        if status is not None:
            query = query.filter(Course.status == status)
        
        pagination = query.order_by(Course.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        courses = [c.to_dict() for c in pagination.items]
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'courses': courses,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取课程列表失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/courses', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_course():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        course_name = data.get('course_name')
        coach_id = data.get('coach_id')
        course_type = data.get('course_type', 'private')
        description = data.get('description')
        duration = data.get('duration', 60)
        max_students = data.get('max_students', 1)
        
        if not course_name or not coach_id:
            return jsonify({
                'code': 400,
                'message': '课程名称和教练不能为空',
                'data': None
            }), 400
        
        course = Course(
            course_name=course_name,
            coach_id=coach_id,
            course_type=course_type,
            description=description,
            duration=duration,
            max_students=max_students,
            status=1
        )
        
        db.session.add(course)
        db.session.commit()
        
        log_operation(
            user_id=current_user.id,
            operation='创建课程',
            module='课程管理',
            detail=f'管理员 {current_user.real_name} 创建了课程 {course_name}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '课程创建成功',
            'data': course.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'创建课程失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/schedules', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_schedules():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        course_id = request.args.get('course_id', type=int)
        coach_id = request.args.get('coach_id', type=int)
        schedule_date = request.args.get('schedule_date')
        status = request.args.get('status')
        
        query = CourseSchedule.query
        
        if course_id:
            query = query.filter(CourseSchedule.course_id == course_id)
        if coach_id:
            query = query.filter(CourseSchedule.coach_id == coach_id)
        if schedule_date:
            query = query.filter(CourseSchedule.schedule_date == schedule_date)
        if status:
            query = query.filter(CourseSchedule.status == status)
        
        pagination = query.order_by(CourseSchedule.schedule_date.desc(), 
                                     CourseSchedule.start_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        schedules = [s.to_dict() for s in pagination.items]
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'schedules': schedules,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取课程排期失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/schedules', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_schedule():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        course_id = data.get('course_id')
        schedule_date = data.get('schedule_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        location = data.get('location')
        
        if not course_id or not schedule_date or not start_time or not end_time:
            return jsonify({
                'code': 400,
                'message': '必要参数不能为空',
                'data': None
            }), 400
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'message': '课程不存在',
                'data': None
            }), 404
        
        schedule = CourseSchedule(
            course_id=course_id,
            coach_id=course.coach_id,
            schedule_date=datetime.strptime(schedule_date, '%Y-%m-%d').date(),
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time(),
            location=location,
            status='scheduled'
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        log_operation(
            user_id=current_user.id,
            operation='创建排期',
            module='课程管理',
            detail=f'管理员 {current_user.real_name} 创建了课程排期',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '排期创建成功',
            'data': schedule.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'创建排期失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/grades', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_all_grades():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        student_id = request.args.get('student_id', type=int)
        coach_id = request.args.get('coach_id', type=int)
        grade_type = request.args.get('grade_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Grade.query
        
        if student_id:
            query = query.filter(Grade.student_id == student_id)
        if coach_id:
            query = query.filter(Grade.coach_id == coach_id)
        if grade_type:
            query = query.filter(Grade.grade_type == grade_type)
        if start_date:
            query = query.filter(Grade.evaluate_date >= start_date)
        if end_date:
            query = query.filter(Grade.evaluate_date <= end_date)
        
        pagination = query.order_by(Grade.evaluate_date.desc(), Grade.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        grades = [g.to_dict() for g in pagination.items]
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'grades': grades,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取成绩列表失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/check-ins', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_all_check_ins():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        check_type = request.args.get('check_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = CheckIn.query
        
        if user_id:
            query = query.filter(CheckIn.user_id == user_id)
        if check_type:
            query = query.filter(CheckIn.check_type == check_type)
        if start_date:
            query = query.filter(CheckIn.check_in_time >= start_date)
        if end_date:
            query = query.filter(CheckIn.check_in_time <= f'{end_date} 23:59:59')
        
        pagination = query.order_by(CheckIn.check_in_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        records = []
        for check_in in pagination.items:
            record = check_in.to_dict()
            if check_in.student and check_in.student.user:
                record['user_name'] = check_in.student.user.real_name
            records.append(record)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'records': records,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取打卡记录失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_operation_logs():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        module = request.args.get('module')
        operation = request.args.get('operation')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = OperationLog.query
        
        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        if module:
            query = query.filter(OperationLog.module.like(f'%{module}%'))
        if operation:
            query = query.filter(OperationLog.operation.like(f'%{operation}%'))
        if start_date:
            query = query.filter(func.date(OperationLog.created_at) >= start_date)
        if end_date:
            query = query.filter(func.date(OperationLog.created_at) <= end_date)
        
        pagination = query.order_by(OperationLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = []
        for log in pagination.items:
            log_dict = log.to_dict()
            if log.user_id:
                user = User.query.get(log.user_id)
                if user:
                    log_dict['user_name'] = user.real_name
            logs.append(log_dict)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'logs': logs,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取操作日志失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_dashboard_stats():
    try:
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        total_users = User.query.count()
        total_coaches = Coach.query.count()
        total_students = Student.query.count()
        total_courses = Course.query.filter_by(status=1).count()
        
        today_check_ins = CheckIn.query.filter(
            func.date(CheckIn.check_in_time) == today
        ).count()
        
        week_check_ins = CheckIn.query.filter(
            func.date(CheckIn.check_in_time) >= week_ago
        ).count()
        
        today_grades = Grade.query.filter(Grade.evaluate_date == today).count()
        
        today_schedules = CourseSchedule.query.filter(
            CourseSchedule.schedule_date == today,
            CourseSchedule.status == 'scheduled'
        ).count()
        
        membership_stats = db.session.query(
            Student.membership_level,
            func.count(Student.id).label('count')
        ).group_by(Student.membership_level).all()
        
        membership_distribution = {
            'basic': 0,
            'premium': 0,
            'vip': 0
        }
        for m in membership_stats:
            membership_distribution[m.membership_level] = m.count
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'total_users': total_users,
                'total_coaches': total_coaches,
                'total_students': total_students,
                'total_courses': total_courses,
                'today_check_ins': today_check_ins,
                'week_check_ins': week_check_ins,
                'today_grades': today_grades,
                'today_schedules': today_schedules,
                'membership_distribution': membership_distribution
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取统计数据失败: {str(e)}',
            'data': None
        }), 500
