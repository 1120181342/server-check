#!/usr/bin/env python3
import sys
import os
import json
from typing import Optional, List, Tuple, TextIO

import click

from ip_classifier import (
    IPClassifier, create_default_classifier,
    load_cidr_list, load_cidr_from_file,
    is_valid_ipv4, ip_to_int
)


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class ColorOutput:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    @classmethod
    def enable(cls):
        if os.name == 'nt':
            os.system('color')
    
    @classmethod
    def green(cls, text: str) -> str:
        return f"{cls.GREEN}{text}{cls.RESET}"
    
    @classmethod
    def red(cls, text: str) -> str:
        return f"{cls.RED}{text}{cls.RESET}"
    
    @classmethod
    def yellow(cls, text: str) -> str:
        return f"{cls.YELLOW}{text}{cls.RESET}"
    
    @classmethod
    def cyan(cls, text: str) -> str:
        return f"{cls.CYAN}{text}{cls.RESET}"
    
    @classmethod
    def bold(cls, text: str) -> str:
        return f"{cls.BOLD}{text}{cls.RESET}"


def get_classifier(cidr_file: Optional[str] = None, 
                   cidrs: Optional[List[str]] = None) -> IPClassifier:
    if cidr_file:
        classifier = IPClassifier()
        classifier.load_china_cidrs_from_file(cidr_file)
        return classifier
    elif cidrs:
        classifier = IPClassifier()
        classifier.load_china_cidrs(cidrs)
        return classifier
    else:
        return create_default_classifier()


def read_ips_from_source(source: str) -> List[str]:
    if os.path.exists(source):
        with open(source, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    else:
        return [ip.strip() for ip in source.split(',') if ip.strip()]


def read_ips_from_stdin() -> List[str]:
    if not sys.stdin.isatty():
        return [line.strip() for line in sys.stdin if line.strip()]
    return []


def format_result(ip: str, is_china: bool, format_type: str = 'text', 
                  color: bool = True) -> str:
    if color:
        status = ColorOutput.green("国内") if is_china else ColorOutput.red("境外")
    else:
        status = "国内" if is_china else "境外"
    
    if format_type == 'json':
        return json.dumps({"ip": ip, "is_china": is_china, "location": "国内" if is_china else "境外"}, 
                         ensure_ascii=False)
    elif format_type == 'csv':
        return f"{ip},{is_china},{'国内' if is_china else '境外'}"
    else:
        if color:
            return f"{ColorOutput.cyan(ip):<18} -> {status}"
        else:
            return f"{ip:<18} -> {status}"


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='显示版本信息')
@click.pass_context
def cli(ctx: click.Context, version: bool):
    """
    IP地址分类工具 - 高效区分国内/境外IP地址
    
    功能特性:
    \b
      - 基于CIDR网段的二分查找，O(log n)时间复杂度
      - 支持命令行、文件、标准输入三种输入方式
      - 支持文本、JSON、CSV多种输出格式
      - 内存占用小，性能高
    
    示例:
    \b
      # 检查单个IP
      ipclassifier check 8.8.8.8
      
      # 检查多个IP
      ipclassifier check 223.5.5.5,1.1.1.1,114.114.114.114
      
      # 从文件分类并输出到文件
      ipclassifier classify -i ips.txt -c china.txt -f foreign.txt
      
      # 从管道读取
      cat ips.txt | ipclassifier classify
      
      # JSON格式输出
      ipclassifier check 8.8.8.8 -o json
    """
    if version:
        click.echo("IP Classifier v2.0.0")
        ctx.exit()
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command('check')
@click.argument('ips', nargs=-1)
@click.option('--cidr-file', '-c', type=click.Path(exists=True),
              help='自定义CIDR网段文件')
@click.option('--output', '-o', type=click.Choice(['text', 'json', 'csv']), 
              default='text', help='输出格式 (默认: text)')
