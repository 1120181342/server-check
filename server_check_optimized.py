#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
华为5280HF服务器综合巡检脚本 [高性能优化版]
功能：查询服务器电源、硬盘、CPU、内存、风扇所有状态
优化特性：异步SNMP、批量查询、高并发控制、内存优化

此脚本为优化版本，适合2000-3000台服务器的大规模巡检。
预计性能提升：3-5倍（相比原版本）
"""

from common_optimized import create_base_parser, run_check_flow


def main():
    epilog = '''
使用示例:
  python server_check_optimized.py -i servers.xlsx -c public -o result.xlsx
  python server_check_optimized.py -i servers.xlsx -c public -w 300 -t 3
  python server_check_optimized.py -i servers.xlsx -c public --no-async

性能优化参数建议（2000-3000台服务器）:
  -w/--workers: 200-500（并发数，根据网络和服务器性能调整）
  -t/--timeout: 2-5秒（建议比原版本更短，因为有重试机制）
  -r/--retries: 1-2次（减少重试，快速失败）

独立巡检优化脚本:
  python check_power_optimized.py  - 仅检查电源状态（优化版）
  python check_fan_optimized.py    - 仅检查风扇状态（优化版）
  python check_cpu_optimized.py    - 仅检查CPU状态（优化版）
  python check_memory_optimized.py - 仅检查内存状态（优化版）
  python check_disk_optimized.py   - 仅检查硬盘状态（优化版）

注意事项:
1. 请确保已安装优化依赖: pip install aiosnmp aiohttp
2. 优化版本默认使用异步SNMP，性能提升显著
3. 如遇兼容性问题，可使用 --no-async 参数强制使用同步模式
4. 对于2000-3000台服务器，建议并发数设置为300-500
5. 预计3000台服务器巡检时间: 5-8分钟（根据网络状况）
    '''

    parser = create_base_parser(
        description='华为5280HF服务器综合巡检脚本 [高性能优化版] - 检查所有硬件状态',
        epilog=epilog
    )

    args = parser.parse_args()

    run_check_flow(
        args=args,
        check_type='all',
        check_name='综合巡检',
        output_prefix='server_check_optimized'
    )


if __name__ == '__main__':
    main()
