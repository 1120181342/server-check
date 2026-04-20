from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import User, Coach, Student, Course, CourseSchedule, StudentCourse, CheckIn, Grade
from app import db
from routes import role_required, log_operation, get_current_user
from datetime import datetime, date
from sqlalchemy import and_, or_

coach_bp = Blueprint('coach', __name__)

@coach_bp.route('/profile', methods=['GET'])
@jwt_required()
@role_required('coach')
def get_profile():
    try:
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        result = user.to_dict()
        result['coach_info'] = coach.to_dict()
        
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

@coach_bp.route('/profile', methods=['PUT'])
@jwt_required()
@role_required('coach')
def update_profile():
    try:
        data = request.get_json()
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
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
        
        if 'speciality' in data:
            coach.speciality = data['speciality']
        if 'experience_years' in data:
            coach.experience_years = data['experience_years']
        if 'certification' in data:
            coach.certification = data['certification']
        if 'bio' in data:
            coach.bio = data['bio']
        
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='更新个人信息',
            module='教练管理',
            detail=f'教练 {user.real_name} 更新了个人信息',
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

@coach_bp.route('/students', methods=['GET'])
@jwt_required()
@role_required('coach')
def get_students():
    try:
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        membership_level = request.args.get('membership_level', '')
        
        query = Student.query.filter_by(coach_id=coach.id)
        
        if keyword:
            query = query.join(User, Student.user_id == User.id).filter(
                or_(
                    User.real_name.like(f'%{keyword}%'),
                    User.username.like(f'%{keyword}%'),
                    User.phone.like(f'%{keyword}%')
                )
            )
        
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

@coach_bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required()
@role_required('coach')
def get_student_detail(student_id):
    try:
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        student = Student.query.filter_by(id=student_id, coach_id=coach.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员不存在',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': student.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取学员详情失败: {str(e)}',
            'data': None
        }), 500

@coach_bp.route('/courses', methods=['GET'])
@jwt_required()
@role_required('coach')
def get_courses():
    try:
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = Course.query.filter_by(coach_id=coach.id)
        
        if status is not None:
            query = query.filter(Course.status == int(status))
        
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

@coach_bp.route('/schedules', methods=['GET'])
@jwt_required()
@role_required('coach')
def get_schedules():
    try:
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        schedule_date = request.args.get('schedule_date')
        status = request.args.get('status')
        
        query = CourseSchedule.query.filter_by(coach_id=coach.id)
        
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

@coach_bp.route('/schedules/<int:schedule_id>/students', methods=['GET'])
@jwt_required()
@role_required('coach')
def get_schedule_students(schedule_id):
    try:
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        schedule = CourseSchedule.query.filter_by(id=schedule_id, coach_id=coach.id).first()
        
        if not schedule:
            return jsonify({
                'code': 404,
                'message': '课程排期不存在',
                'data': None
            }), 404
        
        student_courses = StudentCourse.query.filter_by(schedule_id=schedule_id).all()
        
        students = []
        for sc in student_courses:
            student = sc.student
            if student and student.user:
                students.append({
                    'id': student.id,
                    'user_id': student.user_id,
                    'real_name': student.user.real_name,
                    'username': student.user.username,
                    'phone': student.user.phone,
                    'enroll_status': sc.status,
                    'enroll_time': sc.enroll_time.strftime('%Y-%m-%d %H:%M:%S') if sc.enroll_time else None
                })
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'schedule': schedule.to_dict(),
                'students': students,
                'total': len(students)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取排期学员失败: {str(e)}',
            'data': None
        }), 500

@coach_bp.route('/check-in', methods=['POST'])
@jwt_required()
@role_required('coach')
def coach_check_in():
    try:
        data = request.get_json()
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        check_type = data.get('check_type', 'class')
        schedule_id = data.get('schedule_id')
        remarks = data.get('remarks')
        
        check_in = CheckIn(
            user_id=user.id,
            check_type=check_type,
            schedule_id=schedule_id,
            status='success',
            remarks=remarks
        )
        
        db.session.add(check_in)
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='上课打卡',
            module='打卡管理',
            detail=f'教练 {user.real_name} 上课打卡',
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

@coach_bp.route('/check-in/records', methods=['GET'])
@jwt_required()
@role_required('coach')
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

@coach_bp.route('/grades', methods=['POST'])
@jwt_required()
@role_required('coach')
def add_grade():
    try:
        data = request.get_json()
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        student_id = data.get('student_id')
        schedule_id = data.get('schedule_id')
        grade_type = data.get('grade_type', 'overall')
        score = data.get('score')
        max_score = data.get('max_score', 100.00)
        evaluation = data.get('evaluation')
        evaluate_date = data.get('evaluate_date', date.today().isoformat())
        
        if not student_id or score is None:
            return jsonify({
                'code': 400,
                'message': '学员ID和分数不能为空',
                'data': None
            }), 400
        
        student = Student.query.filter_by(id=student_id, coach_id=coach.id).first()
        
        if not student:
            return jsonify({
                'code': 404,
                'message': '学员不存在或不属于您',
                'data': None
            }), 404
        
        grade = Grade(
            student_id=student_id,
            coach_id=coach.id,
            schedule_id=schedule_id,
            grade_type=grade_type,
            score=score,
            max_score=max_score,
            evaluation=evaluation,
            evaluate_date=datetime.strptime(evaluate_date, '%Y-%m-%d').date()
        )
        
        db.session.add(grade)
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='登记成绩',
            module='成绩管理',
            detail=f'教练 {user.real_name} 为学员 {student.user.real_name} 登记了 {grade_type} 成绩: {score}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '成绩登记成功',
            'data': grade.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'成绩登记失败: {str(e)}',
            'data': None
        }), 500

@coach_bp.route('/grades', methods=['GET'])
@jwt_required()
@role_required('coach')
def get_grades():
    try:
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        student_id = request.args.get('student_id', type=int)
        grade_type = request.args.get('grade_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Grade.query.filter_by(coach_id=coach.id)
        
        if student_id:
            query = query.filter(Grade.student_id == student_id)
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

@coach_bp.route('/grades/<int:grade_id>', methods=['PUT'])
@jwt_required()
@role_required('coach')
def update_grade(grade_id):
    try:
        data = request.get_json()
        user = get_current_user()
        coach = Coach.query.filter_by(user_id=user.id).first()
        
        if not coach:
            return jsonify({
                'code': 404,
                'message': '教练信息不存在',
                'data': None
            }), 404
        
        grade = Grade.query.filter_by(id=grade_id, coach_id=coach.id).first()
        
        if not grade:
            return jsonify({
                'code': 404,
                'message': '成绩记录不存在',
                'data': None
            }), 404
        
        if 'score' in data:
            grade.score = data['score']
        if 'max_score' in data:
            grade.max_score = data['max_score']
        if 'grade_type' in data:
            grade.grade_type = data['grade_type']
        if 'evaluation' in data:
            grade.evaluation = data['evaluation']
        if 'evaluate_date' in data:
            grade.evaluate_date = datetime.strptime(data['evaluate_date'], '%Y-%m-%d').date()
        
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='更新成绩',
            module='成绩管理',
            detail=f'教练 {user.real_name} 更新了成绩记录',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '成绩更新成功',
            'data': grade.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'成绩更新失败: {str(e)}',
            'data': None
        }), 500