@click.option('--no-color', is_flag=True, help='禁用颜色输出')
@click.option('--quiet', '-q', is_flag=True, help='静默模式，仅输出结果')
@click.option('--stats', '-s', is_flag=True, help='显示统计信息')
def check_cmd(ips: Tuple[str, ...], cidr_file: Optional[str], 
              output: str, no_color: bool, quiet: bool, stats: bool):
    """
    检查单个或多个IP地址
    
    IPS: IP地址列表，可以是逗号分隔的字符串或空格分隔的多个参数
    
    示例:
    \b
      ipclassifier check 8.8.8.8
      ipclassifier check 223.5.5.5 1.1.1.1 114.114.114.114
      ipclassifier check 8.8.8.8 -o json
    """
    if not no_color:
        ColorOutput.enable()
    
    classifier = get_classifier(cidr_file)
    
    all_ips = []
    for ip_part in ips:
        if ',' in ip_part:
            all_ips.extend([ip.strip() for ip in ip_part.split(',') if ip.strip()])
        else:
            all_ips.append(ip_part.strip())
    
    if not all_ips:
        all_ips = read_ips_from_stdin()
    
    if not all_ips:
        click.echo("错误: 请提供IP地址", err=True)
        sys.exit(1)
    
    results = []
    china_count = 0
    foreign_count = 0
    invalid_count = 0
    
    for ip in all_ips:
        if not is_valid_ipv4(ip):
            invalid_count += 1
            if not quiet:
                if output == 'json':
                    results.append({"ip": ip, "is_valid": False, "error": "无效的IP地址"})
                elif output == 'csv':
                    results.append(f"{ip},False,,无效IP")
                else:
                    msg = f"{ColorOutput.yellow(ip) if not no_color else ip} -> 无效IP地址"
                    results.append(msg)
            continue
        
        is_china = classifier.is_china_ip(ip)
        if is_china:
            china_count += 1
        else:
            foreign_count += 1
        
        results.append(format_result(ip, is_china, output, not no_color))
    
    for result in results:
        click.echo(result)
    
    if stats and not quiet:
        click.echo()
        if not no_color:
            click.echo(ColorOutput.bold("=" * 40))
            click.echo(f"{ColorOutput.cyan('统计信息')}")
            click.echo(ColorOutput.bold("=" * 40))
            click.echo(f"  总IP数: {len(all_ips)}")
            click.echo(f"  国内IP: {ColorOutput.green(str(china_count))}")
            click.echo(f"  境外IP: {ColorOutput.red(str(foreign_count))}")
            if invalid_count > 0:
                click.echo(f"  无效IP: {ColorOutput.yellow(str(invalid_count))}")
        else:
            click.echo("=" * 40)
            click.echo("统计信息")
            click.echo("=" * 40)
            click.echo(f"  总IP数: {len(all_ips)}")
            click.echo(f"  国内IP: {china_count}")
            click.echo(f"  境外IP: {foreign_count}")
            if invalid_count > 0:
                click.echo(f"  无效IP: {invalid_count}")


@cli.command('classify')
@click.option('--input', '-i', type=click.Path(exists=True),
              help='输入文件路径，每行一个IP地址')
@click.option('--china-output', '-c', type=click.Path(), default='china_ips.txt',
              help='国内IP输出文件 (默认: china_ips.txt)')
@click.option('--foreign-output', '-f', type=click.Path(), default='foreign_ips.txt',
              help='境外IP输出文件 (默认: foreign_ips.txt)')
@click.option('--cidr-file', type=click.Path(exists=True),
              help='自定义CIDR网段文件')
@click.option('--output', '-o', type=click.Choice(['files', 'stdout', 'both']), 
              default='files', help='输出方式 (默认: files)')
@click.option('--format', '-fmt', type=click.Choice(['text', 'json', 'csv']), 
              default='text', help='stdout输出格式 (默认: text)')
