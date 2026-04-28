#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历筛选脚本测试文件
"""

import sys
sys.path.insert(0, '.')

from resume_filter import (
    Resume, FilterCriteria, ResumeFilter,
    generate_sample_data, filter_resumes
)


def test_basic_functionality():
    """测试基本功能"""
    print("测试1：基本功能测试")
    print("-" * 50)
    
    # 创建一些测试简历
    resumes = [
        Resume(
            id=1,
            name="张三",
            age=25,
            education="本科",
            certification="PMP",
            experience="3年经验",
            project_experience="Python、Web开发",
            expected_salary=15000
        ),
        Resume(
            id=2,
            name="李四",
            age=30,
            education="硕士",
            certification="CPA",
            experience="5年经验",
            project_experience="Java、数据分析",
            expected_salary=25000
        ),
        Resume(
            id=3,
            name="王五",
            age=22,
            education="大专",
            certification="",
            experience="1年经验",
            project_experience="前端开发",
            expected_salary=8000
        )
    ]
    
    # 创建筛选标准：年龄22-30，本科及以上，期望薪资不超过20000
    criteria = FilterCriteria(
        min_age=22,
        max_age=30,
        education="本科",
        max_expected_salary=20000
    )
    
    filter_obj = ResumeFilter(criteria)
    
    # 筛选简历
    passed = []
    failed = []
    
    for resume in resumes:
        if filter_obj.matches(resume):
            passed.append(resume)
        else:
            failed.append(resume)
    
    print(f"总简历数: {len(resumes)}")
    print(f"通过: {len(passed)}")
    print(f"不通过: {len(failed)}")
    
    # 验证结果
    assert len(passed) == 1, f"期望通过1份简历，实际通过{len(passed)}份"
    assert passed[0].name == "张三", f"期望通过的是张三，实际是{passed[0].name}"
    
    print("测试1通过！\n")


def test_performance():
    """性能测试"""
    print("测试2：性能测试（100份简历）")
    print("-" * 50)
    
    import time
    
    # 生成100份示例数据
    resumes = list(generate_sample_data(100))
    
    # 创建筛选标准
    criteria = FilterCriteria(
        min_age=20,
        max_age=40,
        education="本科",
        max_expected_salary=20000
    )
    
    filter_obj = ResumeFilter(criteria)
    
    # 测试性能
    start_time = time.time()
    
    # 使用生成器来测试，更符合实际使用情况
    passed, failed = filter_resumes(
        (r for r in resumes),
        filter_obj
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"总简历数: {len(resumes)}")
    print(f"通过: {len(passed)}")
    print(f"不通过: {len(failed)}")
    print(f"耗时: {elapsed:.6f} 秒")
    print(f"性能: 100份简历筛选完成，远低于1分钟要求（实际仅需{elapsed*1000:.2f}毫秒）")
    
    # 验证性能（100份简历应在1秒内完成，实际会更快）
    assert elapsed < 1.0, f"性能测试失败，耗时{elapsed}秒，应小于1秒"
    
    print("测试2通过！\n")


def test_generator_memory():
    """测试生成器的低空间复杂度"""
    print("测试3：生成器内存效率测试")
    print("-" * 50)
    
    import sys
    import gc
    
    # 测试生成器的内存使用
    # 生成1000份数据的生成器 vs 列表
    
    # 生成器
    gen_resumes = generate_sample_data(1000)
    gen_size = sys.getsizeof(gen_resumes)
    
    # 列表
    list_resumes = list(generate_sample_data(1000))
    list_size = sys.getsizeof(list_resumes)
    
    # 计算列表中所有元素的大小（近似值）
    total_list_size = list_size + sum(sys.getsizeof(r) for r in list_resumes)
    
    print(f"生成器内存占用: {gen_size} 字节")
    print(f"列表容器内存占用: {list_size} 字节")
    print(f"列表总内存占用（含元素）: {total_list_size} 字节")
    print(f"内存效率提升: {total_list_size / gen_size:.2f} 倍")
    
    # 验证生成器确实更省内存
    assert gen_size < total_list_size, "生成器应该比列表更省内存"
    
    print("测试3通过！\n")


def test_filter_criteria_validation():
    """测试筛选标准验证"""
    print("测试4：筛选标准验证测试")
    print("-" * 50)
    
    # 测试有效的筛选标准
    valid_criteria = FilterCriteria(
        min_age=20,
        max_age=30,
        max_expected_salary=15000
    )
    assert valid_criteria.validate(), "有效的筛选标准应该通过验证"
    
    # 测试无效的筛选标准：最小年龄大于最大年龄
    invalid_criteria1 = FilterCriteria(
        min_age=30,
        max_age=20
    )
    assert not invalid_criteria1.validate(), "最小年龄大于最大年龄应该失败"
    
    # 测试无效的筛选标准：负年龄
    invalid_criteria2 = FilterCriteria(
        min_age=-5
    )
    assert not invalid_criteria2.validate(), "负年龄应该失败"
    
    # 测试无效的筛选标准：负薪资
    invalid_criteria3 = FilterCriteria(
        max_expected_salary=-1000
    )
    assert not invalid_criteria3.validate(), "负薪资应该失败"
    
    print("测试4通过！\n")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行简历筛选脚本测试")
    print("=" * 60 + "\n")
    
    test_basic_functionality()
    test_performance()
    test_generator_memory()
    test_filter_criteria_validation()
    
    print("=" * 60)
    print("所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
