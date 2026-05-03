#!/usr/bin/env python3
import sys
import os
import json
from typing import Optional, List, Tuple
from dataclasses import asdict

import click

from ip_mapper import IPMapper, CloudServer, is_valid_ipv4


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class ColorOutput:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    @classmethod
    def enable(cls):
        if os.name == "nt":
            os.system("color")
    
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


def get_mapper(data_file: Optional[str] = None) -> IPMapper:
    if data_file:
        return IPMapper(data_file)
    return IPMapper()


def format_server(server: CloudServer, format_type: str = "text", 
                  color: bool = True, index: Optional[int] = None) -> str:
    if format_type == "json":
        return json.dumps(asdict(server), ensure_ascii=False, indent=2)
    
    elif format_type == "csv":
        return f"{server.server_id},{server.ip},{server.user},{server.description}"
    
    else:
        idx_str = f"[{index}] " if index is not None else ""
        if color:
            return (
                f"{ColorOutput.cyan(idx_str)}"
                f"{ColorOutput.bold('服务器ID:')} {server.server_id}\n"
                f"  {ColorOutput.bold('IP地址:')} {server.ip}\n"
                f"  {ColorOutput.bold('所属用户:')} {server.user}\n"
                f"  {ColorOutput.bold('描述:')} {server.description or '-'}"
            )
        else:
            return (
                f"{idx_str}"
                f"服务器ID: {server.server_id}\n"
                f"  IP地址: {server.ip}\n"
                f"  所属用户: {server.user}\n"
                f"  描述: {server.description or '-'}"
            )


def format_server_list(servers: List[CloudServer], format_type: str = "text",
                       color: bool = True) -> List[str]:
    results = []
    for idx, server in enumerate(servers, 1):
        results.append(format_server(server, format_type, color, idx if len(servers) > 1 else None))
    return results


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="显示版本信息")
@click.option("--data-file", "-d", type=click.Path(), help="指定数据文件路径")
@click.pass_context
def cli(ctx: click.Context, version: bool, data_file: Optional[str]):
    """
    云资源池IP匹配工具 - 管理和查询云服务器IP映射关系
    
    功能特性:
    \b
      - 管理云服务器ID、IP地址、所属用户的映射关系
      - 支持根据IP快速查询对应的服务器信息
      - 支持批量导入/导出CSV文件
      - 支持多种输出格式: 文本、JSON、CSV
    
    示例:
    \b
      # 添加服务器
      ipmapper add --id "vm-001" --ip "192.168.1.10" --user "张三"
      
      # 根据IP查询服务器
      ipmapper query --ip "192.168.1.10"
      
      # 列出所有服务器
      ipmapper list
      
      # 从CSV导入
      ipmapper import --file servers.csv
      
      # 导出到CSV
      ipmapper export --file backup.csv
    """
    ctx.ensure_object(dict)
    ctx.obj["data_file"] = data_file
    
    if version:
        click.echo("IP Mapper v1.0.0")
        ctx.exit()
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command("add")
@click.option("--id", "server_id", required=True, help="服务器ID")
@click.option("--ip", required=True, help="服务器IP地址")
@click.option("--user", required=True, help="所属用户")
@click.option("--desc", "description", default="", help="描述信息")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def add_cmd(ctx: click.Context, server_id: str, ip: str, user: str, 
            description: str, no_color: bool, quiet: bool):
    """
    添加服务器映射关系
    
    示例:
    \b
      ipmapper add --id "vm-001" --ip "192.168.1.10" --user "张三"
      ipmapper add --id "vm-002" --ip "10.0.0.5" --user "李四" --desc "测试服务器"
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    if not is_valid_ipv4(ip):
        if not quiet:
            msg = f"错误: 无效的IP地址 '{ip}'"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)
    
    if mapper.add_server(server_id, ip, user, description):
        if not quiet:
            msg = f"成功: 已添加服务器 {server_id}"
            click.echo(ColorOutput.green(msg) if not no_color else msg)
    else:
        if not quiet:
            existing = mapper.get_server_by_id(server_id)
            if existing:
                msg = f"错误: 服务器ID '{server_id}' 已存在"
            else:
                msg = f"错误: IP地址 '{ip}' 已被使用"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)


@cli.command("update")
@click.option("--id", "server_id", required=True, help="服务器ID")
@click.option("--ip", help="新的IP地址")
@click.option("--user", help="新的所属用户")
@click.option("--desc", "description", help="新的描述信息")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def update_cmd(ctx: click.Context, server_id: str, ip: Optional[str], 
               user: Optional[str], description: Optional[str], 
               no_color: bool, quiet: bool):
    """
    更新服务器映射关系
    
    示例:
    \b
      ipmapper update --id "vm-001" --ip "192.168.1.20"
      ipmapper update --id "vm-001" --user "王五" --desc "生产服务器"
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    if ip is not None and not is_valid_ipv4(ip):
        if not quiet:
            msg = f"错误: 无效的IP地址 '{ip}'"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)
    
    if mapper.update_server(server_id, ip, user, description):
        if not quiet:
            msg = f"成功: 已更新服务器 {server_id}"
            click.echo(ColorOutput.green(msg) if not no_color else msg)
    else:
        if not quiet:
            existing = mapper.get_server_by_id(server_id)
            if not existing:
                msg = f"错误: 服务器ID '{server_id}' 不存在"
            elif ip is not None:
                msg = f"错误: IP地址 '{ip}' 已被其他服务器使用"
            else:
                msg = f"错误: 更新失败"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)


