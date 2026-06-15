"""
CLI - 命令行入口
用法: ai-cs [OPTIONS] COMMAND [ARGS]...
"""

import sys
import os
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_customer_service.core.plugin_manager import PluginManager
from ai_customer_service.core.config_manager import ConfigManager

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="ai-customer-service")
def cli():
    """AI客服系统 - 基于MCP协议的插件式客服系统"""
    pass


@cli.command()
@click.option("--host", default="localhost", help="服务器主机地址")
@click.option("--port", default=8000, help="服务器端口")
@click.option("--reload", is_flag=True, help="启用热重载")
def start(host, port, reload):
    """启动AI客服服务器"""
    import uvicorn
    from ai_customer_service.core.app import create_app

    console.print(f"[bold green]启动AI客服系统...[/bold green]")
    console.print(f"地址: http://{host}:{port}")
    console.print(f"API文档: http://{host}:{port}/docs")

    try:
        app = create_app()
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]服务器已停止[/yellow]")


@cli.command()
def init():
    """初始化配置文件"""
    console.print("[bold blue]初始化AI客服系统配置...[/bold blue]")

    config_manager = ConfigManager()
    config_manager.init_config_file()

    console.print("[bold green]配置文件已创建: .env[/bold green]")
    console.print("\n请编辑 .env 文件，配置您的API密钥:")


@cli.command()
def info():
    """显示系统信息"""
    from ai_customer_service import __version__

    table = Table(title="AI客服系统信息")
    table.add_column("项目", style="cyan")
    table.add_column("值", style="green")

    table.add_row("版本", __version__)
    table.add_row("Python", sys.version.split()[0])

    # 检查配置
    config_manager = ConfigManager()
    api_key = config_manager.get("openai_api_key", "")
    if api_key and api_key != "your-api-key-here":
        api_status = "[green]已配置[/green]"
    else:
        api_status = "[yellow]未配置 (使用模拟模式)[/yellow]"

    table.add_row("API密钥", api_status)

    console.print(table)


@cli.command()
def plugins():
    """列出所有可用插件"""
    plugin_manager = PluginManager()
    plugin_manager.discover_plugins()

    available_plugins = plugin_manager.list_plugins()

    if not available_plugins:
        console.print("[yellow]未发现任何插件[/yellow]")
        return

    table = Table(title=f"可用插件 ({len(available_plugins)})")
    table.add_column("名称", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("描述", style="white")

    for name in available_plugins:
        status = plugin_manager.plugin_status.get(name, "unknown")
        status_color = "green" if status == "running" else "yellow"
        table.add_row(name, f"[{status_color}]{status}[/{status_color}]", "")

    console.print(table)


@cli.command()
@click.argument("plugin_name")
def enable(plugin_name):
    """启用指定插件"""
    plugin_manager = PluginManager()
    if plugin_manager.enable_plugin(plugin_name):
        console.print(f"[green]插件 {plugin_name} 已启用[/green]")
    else:
        console.print(f"[red]插件 {plugin_name} 启用失败[/red]")


@cli.command()
@click.argument("plugin_name")
def disable(plugin_name):
    """禁用指定插件"""
    plugin_manager = PluginManager()
    if plugin_manager.disable_plugin(plugin_name):
        console.print(f"[yellow]插件 {plugin_name} 已禁用[/yellow]")
    else:
        console.print(f"[red]插件 {plugin_name} 禁用失败[/red]")


@cli.command()
def doctor():
    """诊断系统状态"""
    console.print("[bold blue]系统诊断...[/bold blue]\n")

    issues = []
    successes = []

    # 检查Python版本
    if sys.version_info >= (3, 9):
        successes.append(f"Python版本: {sys.version.split()[0]}")
    else:
        issues.append(f"需要Python 3.9+，当前: {sys.version.split()[0]}")

    # 检查依赖
    required_packages = [
        "fastapi", "uvicorn", "langchain",
        "langchain_openai", "pydantic", "click", "rich"
    ]
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
            successes.append(f"{pkg}: 已安装")
        except ImportError:
            issues.append(f"{pkg}: 未安装")

    # 检查配置
    config_manager = ConfigManager()
    api_key = config_manager.get("openai_api_key", "")
    if not api_key or api_key == "your-api-key-here":
        issues.append("OpenAI API密钥未配置 (系统将使用模拟模式)")
    else:
        successes.append("API密钥: 已配置")

    # 显示结果
    if successes:
        console.print("[bold green]检查通过:[/bold green]")
        for s in successes:
            console.print(f"  [OK] {s}")

    if issues:
        console.print("\n[bold red]发现问题:[/bold red]")
        for issue in issues:
            console.print(f"  [X] {issue}")
        console.print("\n运行 [cyan]ai-cs init[/cyan] 初始化配置")

    if not issues:
        console.print("\n[bold green]所有检查通过! 可以运行 ai-cs start 启动系统[/bold green]")


def main():
    """CLI主入口"""
    cli()


if __name__ == "__main__":
    main()