@click.option('--quiet', '-q', is_flag=True, help='静默模式')
@click.option('--append', '-a', is_flag=True, help='追加模式写入输出文件')
def classify_cmd(input: Optional[str], china_output: str, foreign_output: str,
                 cidr_file: Optional[str], output: str, format: str, quiet: bool,
                 append: bool):
    """
    批量分类IP地址
    
    支持从文件或标准输入读取IP，分类后写入文件或输出到stdout
    
    示例:
    \b
      # 从文件分类
      ipclassifier classify -i ips.txt -c china.txt -f foreign.txt
      
      # 从管道读取并输出到文件
      cat ips.txt | ipclassifier classify -c out-china.txt -f out-foreign.txt
      
      # 同时输出到文件和stdout
      ipclassifier classify -i ips.txt -o both
      
      # JSON格式输出到stdout
      cat ips.txt | ipclassifier classify -o stdout -fmt json
    """
    classifier = get_classifier(cidr_file)
    
    all_ips = []
    
    if input:
        with open(input, 'r', encoding='utf-8') as f:
            all_ips = [line.strip() for line in f if line.strip()]
    else:
        all_ips = read_ips_from_stdin()
    
    if not all_ips:
        click.echo("错误: 请通过 -i 参数或标准输入提供IP地址", err=True)
        sys.exit(1)
    
    china_ips = []
    foreign_ips = []
    invalid_ips = []
    
    for ip in all_ips:
        if not is_valid_ipv4(ip):
            invalid_ips.append(ip)
            continue
        
        if classifier.is_china_ip(ip):
            china_ips.append(ip)
        else:
            foreign_ips.append(ip)
    
    if output in ['files', 'both']:
        mode = 'a' if append else 'w'
        with open(china_output, mode, encoding='utf-8') as f:
            for ip in china_ips:
                f.write(ip + '\n')
        
        with open(foreign_output, mode, encoding='utf-8') as f:
            for ip in foreign_ips:
                f.write(ip + '\n')
    
    if output in ['stdout', 'both']:
        for ip in china_ips:
            click.echo(format_result(ip, True, format, color=False))
        for ip in foreign_ips:
            click.echo(format_result(ip, False, format, color=False))
    
    if not quiet:
        click.echo()
        click.echo("=" * 40)
        click.echo("分类完成")
        click.echo("=" * 40)
        click.echo(f"  总IP数: {len(all_ips)}")
        click.echo(f"  国内IP: {len(china_ips)} 个")
        click.echo(f"  境外IP: {len(foreign_ips)} 个")
        if invalid_ips:
            click.echo(f"  无效IP: {len(invalid_ips)} 个")
        
        if output in ['files', 'both']:
            click.echo()
            click.echo(f"  国内IP -> {china_output}")
            click.echo(f"  境外IP -> {foreign_output}")


@cli.command('stats')
@click.option('--input', '-i', type=click.Path(exists=True),
              help='输入文件路径')
@click.option('--cidr-file', type=click.Path(exists=True),
              help='自定义CIDR网段文件')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), 
              default='text', help='输出格式')
