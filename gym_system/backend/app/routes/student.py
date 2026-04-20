from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import User, Student, Coach, Course, CourseSchedule, StudentCourse, CheckIn, Grade
from app import db
from routes import role_required, log_operation, get_current_user
from datetime import datetime, date
from sqlalchemy import and_, or_

student_bp = Blueprint('student', __name__)

@student_bp.route('/profile', methods=['GET'])
@jwt_required()
@role_required('student')
def get_profile():
    try:
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        result = user.to_dict()
        result['student_info'] = student.to_dict()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取个人信息失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/profile', methods=['PUT'])
@jwt_required()
@role_required('student')
def update_profile():
    try:
        data = request.get_json()
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        if 'phone' in data:
            user.phone = data['phone']
        if 'email' in data:
            user.email = data['email']
        if 'gender' in data:
            user.gender = data['gender']
        if 'real_name' in data:
            user.real_name = data['real_name']
        
        if 'birth_date' in data:
            if data['birth_date']:
                student.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            else:
                student.birth_date = None
        if 'height' in data:
            student.height = data['height']
        if 'weight' in data:
            student.weight = data['weight']
        
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='更新个人信息',
            module='学员管理',
            detail=f'学员 {user.real_name} 更新了个人信息',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新个人信息失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/coach', methods=['GET'])
@jwt_required()
@role_required('student')
def get_coach():
    try:
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        if not student.coach:
            return jsonify({
                'code': 200,
                'message': '暂未分配教练',
                'data': None
            })
        
        coach_info = student.coach.to_dict()
        if student.coach.user:
            coach_info['user_info'] = student.coach.user.to_dict()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': coach_info
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取教练信息失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/courses', methods=['GET'])
@jwt_required()
@role_required('student')
def get_my_courses():
    try:
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = StudentCourse.query.filter_by(student_id=student.id)
        
        if status:
            query = query.filter(StudentCourse.status == status)
        
        pagination = query.order_by(StudentCourse.enroll_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        courses = []
        for sc in pagination.items:
            if sc.schedule:
                course_info = sc.schedule.to_dict()
                course_info['enroll_status'] = sc.status
                course_info['enroll_time'] = sc.enroll_time.strftime('%Y-%m-%d %H:%M:%S') if sc.enroll_time else None
                courses.append(course_info)
        
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
            'message': f'获取我的课程失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/schedules/available', methods=['GET'])
@jwt_required()
@role_required('student')
def get_available_schedules():
    try:
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        schedule_date = request.args.get('schedule_date')
        coach_id = request.args.get('coach_id', type=int)
        
        today = date.today()
        query = CourseSchedule.query.filter(
            CourseSchedule.schedule_date >= today,
            CourseSchedule.status == 'scheduled',
            CourseSchedule.current_students < Course.max_students
        ).join(Course, CourseSchedule.course_id == Course.id)
        
        if student.coach_id:
            query = query.filter(
                or_(
                    CourseSchedule.coach_id == student.coach_id,
                    Course.course_type == 'group'
                )
            )
        
        if schedule_date:
            query = query.filter(CourseSchedule.schedule_date == schedule_date)
        if coach_id:
            query = query.filter(CourseSchedule.coach_id == coach_id)
        
        pagination = query.order_by(CourseSchedule.schedule_date.asc(), 
                                     CourseSchedule.start_time.asc()).paginate(
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
            'message': f'获取可用课程失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/courses/enroll', methods=['POST'])
@jwt_required()
@role_required('student')
def enroll_course():
    try:
        data = request.get_json()
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        schedule_id = data.get('schedule_id')
        
        if not schedule_id:
            return jsonify({
                'code': 400,
                'message': '请选择要报名的课程',
                'data': None
            }), 400
        
        existing = StudentCourse.query.filter_by(
            student_id=student.id,
            schedule_id=schedule_id
        ).first()
        
        if existing:
            return jsonify({
                'code': 400,
                'message': '您已报名该课程',
                'data': None
            }), 400
        
        schedule = CourseSchedule.query.filter_by(id=schedule_id, status='scheduled').first()
        
        if not schedule:
            return jsonify({
                'code': 404,
                'message': '课程排期不存在或已结束',
                'data': None
            }), 404
        
        if schedule.current_students >= schedule.course.max_students:
            return jsonify({
                'code': 400,
                'message': '该课程已报满',
                'data': None
            }), 400
        
        student_course = StudentCourse(
            student_id=student.id,
            schedule_id=schedule_id,
            status='enrolled'
        )
        
        schedule.current_students += 1
        
        db.session.add(student_course)
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='报名课程',
            module='课程管理',
            detail=f'学员 {user.real_name} 报名了课程 {schedule.course.course_name}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '报名成功',
            'data': student_course.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'报名失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/courses/cancel', methods=['POST'])
