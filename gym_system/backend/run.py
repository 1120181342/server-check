import os
import sys
from app import create_app, db
from models import User, Role, Coach, Student

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.cli.command('init-db')
def init_db():
    db.create_all()
    print('数据库表创建完成')

@app.cli.command('seed-db')
def seed_db():
    from werkzeug.security import generate_password_hash
    from datetime import date
    
    admin_role = Role.query.filter_by(role_name='admin').first()
    if not admin_role:
        admin_role = Role(role_name='admin', description='系统管理员')
        db.session.add(admin_role)
    
    coach_role = Role.query.filter_by(role_name='coach').first()
    if not coach_role:
        coach_role = Role(role_name='coach', description='教练')
        db.session.add(coach_role)
    
    student_role = Role.query.filter_by(role_name='student').first()
    if not student_role:
        student_role = Role(role_name='student', description='学员')
        db.session.add(student_role)
    
    db.session.commit()
    
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            real_name='系统管理员',
            role_id=admin_role.id,
            phone='13800138000',
            email='admin@gym.com',
            gender='male',
            status=1
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    sample_coach = User.query.filter_by(username='coach1').first()
    if not sample_coach:
        sample_coach = User(
            username='coach1',
            real_name='张教练',
            role_id=coach_role.id,
            phone='13800138001',
            email='coach1@gym.com',
            gender='male',
            status=1
        )
        sample_coach.set_password('coach123')
        db.session.add(sample_coach)
        db.session.flush()
        
        coach = Coach(
            user_id=sample_coach.id,
            speciality='健身指导、力量训练',
            experience_years=5,
            certification='国家一级健身指导员',
            bio='专业健身教练，从业5年，擅长力量训练和塑形指导。'
        )
        db.session.add(coach)
    
    sample_student = User.query.filter_by(username='student1').first()
    if not sample_student:
        sample_student = User(
            username='student1',
            real_name='李学员',
            role_id=student_role.id,
            phone='13800138002',
            email='student1@gym.com',
            gender='male',
            status=1
        )
        sample_student.set_password('student123')
        db.session.add(sample_student)
        db.session.flush()
        
        coach_obj = Coach.query.first()
        student = Student(
            user_id=sample_student.id,
            coach_id=coach_obj.id if coach_obj else None,
            membership_level='premium',
            join_date=date.today()
        )
        db.session.add(student)
    
    db.session.commit()
    print('示例数据初始化完成')
    print('默认账号:')
    print('  管理员: admin / admin123')
    print('  教练: coach1 / coach123')
    print('  学员: student1 / student123')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Coach': Coach,
        'Student': Student
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
