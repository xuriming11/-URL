"""
启动脚本
快速启动AI客服系统
"""

import sys
import os
import subprocess
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "langchain",
        "langchain-openai",
        "python-dotenv",
        "websockets",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"[OK] {package}")
        except ImportError:
            print(f"[X] {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n缺少依赖包，正在安装...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt"
        ])
        print("依赖安装完成")
    
    return True


def check_env_file():
    """检查环境配置文件"""
    print("\n检查环境配置...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("未找到.env文件，从.env.example复制...")
            subprocess.run(["copy", ".env.example", ".env"], shell=True)
            print("[OK] .env文件已创建")
            print("[!] 请编辑.env文件，配置您的API密钥")
        else:
            print("[X] 未找到.env和.env.example文件")
            return False
    else:
        print("[OK] .env文件存在")
    
    return True


def start_server():
    """启动服务器"""
    print("\n启动AI客服系统...")
    
    try:
        # 使用uvicorn启动
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--reload",
            "--host", "localhost",
            "--port", "8000"
        ])
        
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("AI客服插件系统启动脚本")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("依赖检查失败")
        return
    
    # 检查环境配置
    if not check_env_file():
        print("环境配置检查失败")
        return
    
    # 启动服务器
    print("\n准备启动服务器...")
    print("访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("=" * 50)
    
    start_server()


if __name__ == "__main__":
    main()