@cli.command("delete")
@click.option("--id", "server_id", help="服务器ID")
@click.option("--ip", help="服务器IP地址")
@click.option("--force", "-f", is_flag=True, help="强制删除，不提示确认")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def delete_cmd(ctx: click.Context, server_id: Optional[str], ip: Optional[str],
               force: bool, no_color: bool, quiet: bool):
    """
    删除服务器映射关系
    
    必须提供 --id 或 --ip 其中一个参数
    
    示例:
    \b
      ipmapper delete --id "vm-001"
      ipmapper delete --ip "192.168.1.10"
      ipmapper delete --id "vm-001" --force
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    if not server_id and not ip:
        if not quiet:
            msg = "错误: 必须提供 --id 或 --ip 参数"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)
    
    target_server = None
    if server_id:
        target_server = mapper.get_server_by_id(server_id)
    elif ip:
        target_server = mapper.get_server_by_ip(ip)
    
    if not target_server:
        if not quiet:
            if server_id:
                msg = f"错误: 服务器ID '{server_id}' 不存在"
            else:
                msg = f"错误: IP地址 '{ip}' 不存在"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)
    
    if not force and not quiet:
        click.echo(ColorOutput.yellow("即将删除以下服务器:") if not no_color else "即将删除以下服务器:")
        click.echo(format_server(target_server, color=not no_color))
        confirm = click.prompt("请输入 'yes' 确认删除", default="no")
        if confirm.lower() != "yes":
            click.echo("已取消删除")
            sys.exit(0)
    
    if mapper.delete_server(target_server.server_id):
        if not quiet:
            msg = f"成功: 已删除服务器 {target_server.server_id}"
            click.echo(ColorOutput.green(msg) if not no_color else msg)
    else:
        if not quiet:
            msg = "错误: 删除失败"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)


@cli.command("query")
@click.option("--ip", help="根据IP地址查询")
@click.option("--id", "server_id", help="根据服务器ID查询")
@click.option("--user", help="根据用户查询所有服务器")
@click.option("--output", "-o", type=click.Choice(["text", "json", "csv"]),
              default="text", help="输出格式 (默认: text)")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def query_cmd(ctx: click.Context, ip: Optional[str], server_id: Optional[str],
              user: Optional[str], output: str, no_color: bool, quiet: bool):
    """
    查询服务器映射关系
    
    必须提供 --ip、--id 或 --user 其中一个参数
    
    示例:
    \b
      # 根据IP查询
      ipmapper query --ip "192.168.1.10"
      
      # 根据ID查询
      ipmapper query --id "vm-001"
      
      # 查询用户所有服务器
      ipmapper query --user "张三"
      
      # JSON格式输出
      ipmapper query --ip "192.168.1.10" -o json
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    if not ip and not server_id and not user:
        if not quiet:
            msg = "错误: 必须提供 --ip、--id 或 --user 参数"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)
    
    servers: List[CloudServer] = []
    
    if ip:
        server = mapper.get_server_by_ip(ip)
        if server:
            servers.append(server)
    elif server_id:
        server = mapper.get_server_by_id(server_id)
        if server:
            servers.append(server)
    elif user:
        servers = mapper.get_servers_by_user(user)
    
    if not servers:
        if not quiet:
            if ip:
                msg = f"未找到IP地址 '{ip}' 对应的服务器"
            elif server_id:
                msg = f"未找到服务器ID '{server_id}'"
            else:
                msg = f"用户 '{user}' 没有服务器"
            click.echo(ColorOutput.yellow(msg) if not no_color else msg)
        sys.exit(0)
    
    results = format_server_list(servers, output, not no_color)
    
    for result in results:
        click.echo(result)


