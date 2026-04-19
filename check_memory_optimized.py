#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
华为5280HF服务器内存状态巡检脚本 [高性能优化版]
功能：仅查询服务器内存状态
"""

from common_optimized import create_base_parser, run_check_flow


def main():
    epilog = '''
使用示例:
  python check_memory_optimized.py -i servers.xlsx -c public
  python check_memory_optimized.py -i servers.xlsx -c public -w 400
    '''

    parser = create_base_parser(
        description='华为5280HF服务器内存状态巡检脚本 [高性能优化版]',
        epilog=epilog
    )

    args = parser.parse_args()

    run_check_flow(
        args=args,
        check_type='memory',
        check_name='内存状态巡检',
        output_prefix='memory_check_optimized'
    )


if __name__ == '__main__':
    main()