@click.option('--list-ips', '-l', is_flag=True, help='同时列出所有IP')
def stats_cmd(input: Optional[str], cidr_file: Optional[str], 
              output: str, list_ips: bool):
    """
    统计IP地址分布情况
    
    示例:
    \b
      # 统计文件中的IP分布
      ipclassifier stats -i ips.txt
      
      # JSON格式输出
      ipclassifier stats -i ips.txt -o json
      
      # 列出所有IP及其分类
      ipclassifier stats -i ips.txt -l
    """
    classifier = get_classifier(cidr_file)
    
    all_ips = []
    if input:
        with open(input, 'r', encoding='utf-8') as f:
            all_ips = [line.strip() for line in f if line.strip()]
    else:
        all_ips = read_ips_from_stdin()
    
    if not all_ips:
        click.echo("错误: 请通过 -i 参数或标准输入提供IP地址", err=True)
        sys.exit(1)
    
    china_ips = []
    foreign_ips = []
    invalid_ips = []
    
    for ip in all_ips:
        if not is_valid_ipv4(ip):
            invalid_ips.append(ip)
            continue
        
        if classifier.is_china_ip(ip):
            china_ips.append(ip)
        else:
            foreign_ips.append(ip)
    
    stats_data = {
        "total": len(all_ips),
        "china": {
            "count": len(china_ips),
            "percentage": round(len(china_ips) / len(all_ips) * 100, 2) if all_ips else 0,
            "ips": china_ips if list_ips else []
        },
        "foreign": {
            "count": len(foreign_ips),
            "percentage": round(len(foreign_ips) / len(all_ips) * 100, 2) if all_ips else 0,
            "ips": foreign_ips if list_ips else []
        },
        "invalid": {
            "count": len(invalid_ips),
            "ips": invalid_ips if list_ips else []
        }
    }
    
    if output == 'json':
        click.echo(json.dumps(stats_data, ensure_ascii=False, indent=2))
    else:
        ColorOutput.enable()
        click.echo(ColorOutput.bold("=" * 50))
        click.echo(ColorOutput.cyan("IP地址分布统计"))
        click.echo(ColorOutput.bold("=" * 50))
        click.echo()
        click.echo(f"  总IP数: {stats_data['total']}")
        click.echo()
        click.echo(f"  {ColorOutput.green('国内IP')}: {stats_data['china']['count']} 个 ({stats_data['china']['percentage']}%)")
        click.echo(f"  {ColorOutput.red('境外IP')}: {stats_data['foreign']['count']} 个 ({stats_data['foreign']['percentage']}%)")
        if stats_data['invalid']['count'] > 0:
            click.echo(f"  {ColorOutput.yellow('无效IP')}: {stats_data['invalid']['count']} 个")
        
        if list_ips:
            click.echo()
            click.echo(ColorOutput.bold("-" * 50))
            if china_ips:
                click.echo(f"\n{ColorOutput.green('国内IP列表:')}")
                for ip in china_ips:
                    click.echo(f"    {ip}")
            if foreign_ips:
                click.echo(f"\n{ColorOutput.red('境外IP列表:')}")
                for ip in foreign_ips:
                    click.echo(f"    {ip}")
            if invalid_ips:
                click.echo(f"\n{ColorOutput.yellow('无效IP列表:')}")
                for ip in invalid_ips:
                    click.echo(f"    {ip}")


@cli.command('info')
@click.option('--cidr-file', type=click.Path(exists=True),
              help='自定义CIDR网段文件')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), 
              default='text', help='输出格式')
def info_cmd(cidr_file: Optional[str], output: str):
    """
    显示分类器信息
    
    示例:
    \b
      # 显示默认分类器信息
      ipclassifier info
      
      # 显示自定义CIDR分类器信息
      ipclassifier info --cidr-file my_cidrs.txt
    """
    classifier = get_classifier(cidr_file)
    
    info_data = {
        "version": "2.0.0",
        "cidr_source": "自定义" if cidr_file else "默认内置",
        "cidr_file": cidr_file,
        "total_ranges": len(classifier._china_ranges) if hasattr(classifier, '_china_ranges') else 0
    }
    
    if output == 'json':
        click.echo(json.dumps(info_data, ensure_ascii=False, indent=2))
    else:
        ColorOutput.enable()
        click.echo(ColorOutput.bold("=" * 50))
        click.echo(ColorOutput.cyan("IP Classifier 信息"))
        click.echo(ColorOutput.bold("=" * 50))
        click.echo()
        click.echo(f"  版本: {info_data['version']}")
        click.echo(f"  CIDR来源: {info_data['cidr_source']}")
        if cidr_file:
            click.echo(f"  CIDR文件: {cidr_file}")
        click.echo(f"  网段总数: {info_data['total_ranges']}")
        click.echo()
        click.echo("  支持的命令:")
        click.echo("    check  - 检查单个或多个IP")
        click.echo("    classify - 批量分类IP")
        click.echo("    stats  - 统计IP分布")
        click.echo("    info   - 显示此信息")


if __name__ == '__main__':
    cli()