@cli.command("search")
@click.argument("keyword")
@click.option("--output", "-o", type=click.Choice(["text", "json", "csv"]),
              default="text", help="输出格式 (默认: text)")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def search_cmd(ctx: click.Context, keyword: str, output: str,
               no_color: bool, quiet: bool):
    """
    搜索服务器映射关系
    
    在服务器ID、IP地址、用户、描述中搜索关键词
    
    示例:
    \b
      ipmapper search "192.168"
      ipmapper search "张三"
      ipmapper search "测试"
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    servers = mapper.search_servers(keyword)
    
    if not servers:
        if not quiet:
            msg = f"未找到包含 '{keyword}' 的服务器"
            click.echo(ColorOutput.yellow(msg) if not no_color else msg)
        sys.exit(0)
    
    if not quiet:
        click.echo(f"找到 {len(servers)} 个匹配的服务器:\n")
    
    results = format_server_list(servers, output, not no_color)
    
    for result in results:
        click.echo(result)
        if output == "text" and len(results) > 1:
            click.echo()


@cli.command("list")
@click.option("--output", "-o", type=click.Choice(["text", "json", "csv"]),
              default="text", help="输出格式 (默认: text)")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def list_cmd(ctx: click.Context, output: str, no_color: bool, quiet: bool):
    """
    列出所有服务器映射关系
    
    示例:
    \b
      ipmapper list
      ipmapper list -o json
      ipmapper list -o csv
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    servers = mapper.get_all_servers()
    
    if not servers:
        if not quiet:
            msg = "当前没有任何服务器映射关系"
            click.echo(ColorOutput.yellow(msg) if not no_color else msg)
        sys.exit(0)
    
    if not quiet:
        click.echo(f"共 {len(servers)} 个服务器:\n")
    
    if output == "json":
        json_data = [asdict(server) for server in servers]
        click.echo(json.dumps(json_data, ensure_ascii=False, indent=2))
    elif output == "csv":
        click.echo("server_id,ip,user,description")
        for server in servers:
            click.echo(f"{server.server_id},{server.ip},{server.user},{server.description}")
    else:
        results = format_server_list(servers, "text", not no_color)
        for i, result in enumerate(results):
            click.echo(result)
            if i < len(results) - 1:
                click.echo()


