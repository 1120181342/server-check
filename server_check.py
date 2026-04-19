#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
华为5280HF服务器综合巡检脚本
功能：查询服务器电源、硬盘、CPU、内存、风扇所有状态
支持：多线程并发巡检，Excel格式输出

此脚本为综合巡检脚本，会一次性检查所有硬件状态。
如需单独检查某个组件，请使用以下专用脚本：
- check_power.py  - 电源状态巡检
- check_fan.py    - 风扇状态巡检
- check_cpu.py    - CPU状态巡检
- check_memory.py - 内存状态巡检
- check_disk.py   - 硬盘状态巡检
"""

from common import create_base_parser, run_check_flow


def main():
    """
    主函数
    """
    epilog = '''
使用示例:
  python server_check.py -i servers.xlsx -c public -o result.xlsx
  python server_check.py --ip-file servers.xlsx --community private --output result_20260419.xlsx
  python server_check.py -i servers.xlsx -c public -w 100 -t 10

独立巡检脚本:
  python check_power.py  - 仅检查电源状态
  python check_fan.py    - 仅检查风扇状态
  python check_cpu.py    - 仅检查CPU状态
  python check_memory.py - 仅检查内存状态
  python check_disk.py   - 仅检查硬盘状态

注意事项:
1. 请确保服务器已启用SNMP服务，并配置了正确的团体名
2. IP列表文件第一行为表头，从第二行开始读取IP地址
3. 对于2000-3000台服务器，建议设置较大的并发线程数（如100-200）
4. 如遇连接超时，请适当增加超时时间或减少并发线程数
5. 综合巡检会检查所有硬件状态，生成包含所有信息的Excel报告
    '''

    parser = create_base_parser(
        description='华为5280HF服务器综合巡检脚本 - 检查所有硬件状态',
        epilog=epilog
    )

    args = parser.parse_args()

    # 执行综合巡检
    run_check_flow(
        args=args,
        check_type='all',
        check_name='综合巡检',
        output_prefix='server_check'
    )


if __name__ == '__main__':
    main()
