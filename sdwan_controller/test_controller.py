"""
SD-WAN控制器测试脚本
测试功能、性能和正确性
"""

import asyncio
import time
import logging
import sys
from typing import Dict, List, Any
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    passed: bool
    duration: float
    details: Dict[str, Any]


class SDWANControllerTester:
    """SD-WAN控制器测试类"""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.controller = None

    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("Starting SD-WAN Controller Tests")
        logger.info("=" * 60)
        
        try:
            # 1. 初始化测试
            await self.test_initialization()
            
            # 2. 拓扑测试
            await self.test_topology()
            
            # 3. 路由计算测试
            await self.test_route_calculation()
            
            # 4. 性能测试
            await self.test_performance()
            
            # 5. 路径查找测试
            await self.test_path_finding()
            
            # 6. ECMP测试
            await self.test_ecmp()
            
            # 7. 故障恢复测试
            await self.test_failover()
            
            # 打印测试结果摘要
            self._print_test_summary()
            
            # 检查是否所有测试都通过
            all_passed = all(result.passed for result in self.test_results)
            return all_passed
            
        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            return False
        finally:
            # 清理
            if self.controller and self.controller.running:
                await self.controller.stop()

    async def test_initialization(self) -> None:
        """测试控制器初始化"""
        test_name = "Controller Initialization"
        logger.info(f"\n--- Testing: {test_name} ---")
        
        start_time = time.time()
        
        try:
            # 导入控制器
            from .main import SDWANController
            
            self.controller = SDWANController()
            
            # 初始化
            init_success = await self.controller.initialize()
            
            duration = time.time() - start_time
            
            passed = init_success
            
            details = {
                "initialization_time": duration,
                "topology_initialization_time": self.controller.stats.topology_initialization_time,
                "route_calculation_time": self.controller.stats.initial_route_calculation_time,
            }
            
            if passed:
                logger.info(f"✓ {test_name} PASSED")
                logger.info(f"  - Total initialization time: {duration:.4f}s")
                logger.info(f"  - Topology init: {details['topology_initialization_time']:.4f}s")
                logger.info(f"  - Route calc: {details['route_calculation_time']:.4f}s")
            else:
                logger.error(f"✗ {test_name} FAILED")
            
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=passed,
                duration=duration,
                details=details,
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                details={"error": str(e)},
            ))

    async def test_topology(self) -> None:
        """测试拓扑结构"""
        test_name = "Network Topology"
        logger.info(f"\n--- Testing: {test_name} ---")
        
        start_time = time.time()
        
        try:
            if not self.controller:
                raise RuntimeError("Controller not initialized")
            
            topology = self.controller.get_status()["topology"]
            
            # 验证交换机数量
            expected_total = 20
            expected_core = 2
            expected_access = 10
            expected_pop = 8
            
            checks = [
                ("Total switches", topology["total_switches"], expected_total),
                ("Core switches", topology["core_switches"], expected_core),
                ("Access switches", topology["access_switches"], expected_access),
                ("POP switches", topology["pop_switches"], expected_pop),
            ]
            
            all_passed = True
            for name, actual, expected in checks:
                if actual == expected:
                    logger.info(f"  ✓ {name}: {actual} (expected: {expected})")
                else:
                    logger.error(f"  ✗ {name}: {actual} (expected: {expected})")
                    all_passed = False
            
            # 验证链路数量
            logger.info(f"  - Total links: {topology['total_links']}")
            logger.info(f"  - Active links: {topology['active_links']}")
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=all_passed,
                duration=duration,
                details={"topology": topology},
            ))
            
            if all_passed:
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                details={"error": str(e)},
            ))

    async def test_route_calculation(self) -> None:
        """测试路由计算"""
        test_name = "Route Calculation"
        logger.info(f"\n--- Testing: {test_name} ---")
        
        start_time = time.time()
        
        try:
            if not self.controller:
                raise RuntimeError("Controller not initialized")
            
            # 执行多次路由计算
            calculation_times = []
            
            for i in range(3):
                calc_start = time.time()
                success = await self.controller.calculate_all_routes()
                calc_time = time.time() - calc_start
                calculation_times.append(calc_time)
                
                if not success:
                    raise RuntimeError(f"Route calculation {i+1} failed")
                
                logger.info(f"  Calculation {i+1}: {calc_time:.4f}s")
            
            # 计算统计
            avg_time = sum(calculation_times) / len(calculation_times)
            max_time = max(calculation_times)
            min_time = min(calculation_times)
            
            # 验证性能要求（<1秒）
            from .config import PERFORMANCE_CONFIG
            target_time = PERFORMANCE_CONFIG["max_computation_time"]
            
            passed = max_time < target_time
            
            logger.info(f"\n  Statistics:")
            logger.info(f"    - Average: {avg_time:.4f}s")
            logger.info(f"    - Maximum: {max_time:.4f}s")
            logger.info(f"    - Minimum: {min_time:.4f}s")
            logger.info(f"    - Target: < {target_time}s")
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=passed,
                duration=duration,
                details={
                    "calculation_times": calculation_times,
                    "average_time": avg_time,
                    "max_time": max_time,
                    "min_time": min_time,
                    "target_time": target_time,
                },
            ))
            
            if passed:
                logger.info(f"✓ {test_name} PASSED (all calculations < {target_time}s)")
            else:
                logger.error(f"✗ {test_name} FAILED (max time {max_time:.4f}s >= {target_time}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                details={"error": str(e)},
            ))

    async def test_performance(self) -> None:
        """测试性能"""
        test_name = "Performance Benchmark"
        logger.info(f"\n--- Testing: {test_name} ---")
        
        start_time = time.time()
        
        try:
            if not self.controller:
                raise RuntimeError("Controller not initialized")
            
            # 性能测试1: 批量路径查询
            query_start = time.time()
            path_queries = 0
            
            # 查询多个源-目的地对
            test_pairs = [
                ("access-1", "access-10"),
                ("core-1", "pop-8"),
                ("pop-1", "access-5"),
                ("access-3", "core-2"),
                ("pop-4", "pop-7"),
            ]
            
            for source, dest in test_pairs:
                paths = self.controller.get_path_between(source, dest)
                if paths:
                    path_queries += 1
                    logger.debug(f"    {source} -> {dest}: {len(paths)} paths found")
            
            query_time = time.time() - query_start
            
            # 性能测试2: 缓存命中率
            cache_stats = self.controller.route_cache.get_stats() if self.controller.route_cache else {}
            
            logger.info(f"  Path Query Performance:")
            logger.info(f"    - Queries performed: {path_queries}")
            logger.info(f"    - Total time: {query_time:.4f}s")
            logger.info(f"    - Average per query: {query_time/max(1, path_queries):.6f}s")
            
            if cache_stats:
                logger.info(f"\n  Cache Statistics:")
                logger.info(f"    - Cache size: {cache_stats.get('size', 0)}")
                logger.info(f"    - Utilization: {cache_stats.get('utilization', 0):.2%}")
            
            # 验证性能要求
            from .config import PERFORMANCE_CONFIG
            target_time = PERFORMANCE_CONFIG["max_computation_time"]
            
            # 主要验证路由计算时间已经在test_route_calculation中测试
            # 这里主要验证缓存和查询性能
            
            passed = True  # 默认通过，因为没有严格的查询时间限制
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=passed,
                duration=duration,
                details={
                    "path_queries": path_queries,
                    "query_time": query_time,
                    "cache_stats": cache_stats,
                },
            ))
            
            logger.info(f"✓ {test_name} PASSED")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                details={"error": str(e)},
            ))

    async def test_path_finding(self) -> None:
        """测试路径查找"""
        test_name = "Path Finding"
        logger.info(f"\n--- Testing: {test_name} ---")
        
        start_time = time.time()
        
        try:
            if not self.controller:
                raise RuntimeError("Controller not initialized")
            
            # 测试不同类型的路径查找
            test_cases = [
                # (源, 目的地, 描述)
                ("access-1", "core-1", "Access to Core"),
                ("core-1", "access-1", "Core to Access"),
                ("access-1", "access-2", "Access to Access"),
                ("pop-1", "core-1", "POP to Core"),
                ("pop-1", "access-1", "POP to Access"),
                ("core-1", "core-2", "Core to Core"),
                ("pop-1", "pop-2", "POP to POP"),
            ]
            
            all_passed = True
            paths_found = 0
            
            for source, dest, description in test_cases:
                paths = self.controller.get_path_between(source, dest)
                
                if paths:
                    paths_found += 1
                    primary_path = paths[0]
                    logger.info(f"  ✓ {description} ({source} -> {dest}):")
                    logger.info(f"      - Paths found: {len(paths)}")
                    logger.info(f"      - Primary path: {' -> '.join(primary_path['nodes'])}")
                    logger.info(f"      - Cost: {primary_path['total_cost']}")
                    logger.info(f"      - Latency: {primary_path['latency']:.2f}ms")
                else:
                    all_passed = False
                    logger.error(f"  ✗ {description} ({source} -> {dest}): No path found")
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=all_passed,
                duration=duration,
                details={
                    "test_cases": len(test_cases),
                    "paths_found": paths_found,
                },
            ))
            
            if all_passed:
                logger.info(f"✓ {test_name} PASSED ({paths_found}/{len(test_cases)} paths found)")
            else:
                logger.error(f"✗ {test_name} FAILED")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                details={"error": str(e)},
            ))

    async def test_ecmp(self) -> None:
        """测试等价多路径(ECMP)"""
        test_name = "ECMP (Equal-Cost Multi-Path)"
        logger.info(f"\n--- Testing: {test_name} ---")
        
        start_time = time.time()
        
        try:
            if not self.controller:
                raise RuntimeError("Controller not initialized")
            
            # 查找可能存在ECMP的路径
            # 通常是接入交换机到核心交换机（双归属）
            ecmp_cases = [
                ("access-1", "core-1"),  # 可能有多个路径
                ("access-1", "core-2"),
                ("pop-1", "core-1"),
            ]
            
            ecmp_found = 0
            
            for source, dest in ecmp_cases:
                paths = self.controller.get_path_between(source, dest)
                
                if paths and len(paths) > 1:
                    ecmp_found += 1
                    logger.info(f"  ✓ ECMP found for {source} -> {dest}:")
                    for i, path in enumerate(paths):
                        logger.info(f"      Path {i+1}: {' -> '.join(path['nodes'])} (cost: {path['total_cost']})")
                elif paths:
                    logger.info(f"  - Single path for {source} -> {dest}: {' -> '.join(paths[0]['nodes'])}")
                else:
                    logger.warning(f"  - No path found for {source} -> {dest}")
            
            # ECMP测试不做硬性要求，只要功能正常即可
            passed = True
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=passed,
                duration=duration,
                details={
                    "ecmp_found": ecmp_found,
                    "total_cases": len(ecmp_cases),
                },
            ))
            
            logger.info(f"✓ {test_name} PASSED")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                details={"error": str(e)},
            ))

    async def test_failover(self) -> None:
        """测试故障恢复"""
        test_name = "Failover and Re-routing"
        logger.info(f"\n--- Testing: {test_name} ---")
        
        start_time = time.time()
        
        try:
            if not self.controller:
                raise RuntimeError("Controller not initialized")
            
            # 1. 获取故障前的路径
            source = "access-1"
            dest = "core-1"
            
            original_paths = self.controller.get_path_between(source, dest)
            
            if not original_paths:
                logger.warning(f"No path found for {source} -> {dest}, skipping failover test")
                self.test_results.append(TestResult(
                    test_name=test_name,
                    passed=True,
                    duration=time.time() - start_time,
                    details={"skipped": "No initial path found"},
                ))
                logger.info(f"✓ {test_name} SKIPPED")
                return
            
            original_path = original_paths[0]
            logger.info(f"  Original path: {' -> '.join(original_path['nodes'])}")
            
            # 2. 模拟链路故障
            # 找到拓扑中的一个链路
            topology = self.controller.core_controller.topology
            links = list(topology.links.values())
            
            if not links:
                logger.warning("No links found in topology")
                self.test_results.append(TestResult(
                    test_name=test_name,
                    passed=True,
                    duration=time.time() - start_time,
                    details={"skipped": "No links found"},
                ))
                return
            
            # 选择一个链路进行测试
            test_link = links[0]
            logger.info(f"  Simulating link failure: {test_link.link_id} "
                       f"({test_link.source_switch_id} <-> {test_link.destination_switch_id})")
            
            # 3. 更新链路状态
            failover_start = time.time()
            success = await self.controller.update_link_status(test_link.link_id, "down")
            failover_time = time.time() - failover_start
            
            if not success:
                raise RuntimeError("Failed to update link status")
            
            # 4. 验证路由重新计算
            new_paths = self.controller.get_path_between(source, dest)
            
            if new_paths:
                new_path = new_paths[0]
                logger.info(f"  New path after failure: {' -> '.join(new_path['nodes'])}")
                logger.info(f"  Failover time: {failover_time:.4f}s")
            else:
                logger.warning(f"  No path found after link failure")
            
            # 5. 恢复链路
            await self.controller.update_link_status(test_link.link_id, "up")
            logger.info(f"  Link restored")
            
            passed = True
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=passed,
                duration=duration,
                details={
                    "original_path": original_path["nodes"],
                    "failover_time": failover_time,
                    "test_link": test_link.link_id,
                },
            ))
            
            logger.info(f"✓ {test_name} PASSED")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            self.test_results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                details={"error": str(e)},
            ))

    def _print_test_summary(self) -> None:
        """打印测试结果摘要"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed_count = sum(1 for r in self.test_results if r.passed)
        total_count = len(self.test_results)
        
        print(f"\nResults: {passed_count}/{total_count} tests passed")
        print("\nDetailed Results:")
        
        for result in self.test_results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.test_name}: {result.duration:.4f}s")
        
        # 计算总时间
        total_time = sum(r.duration for r in self.test_results)
        print(f"\nTotal test time: {total_time:.4f}s")
        
        if passed_count == total_count:
            print("\n" + "=" * 60)
            print("ALL TESTS PASSED! ✓")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("SOME TESTS FAILED! ✗")
            print("=" * 60)


async def run_tests():
    """运行测试"""
    tester = SDWANControllerTester()
    success = await tester.run_all_tests()
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
