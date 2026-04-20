#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
华为5280HF服务器风扇状态巡检脚本
功能：查询服务器风扇状态和转速
支持：多线程并发巡检，Excel格式输出
"""

from common import create_base_parser, run_check_flow


def main():
    """
    主函数
    """
    epilog = '''
使用示例:
  python check_fan.py -i servers.xlsx -c public -o fan_result.xlsx
  python check_fan.py --ip-file servers.xlsx --community private --output fan_20260419.xlsx
  python check_fan.py -i servers.xlsx -c public -w 100 -t 10

注意事项:
1. 请确保服务器已启用SNMP服务，并配置了正确的团体名
2. IP列表文件第一行为表头，从第二行开始读取IP地址
3. 对于2000-3000台服务器，建议设置较大的并发线程数（如100-200）
4. 如遇连接超时，请适当增加超时时间或减少并发线程数
5. 风扇状态包括：风扇运行状态、转速(RPM)
    '''

    parser = create_base_parser(
        description='华为5280HF服务器风扇状态巡检脚本',
        epilog=epilog
    )

    args = parser.parse_args()

    # 执行风扇状态巡检
    run_check_flow(
        args=args,
        check_type='fan',
        check_name='风扇状态巡检',
        output_prefix='fan_check'
    )


if __name__ == '__main__':
    main()
