#!/usr/bin/env python3
"""
Melon自动化项目设置脚本
"""

import os
import sys
import subprocess

def install_requirements():
    """安装项目依赖"""
    print("📦 安装项目依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def create_env_file():
    """创建环境变量文件"""
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} 已存在，跳过创建")
        return True
    
    print(f"📝 创建 {env_file} 文件...")
    
    # 获取用户输入
    username = input("请输入Melon用户名: ").strip()
    password = input("请输入Melon密码: ").strip()
    
    if not username or not password:
        print("❌ 用户名和密码不能为空")
        return False
    
    # 创建.env文件
    env_content = f"""# Melon登录信息
MELON_USERNAME={username}
MELON_PASSWORD={password}

# 浏览器设置
HEADLESS_MODE=False
WAIT_TIMEOUT=10
IMPLICIT_WAIT=5

# Session相关
SESSION_FILE=session_data.json
COOKIE_FILE=cookies.json
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ {env_file} 创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建 {env_file} 失败: {e}")
        return False

def main():
    """主函数"""
    print("🎵 Melon自动化项目设置 (Pyppeteer版)")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    
    # 安装依赖
    if not install_requirements():
        return False
    
    # 创建环境变量文件
    create_env = input("\n是否创建.env配置文件? (y/n): ").strip().lower()
    if create_env in ['y', 'yes', '是']:
        if not create_env_file():
            return False
    
    print("\n" + "=" * 50)
    print("🎉 设置完成!")
    print("\n💡 下一步:")
    print("   1. 确保已正确配置用户名和密码")
    print("   2. 运行: python main.py")
    print("   3. 或查看示例: python example.py")
    print("\n⚠️  重要提醒:")
    print("   - 本工具仅用于学习和研究")
    print("   - 请遵守网站使用条款")
    print("   - 不得用于违法用途")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  设置被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 设置过程中发生错误: {e}")
        sys.exit(1) 