@cli.command("import")
@click.option("--file", "csv_file", required=True, type=click.Path(exists=True),
              help="CSV文件路径")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def import_cmd(ctx: click.Context, csv_file: str, no_color: bool, quiet: bool):
    """
    从CSV文件批量导入服务器映射关系
    
    CSV文件格式要求:
    \b
      第一行: server_id,ip,user,description
      后续行: 具体数据
    
    示例:
    \b
      ipmapper import --file servers.csv
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    result = mapper.import_from_csv(csv_file)
    
    if not quiet:
        if result["errors"]:
            click.echo(ColorOutput.yellow("导入过程中出现以下错误:") if not no_color else "导入过程中出现以下错误:")
            for error in result["errors"]:
                click.echo(f"  - {error}")
            click.echo()
        
        click.echo(ColorOutput.green(f"导入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条") if not no_color 
                  else f"导入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")
    
    if result["success"] == 0 and result["failed"] > 0:
        sys.exit(1)


@cli.command("export")
@click.option("--file", "csv_file", required=True, type=click.Path(),
              help="输出CSV文件路径")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def export_cmd(ctx: click.Context, csv_file: str, no_color: bool, quiet: bool):
    """
    导出所有服务器映射关系到CSV文件
    
    示例:
    \b
      ipmapper export --file backup.csv
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    if mapper.export_to_csv(csv_file):
        if not quiet:
            msg = f"成功: 已导出到 {csv_file}"
            click.echo(ColorOutput.green(msg) if not no_color else msg)
    else:
        if not quiet:
            msg = f"错误: 导出失败"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)


@cli.command("clear")
@click.option("--force", "-f", is_flag=True, help="强制清除，不提示确认")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
@click.pass_context
def clear_cmd(ctx: click.Context, force: bool, no_color: bool, quiet: bool):
    """
    清除所有服务器映射关系
    
    示例:
    \b
      ipmapper clear
      ipmapper clear --force
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    if not force and not quiet:
        count = mapper.server_count
        if count == 0:
            click.echo("当前没有任何数据需要清除")
            sys.exit(0)
        
        msg = f"警告: 即将清除所有 {count} 条服务器映射关系"
        click.echo(ColorOutput.yellow(msg) if not no_color else msg)
        confirm = click.prompt("请输入 'yes' 确认清除", default="no")
        if confirm.lower() != "yes":
            click.echo("已取消清除")
            sys.exit(0)
    
    if mapper.clear_all():
        if not quiet:
            msg = "成功: 已清除所有数据"
            click.echo(ColorOutput.green(msg) if not no_color else msg)
    else:
        if not quiet:
            msg = "错误: 清除失败"
            click.echo(ColorOutput.red(msg) if not no_color else msg, err=True)
        sys.exit(1)


@cli.command("info")
@click.option("--output", "-o", type=click.Choice(["text", "json"]),
              default="text", help="输出格式 (默认: text)")
@click.option("--no-color", is_flag=True, help="禁用颜色输出")
@click.pass_context
def info_cmd(ctx: click.Context, output: str, no_color: bool):
    """
    显示工具信息
    
    示例:
    \b
      ipmapper info
      ipmapper info -o json
    """
    if not no_color:
        ColorOutput.enable()
    
    mapper = get_mapper(ctx.obj.get("data_file"))
    
    info_data = {
        "version": "1.0.0",
        "data_file": mapper.data_file,
        "server_count": mapper.server_count
    }
    
    if output == "json":
        click.echo(json.dumps(info_data, ensure_ascii=False, indent=2))
    else:
        click.echo(ColorOutput.bold("=" * 50) if not no_color else "=" * 50)
        click.echo(ColorOutput.cyan("IP Mapper 信息") if not no_color else "IP Mapper 信息")
        click.echo(ColorOutput.bold("=" * 50) if not no_color else "=" * 50)
        click.echo()
        click.echo(f"  版本: {info_data['version']}")
        click.echo(f"  数据文件: {info_data['data_file']}")
        click.echo(f"  服务器数量: {info_data['server_count']}")
        click.echo()
        click.echo("  支持的命令:")
        click.echo("    add      - 添加服务器")
        click.echo("    update   - 更新服务器")
        click.echo("    delete   - 删除服务器")
        click.echo("    query    - 查询服务器")
        click.echo("    search   - 搜索服务器")
        click.echo("    list     - 列出所有服务器")
        click.echo("    import   - 从CSV导入")
        click.echo("    export   - 导出到CSV")
        click.echo("    clear    - 清除所有数据")
        click.echo("    info     - 显示此信息")


if __name__ == "__main__":
    cli()
