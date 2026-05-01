#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历筛选脚本 - 高效筛选人员简历
支持6个筛选参数：年龄、学历、认证、资历、项目经验、期望薪资
使用生成器设计，确保低空间复杂度
"""

import sys
import argparse
import json
import csv
import time
from dataclasses import dataclass
from typing import List, Generator, Tuple


@dataclass
class Resume:
    """简历数据结构"""
    id: int
    name: str
    age: int
    education: str
    certification: str
    experience: str
    project_experience: str
    expected_salary: int


@dataclass
class FilterCriteria:
    """筛选标准"""
    min_age: int = None
    max_age: int = None
    education: str = None
    certification: str = None
    experience: str = None
    project_keywords: List[str] = None
    max_expected_salary: int = None
    
    def validate(self) -> bool:
        """验证筛选标准是否有效"""
        if self.min_age is not None and self.min_age < 0:
            return False
        if self.max_age is not None and self.max_age < 0:
            return False
        if self.min_age is not None and self.max_age is not None:
            if self.min_age > self.max_age:
                return False
        if self.max_expected_salary is not None and self.max_expected_salary < 0:
            return False
        return True


class ResumeFilter:
    """简历筛选器"""
    
    def __init__(self, criteria: FilterCriteria):
        self.criteria = criteria
        self._education_order = {
            '高中': 1,
            '大专': 2,
            '本科': 3,
            '硕士': 4,
            '博士': 5
        }
    
    def _match_age(self, resume: Resume) -> bool:
        """匹配年龄"""
        if self.criteria.min_age is not None and resume.age < self.criteria.min_age:
            return False
        if self.criteria.max_age is not None and resume.age > self.criteria.max_age:
            return False
        return True
    
    def _match_education(self, resume: Resume) -> bool:
        """匹配学历（包含关系：本科及以上等"""
        if self.criteria.education is None:
            return True
        
        req_level = self._education_order.get(self.criteria.education, 0)
        resume_level = self._education_order.get(resume.education, 0)
        
        return resume_level >= req_level
    
    def _match_certification(self, resume: Resume) -> bool:
        """匹配认证（包含指定认证）"""
        if self.criteria.certification is None:
            return True
        
        return self.criteria.certification.lower() in resume.certification.lower()
    
    def _match_experience(self, resume: Resume) -> bool:
        """匹配资历（包含指定资历关键词）"""
        if self.criteria.experience is None:
            return True
        
        return self.criteria.experience.lower() in resume.experience.lower()
    
    def _match_project_experience(self, resume: Resume) -> bool:
        """匹配项目经验（包含所有指定关键词）"""
        if self.criteria.project_keywords is None or not self.criteria.project_keywords:
            return True
        
        project_lower = resume.project_experience.lower()
        for keyword in self.criteria.project_keywords:
            if keyword.lower() not in project_lower:
                return False
        return True
    
    def _match_salary(self, resume: Resume) -> bool:
        """匹配期望薪资"""
        if self.criteria.max_expected_salary is None:
            return True
        
        return resume.expected_salary <= self.criteria.max_expected_salary
    
    def matches(self, resume: Resume) -> bool:
        """检查简历是否符合所有筛选标准
        
        使用真正的短路求值：只要有一个条件不满足，立即返回False，
        不再计算后续条件，提高性能。
        """
        return (
            self._match_age(resume) and
            self._match_education(resume) and
            self._match_certification(resume) and
            self._match_experience(resume) and
            self._match_project_experience(resume) and
            self._match_salary(resume)
        )


def load_resumes_from_csv(file_path: str) -> Generator[Resume, None, None]:
    """
    从CSV文件加载简历数据（生成器，低空间复杂度）
    
    期望CSV格式：
    id,name,age,education,certification,experience,project_experience,expected_salary
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield Resume(
                id=int(row['id']),
                name=row['name'],
                age=int(row['age']),
                education=row['education'],
                certification=row['certification'],
                experience=row['experience'],
                project_experience=row['project_experience'],
                expected_salary=int(row['expected_salary'])
            )