@jwt_required()
@role_required('student')
def cancel_course():
    try:
        data = request.get_json()
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        schedule_id = data.get('schedule_id')
        
        if not schedule_id:
            return jsonify({
                'code': 400,
                'message': '请选择要取消的课程',
                'data': None
            }), 400
        
        student_course = StudentCourse.query.filter_by(
            student_id=student.id,
            schedule_id=schedule_id,
            status='enrolled'
        ).first()
        
        if not student_course:
            return jsonify({
                'code': 404,
                'message': '未找到该课程报名记录',
                'data': None
            }), 404
        
        schedule = CourseSchedule.query.filter_by(id=schedule_id).first()
        
        if schedule and schedule.status in ['ongoing', 'completed']:
            return jsonify({
                'code': 400,
                'message': '课程已开始或已结束，无法取消',
                'data': None
            }), 400
        
        student_course.status = 'cancelled'
        
        if schedule:
            schedule.current_students = max(0, schedule.current_students - 1)
        
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='取消报名',
            module='课程管理',
            detail=f'学员 {user.real_name} 取消了课程报名',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '取消成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'取消失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/check-in', methods=['POST'])
@jwt_required()
@role_required('student')
def student_check_in():
    try:
        data = request.get_json()
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        check_type = data.get('check_type', 'class')
        schedule_id = data.get('schedule_id')
        remarks = data.get('remarks')
        
        now = datetime.now()
        status = 'success'
        
        if schedule_id and check_type == 'class':
            schedule = CourseSchedule.query.filter_by(id=schedule_id).first()
            if schedule:
                schedule_datetime = datetime.combine(schedule.schedule_date, schedule.start_time)
                if now > schedule_datetime:
                    status = 'late'
                
                student_course = StudentCourse.query.filter_by(
                    student_id=student.id,
                    schedule_id=schedule_id
                ).first()
                
                if student_course:
                    student_course.status = 'attended'
        
        check_in = CheckIn(
            user_id=user.id,
            check_type=check_type,
            schedule_id=schedule_id,
            status=status,
            remarks=remarks
        )
        
        db.session.add(check_in)
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='上课打卡',
            module='打卡管理',
            detail=f'学员 {user.real_name} 上课打卡',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '打卡成功',
            'data': check_in.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'打卡失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/check-in/records', methods=['GET'])
@jwt_required()
@role_required('student')
def get_check_in_records():
    try:
        user = get_current_user()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        check_type = request.args.get('check_type')
        
        query = CheckIn.query.filter_by(user_id=user.id)
        
        if start_date:
            query = query.filter(CheckIn.check_in_time >= start_date)
        if end_date:
            query = query.filter(CheckIn.check_in_time <= f'{end_date} 23:59:59')
        if check_type:
            query = query.filter(CheckIn.check_type == check_type)
        
        pagination = query.order_by(CheckIn.check_in_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        records = [r.to_dict() for r in pagination.items]
        
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

@student_bp.route('/grades', methods=['GET'])
@jwt_required()
@role_required('student')
def get_my_grades():
    try:
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        grade_type = request.args.get('grade_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Grade.query.filter_by(student_id=student.id)
        
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
            'message': f'获取成绩失败: {str(e)}',
            'data': None
        }), 500

@student_bp.route('/grades/stats', methods=['GET'])
@jwt_required()
@role_required('student')
def get_grades_stats():
    try:
        user = get_current_user()
        student = Student.query.filter_by(user_id=user.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员信息不存在',
                'data': None
            }), 404
        
        grades = Grade.query.filter_by(student_id=student.id).all()
        
        total_count = len(grades)
        total_score = sum(float(g.score) for g in grades)
        avg_score = total_score / total_count if total_count > 0 else 0
        
        type_stats = {}
        for g in grades:
            if g.grade_type not in type_stats:
                type_stats[g.grade_type] = {'count': 0, 'total': 0, 'avg': 0}
            type_stats[g.grade_type]['count'] += 1
            type_stats[g.grade_type]['total'] += float(g.score)
        
        for k, v in type_stats.items():
            v['avg'] = v['total'] / v['count'] if v['count'] > 0 else 0
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'total_count': total_count,
                'avg_score': round(avg_score, 2),
                'type_stats': type_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取成绩统计失败: {str(e)}',
            'data': None
        }), 500
