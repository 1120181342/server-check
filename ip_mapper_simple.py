#!/usr/bin/env python3
import sys
import os
import json
import argparse
import time
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from ip_mapper import IPMapper, CloudServer, is_valid_ipv4


def format_server_simple(server: CloudServer, index: Optional[int] = None) -> str:
    idx_str = f"[{index}] " if index is not None else ""
    return (
        f"{idx_str}服务器ID: {server.server_id}\n"
        f"  IP地址: {server.ip}\n"
        f"  所属用户: {server.user}\n"
        f"  描述: {server.description or '-'}"
    )


def cmd_add(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    if not is_valid_ipv4(args.ip):
        print(f"错误: 无效的IP地址 '{args.ip}'", file=sys.stderr)
        return 1
    
    if mapper.add_server(args.id, args.ip, args.user, args.desc or ""):
        print(f"成功: 已添加服务器 {args.id}")
        return 0
    else:
        existing = mapper.get_server_by_id(args.id)
        if existing:
            print(f"错误: 服务器ID '{args.id}' 已存在", file=sys.stderr)
        else:
            print(f"错误: IP地址 '{args.ip}' 已被使用", file=sys.stderr)
        return 1


def cmd_update(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    if args.ip is not None and not is_valid_ipv4(args.ip):
        print(f"错误: 无效的IP地址 '{args.ip}'", file=sys.stderr)
        return 1
    
    if mapper.update_server(args.id, args.ip, args.user, args.desc):
        print(f"成功: 已更新服务器 {args.id}")
        return 0
    else:
        existing = mapper.get_server_by_id(args.id)
        if not existing:
            print(f"错误: 服务器ID '{args.id}' 不存在", file=sys.stderr)
        elif args.ip is not None:
            print(f"错误: IP地址 '{args.ip}' 已被其他服务器使用", file=sys.stderr)
        else:
            print("错误: 更新失败", file=sys.stderr)
        return 1


def cmd_delete(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    if not args.id and not args.ip:
        print("错误: 必须提供 --id 或 --ip 参数", file=sys.stderr)
        return 1
    
    target_server = None
    if args.id:
        target_server = mapper.get_server_by_id(args.id)
    elif args.ip:
        target_server = mapper.get_server_by_ip(args.ip)
    
    if not target_server:
        if args.id:
            print(f"错误: 服务器ID '{args.id}' 不存在", file=sys.stderr)
        else:
            print(f"错误: IP地址 '{args.ip}' 不存在", file=sys.stderr)
        return 1
    
    if not args.force:
        print("警告: 即将删除以下服务器:")
        print(format_server_simple(target_server))
        confirm = input("请输入 'yes' 确认删除 (输入其他内容取消): ")
        if confirm.lower() != "yes":
            print("已取消删除")
            return 0
    
    if mapper.delete_server(target_server.server_id):
        print(f"成功: 已删除服务器 {target_server.server_id}")
        return 0
    else:
        print("错误: 删除失败", file=sys.stderr)
        return 1


def cmd_query(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    if not args.ip and not args.id and not args.user:
        print("错误: 必须提供 --ip、--id 或 --user 参数", file=sys.stderr)
        return 1
    
    servers: List[CloudServer] = []
    
    if args.ip:
        server = mapper.get_server_by_ip(args.ip)
        if server:
            servers.append(server)
    elif args.id:
        server = mapper.get_server_by_id(args.id)
        if server:
            servers.append(server)
    elif args.user:
        servers = mapper.get_servers_by_user(args.user)
    
    if not servers:
        if args.ip:
            print(f"未找到IP地址 '{args.ip}' 对应的服务器")
        elif args.id:
            print(f"未找到服务器ID '{args.id}'")
        else:
            print(f"用户 '{args.user}' 没有服务器")
        return 0
    
    if args.output == "json":
        json_data = [asdict(s) for s in servers]
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    elif args.output == "csv":
        print("server_id,ip,user,description")
        for server in servers:
            print(f"{server.server_id},{server.ip},{server.user},{server.description}")
    else:
        for i, server in enumerate(servers):
            print(format_server_simple(server, i + 1 if len(servers) > 1 else None))
            if i < len(servers) - 1:
                print()
    
    return 0


def cmd_batch_query(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    ips: List[str] = []
    
    if args.ips:
        ips = [ip.strip() for ip in args.ips.split(",") if ip.strip()]
    elif args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                ips = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"错误: 读取输入文件失败: {e}", file=sys.stderr)
            return 1
    
    if not ips:
        print("错误: 未提供任何IP地址。请使用 --ips 或 --input 参数", file=sys.stderr)
        return 1
    
    if not args.quiet:
        print("=" * 60)
        print("云资源池IP匹配工具 - 批量并发查询")
        print("=" * 60)
        print(f"并发数: {args.workers}")
        print(f"查询IP数量: {len(ips)}")
        print("-" * 60)
        start_time = time.time()
    
    results = mapper.batch_query_ips(ips, max_workers=args.workers)
    
    if not args.quiet:
        elapsed_time = time.time() - start_time
        print()
        print("=" * 60)
        print("查询结果统计")
        print("=" * 60)
        print(f"  总IP数: {results['total']}")
        print(f"  找到: {results['found']} 个")
        print(f"  未找到: {results['not_found']} 个")
        print(f"  无效IP: {results['invalid']} 个")
        print(f"  耗时: {elapsed_time:.3f} 秒")
        print(f"  吞吐率: {len(ips)/elapsed_time:.1f} IP/秒")
        print("-" * 60)
    
    if args.output == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.output == "csv":
        print("ip,found,server_id,user,description")
        for ip, server_data in results.get("results", {}).items():
            if server_data:
                print(f"{ip},是,{server_data.get('server_id','')},{server_data.get('user','')},{server_data.get('description','')}")
        for ip in results.get("not_found_ips", []):
            print(f"{ip},否,,,")
        for ip in results.get("invalid_ips", []):
            print(f"{ip},无效IP,,,")
    else:
        if results.get("results"):
            print("\n找到的服务器:")
            print("-" * 60)
            for i, (ip, server_data) in enumerate(results["results"].items(), 1):
                if server_data:
                    print(f"\n[{i}] IP: {ip}")
                    print(f"    服务器ID: {server_data.get('server_id', '')}")
                    print(f"    所属用户: {server_data.get('user', '')}")
                    desc = server_data.get('description', '')
                    if desc:
                        print(f"    描述: {desc}")
        
        if results.get("not_found_ips"):
            print(f"\n未找到的IP ({results['not_found']} 个):")
            print("  " + ", ".join(results["not_found_ips"][:20]))
            if len(results["not_found_ips"]) > 20:
                print(f"  ... 还有 {len(results['not_found_ips']) - 20} 个")
        
        if results.get("invalid_ips"):
            print(f"\n无效的IP ({results['invalid']} 个):")
            print("  " + ", ".join(results["invalid_ips"][:20]))
            if len(results["invalid_ips"]) > 20:
                print(f"  ... 还有 {len(results['invalid_ips']) - 20} 个")
    
    if args.export:
        export_format = args.export_format or ("csv" if args.export.endswith(".csv") else "json")
        if mapper.export_query_results(results, args.export, export_format):
            print(f"\n结果已导出到: {args.export}")
        else:
            print(f"\n警告: 导出结果失败", file=sys.stderr)
    
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    servers = mapper.search_servers(args.keyword)
    
    if not servers:
        print(f"未找到包含 '{args.keyword}' 的服务器")
        return 0
    
    print(f"找到 {len(servers)} 个匹配的服务器:\n")
    
    if args.output == "json":
        json_data = [asdict(s) for s in servers]
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    elif args.output == "csv":
        print("server_id,ip,user,description")
        for server in servers:
            print(f"{server.server_id},{server.ip},{server.user},{server.description}")
    else:
        for i, server in enumerate(servers):
            print(format_server_simple(server, i + 1))
            if i < len(servers) - 1:
                print()
    
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    servers = mapper.get_all_servers()
    
    if not servers:
        print("当前没有任何服务器映射关系")
        return 0
    
    print(f"共 {len(servers)} 个服务器:\n")
    
    if args.output == "json":
        json_data = [asdict(s) for s in servers]
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    elif args.output == "csv":
        print("server_id,ip,user,description")
        for server in servers:
            print(f"{server.server_id},{server.ip},{server.user},{server.description}")
    else:
        for i, server in enumerate(servers):
            print(format_server_simple(server, i + 1))
            if i < len(servers) - 1:
                print()
    
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    result = mapper.import_from_csv(args.file)
    
    if result["errors"]:
        print("导入过程中出现以下错误:")
        for error in result["errors"]:
            print(f"  - {error}")
        print()
    
    print(f"导入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")
    
    if result["success"] == 0 and result["failed"] > 0:
        return 1
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    if mapper.export_to_csv(args.file):
        print(f"成功: 已导出到 {args.file}")
        return 0
    else:
        print("错误: 导出失败", file=sys.stderr)
        return 1


def cmd_clear(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    if not args.force:
        count = mapper.server_count
        if count == 0:
            print("当前没有任何数据需要清除")
            return 0
        
        print(f"警告: 即将清除所有 {count} 条服务器映射关系")
        confirm = input("请输入 'yes' 确认清除 (输入其他内容取消): ")
        if confirm.lower() != "yes":
            print("已取消清除")
            return 0
    
    if mapper.clear_all():
        print("成功: 已清除所有数据")
        return 0
    else:
        print("错误: 清除失败", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    mapper = IPMapper(args.data_file, max_workers=args.workers)
    
    if args.output == "json":
        info_data = {
            "version": "1.1.0",
            "data_file": mapper.data_file,
            "server_count": mapper.server_count,
            "max_workers": mapper.max_workers
        }
        print(json.dumps(info_data, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("IP Mapper 信息 (支持100并发)")
        print("=" * 60)
        print()
        print(f"  版本: 1.1.0")
        print(f"  数据文件: {mapper.data_file}")
        print(f"  服务器数量: {mapper.server_count}")
        print(f"  默认并发数: {mapper.max_workers}")
        print()
        print("  支持的命令:")
        print("    add          - 添加服务器")
        print("    update       - 更新服务器")
        print("    delete       - 删除服务器")
        print("    query        - 查询单个服务器")
        print("    batch-query  - 批量并发查询 (支持100并发)")
        print("    search       - 搜索服务器")
        print("    list         - 列出所有服务器")
        print("    import       - 从CSV导入")
        print("    export       - 导出到CSV")
        print("    clear        - 清除所有数据")
        print("    info         - 显示此信息")
        print()
        print("  并发控制:")
        print("    使用 --workers 参数指定并发数 (默认100)")
        print("    例如: python ip_mapper_simple.py batch-query --workers 100 --ips ...")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="云资源池IP匹配工具 - 管理和查询云服务器IP映射关系 (支持100并发)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 添加服务器
  python ip_mapper_simple.py add --id "vm-001" --ip "192.168.1.10" --user "张三"
  
  # 根据IP查询服务器
  python ip_mapper_simple.py query --ip "192.168.1.10"
  
  # 批量并发查询 (100并发)
  python ip_mapper_simple.py batch-query --ips "192.168.1.10,10.0.0.5,8.8.8.8" --workers 100
  
  # 从文件批量查询
  python ip_mapper_simple.py batch-query --input ips.txt --export results.json
  
  # 列出所有服务器
  python ip_mapper_simple.py list
  
  # 从CSV导入
  python ip_mapper_simple.py import --file servers.csv
  
  # 导出到CSV
  python ip_mapper_simple.py export --file backup.csv
        """
    )
    
    parser.add_argument("--version", "-v", action="version", version="IP Mapper v1.1.0 (支持100并发)")
    parser.add_argument("--data-file", "-d", help="指定数据文件路径")
    parser.add_argument("--workers", "-w", type=int, default=100, 
                        help="并发数 (默认100，最大建议200)")
    
    subparsers = parser.add_subparsers(title="可用命令", dest="command")
    
    add_parser = subparsers.add_parser("add", help="添加服务器映射关系")
    add_parser.add_argument("--id", required=True, help="服务器ID")
    add_parser.add_argument("--ip", required=True, help="服务器IP地址")
    add_parser.add_argument("--user", required=True, help="所属用户")
    add_parser.add_argument("--desc", help="描述信息")
    
    update_parser = subparsers.add_parser("update", help="更新服务器映射关系")
    update_parser.add_argument("--id", required=True, help="服务器ID")
    update_parser.add_argument("--ip", help="新的IP地址")
    update_parser.add_argument("--user", help="新的所属用户")
    update_parser.add_argument("--desc", help="新的描述信息")
    
    delete_parser = subparsers.add_parser("delete", help="删除服务器映射关系")
    delete_parser.add_argument("--id", help="服务器ID")
    delete_parser.add_argument("--ip", help="服务器IP地址")
    delete_parser.add_argument("--force", "-f", action="store_true", help="强制删除，不提示确认")
    
    query_parser = subparsers.add_parser("query", help="查询单个服务器映射关系")
    query_parser.add_argument("--ip", help="根据IP地址查询")
    query_parser.add_argument("--id", help="根据服务器ID查询")
    query_parser.add_argument("--user", help="根据用户查询所有服务器")
    query_parser.add_argument("--output", "-o", choices=["text", "json", "csv"], default="text",
                               help="输出格式 (默认: text)")
    
    batch_query_parser = subparsers.add_parser("batch-query", 
        help="批量并发查询服务器映射关系 (支持100并发)")
    batch_query_parser.add_argument("--ips", help="逗号分隔的IP地址列表")
    batch_query_parser.add_argument("--input", "-i", help="输入文件路径，每行一个IP地址")
    batch_query_parser.add_argument("--output", "-o", choices=["text", "json", "csv"], default="text",
                                      help="输出格式 (默认: text)")
    batch_query_parser.add_argument("--export", "-e", help="导出结果到文件")
    batch_query_parser.add_argument("--export-format", "-ef", choices=["json", "csv"],
                                      help="导出格式 (默认根据文件扩展名判断)")
    batch_query_parser.add_argument("--quiet", "-q", action="store_true", help="静默模式，减少输出")
    
    search_parser = subparsers.add_parser("search", help="搜索服务器映射关系")
    search_parser.add_argument("keyword", help="搜索关键词")
    search_parser.add_argument("--output", "-o", choices=["text", "json", "csv"], default="text",
                                help="输出格式 (默认: text)")
    
    list_parser = subparsers.add_parser("list", help="列出所有服务器映射关系")
    list_parser.add_argument("--output", "-o", choices=["text", "json", "csv"], default="text",
                              help="输出格式 (默认: text)")
    
    import_parser = subparsers.add_parser("import", help="从CSV文件批量导入服务器映射关系")
    import_parser.add_argument("--file", required=True, help="CSV文件路径")
    
    export_parser = subparsers.add_parser("export", help="导出所有服务器映射关系到CSV文件")
    export_parser.add_argument("--file", required=True, help="输出CSV文件路径")
    
    clear_parser = subparsers.add_parser("clear", help="清除所有服务器映射关系")
    clear_parser.add_argument("--force", "-f", action="store_true", help="强制清除，不提示确认")
    
    info_parser = subparsers.add_parser("info", help="显示工具信息")
    info_parser.add_argument("--output", "-o", choices=["text", "json"], default="text",
                              help="输出格式 (默认: text)")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    command_map = {
        "add": cmd_add,
        "update": cmd_update,
        "delete": cmd_delete,
        "query": cmd_query,
        "batch-query": cmd_batch_query,
        "search": cmd_search,
        "list": cmd_list,
        "import": cmd_import,
        "export": cmd_export,
        "clear": cmd_clear,
        "info": cmd_info,
    }
    
    sys.exit(command_map[args.command](args))


if __name__ == "__main__":
    main()