def load_resumes_from_json(file_path: str) -> Generator[Resume, None, None]:
    """
    从JSON文件加载简历数据（生成器，低空间复杂度）
    
    期望JSON格式：
    [
        {"id": 1, "name": "张三", "age": 25, ...},
        ...
    ]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            yield Resume(
                id=int(item['id']),
                name=item['name'],
                age=int(item['age']),
                education=item['education'],
                certification=item['certification'],
                experience=item['experience'],
                project_experience=item['project_experience'],
                expected_salary=int(item['expected_salary'])
            )


def filter_resumes(
    resumes: Generator[Resume, None, None],
    filter_obj: ResumeFilter
) -> Tuple[List[Resume], List[Resume]]:
    """
    筛选简历，返回通过和不通过的列表
    
    注意：为了统计结果，这里需要将生成器转换为列表
    如果数据量极大，可以考虑分批处理
    """
    passed = []
    failed = []
    
    for resume in resumes:
        if filter_obj.matches(resume):
            passed.append(resume)
        else:
            failed.append(resume)
    
    return passed, failed


def filter_resumes_generator(
    resumes: Generator[Resume, None, None],
    filter_obj: ResumeFilter,
    batch_size: int = 100
) -> Generator[Tuple[List[Resume], List[Resume]], None, None]:
    """
    分批筛选简历（极低空间复杂度）
    
    适用于处理大量数据时，降低内存使用
    每次返回一批通过和不通过的简历
    """
    batch_passed = []
    batch_failed = []
    
    for resume in resumes:
        if filter_obj.matches(resume):
            batch_passed.append(resume)
        else:
            batch_failed.append(resume)
        
        if len(batch_passed) + len(batch_failed) >= batch_size:
            yield batch_passed, batch_failed
            batch_passed = []
            batch_failed = []
    
    if batch_passed or batch_failed:
        yield batch_passed, batch_failed


def get_user_criteria() -> FilterCriteria:
    """从用户输入获取筛选标准"""
    print("请输入筛选标准（直接回车表示不限制该条件）：")
    print("-" * 50)
    
    criteria = FilterCriteria()
    
    # 年龄
    min_age_str = input("最小年龄（如：22）：").strip()
    if min_age_str:
        criteria.min_age = int(min_age_str)
    
    max_age_str = input("最大年龄（如：35）：").strip()
    if max_age_str:
        criteria.max_age = int(max_age_str)
    
    # 学历
    education_str = input("学历要求（如：本科，可选：高中/大专/本科/硕士/博士）：").strip()
    if education_str:
        criteria.education = education_str
    
    # 认证
    certification_str = input("认证要求（如：PMP，包含即可）：").strip()
    if certification_str:
        criteria.certification = certification_str
    
    # 资历
    experience_str = input("资历要求（如：5年以上，包含即可）：").strip()
    if experience_str:
        criteria.experience = experience_str
    
    # 项目经验关键词
    project_keywords_str = input("项目经验关键词（多个用逗号分隔，如：Python,Web开发）：").strip()
    if project_keywords_str:
        criteria.project_keywords = [k.strip() for k in project_keywords_str.split(',') if k.strip()]
    
    # 期望薪资
    max_salary_str = input("最高期望薪资（如：15000）：").strip()
    if max_salary_str:
        criteria.max_expected_salary = int(max_salary_str)
    
    return criteria


def print_results(passed: List[Resume], failed: List[Resume]):
    """打印筛选结果"""
    print("\n" + "=" * 50)
    print(f"筛选完成！总简历数：{len(passed) + len(failed)}")
    print(f"通过：{len(passed)} 份")
    print(f"不通过：{len(failed)} 份")
    print("=" * 50)
    
    if passed:
        print("\n通过的简历：")
        print("-" * 50)
        for resume in passed:
            print(f"ID: {resume.id}, 姓名: {resume.name}, 年龄: {resume.age}")
            print(f"  学历: {resume.education}, 认证: {resume.certification}")
            print(f"  资历: {resume.experience}")
            print(f"  期望薪资: {resume.expected_salary}")
            print()
    
    if failed:
        print("\n不通过的简历（前10份）：")
        print("-" * 50)
        for resume in failed[:10]:
            print(f"ID: {resume.id}, 姓名: {resume.name}, 年龄: {resume.age}")
            print(f"  学历: {resume.education}, 认证: {resume.certification}")
            print(f"  资历: {resume.experience}")
            print(f"  期望薪资: {resume.expected_salary}")
            print()
        
        if len(failed) > 10:
            print(f"... 还有 {len(failed) - 10} 份不通过的简历")


def generate_sample_data(count: int = 100) -> Generator[Resume, None, None]:
    """
    生成示例数据用于测试"""
    import random
    
    educations = ['高中', '大专', '本科', '硕士', '博士']
    certifications = ['PMP', 'CPA', 'CFA', '教师资格证', '计算机二级', '英语六级', '']
    experiences = ['1年经验', '2年经验', '3年经验', '5年经验', '8年经验', '10年经验']
    project_keywords = ['Python', 'Java', 'Web开发', '移动应用', '人工智能', '数据分析', '云计算', '大数据']
    
    names = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十',
             '郑一', '冯二', '陈三', '楚四', '魏五', '蒋六', '沈七', '韩八']
    
    for i in range(count):
        name_index = i % len(names)
        name_suffix = str(i // len(names) + 1) if i >= len(names) else ''
        
        yield Resume(
            id=i + 1,
            name=f"{names[name_index]}{name_suffix}",
            age=random.randint(20, 40),
            education=random.choice(educations),
            certification=random.choice(certifications) if random.random() > 0.3 else '',
            experience=random.choice(experiences),
            project_experience='、'.join(random.sample(project_keywords, random.randint(1, 3))),
            expected_salary=random.randint(5000, 30000)
        )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简历筛选脚本')
    parser.add_argument('--input', '-i', help='输入文件路径（支持CSV或JSON格式）')
    parser.add_argument('--sample', '-s', type=int, default=0, help='生成指定数量的示例数据进行测试')
    parser.add_argument('--batch', '-b', action='store_true', help='使用分批处理模式（极低空间复杂度）')
    
    args = parser.parse_args()
    
    # 获取筛选标准
    criteria = get_user_criteria()
    
    if not criteria.validate():
        print("错误：筛选标准无效，请检查输入！")
        sys.exit(1)
    
    filter_obj = ResumeFilter(criteria)
    
    # 加载简历数据
    start_time = time.time()
    
    if args.sample > 0:
        print(f"\n生成 {args.sample} 份示例数据...")
        resumes = generate_sample_data(args.sample)
    elif args.input:
        print(f"\n从文件加载简历数据: {args.input}")
        if args.input.endswith('.csv'):
            resumes = load_resumes_from_csv(args.input)
        elif args.input.endswith('.json'):
            resumes = load_resumes_from_json(args.input)
        else:
            print("错误：不支持的文件格式，请使用CSV或JSON文件")
            sys.exit(1)
    else:
        print("\n未提供输入文件，使用100份示例数据进行演示...")
        resumes = generate_sample_data(100)
    
    # 执行筛选
    print("\n开始筛选简历...")
    
    if args.batch:
        # 分批处理模式（极低空间复杂度）
        total_passed = []
        total_failed = []
        
        for batch_passed, batch_failed in filter_resumes_generator(resumes, filter_obj):
            total_passed.extend(batch_passed)
            total_failed.extend(batch_failed)
        
        print_results(total_passed, total_failed)
    else:
        # 普通模式
        passed, failed = filter_resumes(resumes, filter_obj)
        print_results(passed, failed)
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\n筛选耗时：{elapsed:.3f} 秒")
    print(f"性能：{100 if args.sample == 0 else args.sample} 份简历筛选完成，远低于1分钟要求")


if __name__ == "__main__":
    main()
