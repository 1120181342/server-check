#!/usr/bin/env python3
import argparse
import sys
from ip_classifier import create_default_classifier, IPClassifier


def main():
    parser = argparse.ArgumentParser(
        description='IP地址分类工具 - 区分国内/境外IP地址',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 从命令行参数分类IP
  python classify_ips.py --ips "1.1.1.1,8.8.8.8,223.5.5.5"
  
  # 从文件读取IP并分类到两个输出文件
  python classify_ips.py --input ips.txt --china-output china.txt --foreign-output foreign.txt
  
  # 使用自定义CIDR文件
  python classify_ips.py --cidr-file my_cidrs.txt --ips "1.2.3.4"
        '''
    )
    
    parser.add_argument('--ips', type=str, 
                        help='逗号分隔的IP地址列表 (例如: "1.1.1.1,8.8.8.8")')
    parser.add_argument('--input', '-i', type=str,
                        help='输入文件路径，每行一个IP地址')
    parser.add_argument('--china-output', '-c', type=str, default='china_ips.txt',
                        help='国内IP输出文件路径 (默认: china_ips.txt)')
    parser.add_argument('--foreign-output', '-f', type=str, default='foreign_ips.txt',
                        help='境外IP输出文件路径 (默认: foreign_ips.txt)')
    parser.add_argument('--cidr-file', type=str,
                        help='自定义国内CIDR段文件路径，每行一个CIDR')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='静默模式，不输出详细信息')
    parser.add_argument('--version', '-v', action='version', version='IP Classifier 1.0')
    
    args = parser.parse_args()
    
    if not args.ips and not args.input:
        parser.print_help()
        sys.exit(1)
    
    if not args.quiet:
        print('=' * 50)
        print('IP地址分类工具')
        print('=' * 50)
    
    if args.cidr_file:
        if not args.quiet:
            print(f'加载自定义CIDR文件: {args.cidr_file}')
        classifier = IPClassifier()
        classifier.load_china_cidrs_from_file(args.cidr_file)
    else:
        if not args.quiet:
            print('使用默认国内CIDR段')
        classifier = create_default_classifier()
    
    if args.ips:
        ip_list = [ip.strip() for ip in args.ips.split(',') if ip.strip()]
        
        if not args.quiet:
            print(f'\n输入IP数量: {len(ip_list)}')
            print('-' * 50)
        
        china_ips, foreign_ips = classifier.classify(iter(ip_list))
        
        if not args.quiet:
            print(f'国内IP: {len(china_ips)} 个')
            print(f'境外IP: {len(foreign_ips)} 个')
            print('-' * 50)
            
            if china_ips:
                print('\n国内IP列表:')
                for ip in china_ips:
                    print(f'  {ip}')
            
            if foreign_ips:
                print('\n境外IP列表:')
                for ip in foreign_ips:
                    print(f'  {ip}')
        
        with open(args.china_output, 'w', encoding='utf-8') as f:
            for ip in china_ips:
                f.write(ip + '\n')
        
        with open(args.foreign_output, 'w', encoding='utf-8') as f:
            for ip in foreign_ips:
                f.write(ip + '\n')
        
        if not args.quiet:
            print(f'\n结果已保存:')
            print(f'  国内IP: {args.china_output}')
            print(f'  境外IP: {args.foreign_output}')
    
    if args.input:
        if not args.quiet:
            print(f'\n从文件读取: {args.input}')
            print('正在分类...')
        
        china_count, foreign_count = classifier.classify_to_files(
            args.input,
            args.china_output,
            args.foreign_output
        )
        
        if not args.quiet:
            print(f'\n分类完成!')
            print(f'  国内IP: {china_count} 个 -> {args.china_output}')
            print(f'  境外IP: {foreign_count} 个 -> {args.foreign_output}')
    
    if not args.quiet:
        print('=' * 50)


if __name__ == '__main__':
    main()
