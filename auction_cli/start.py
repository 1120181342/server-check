#!/usr/bin/env python3
import sys
import os
import subprocess
import time

def print_header():
    print("="*60)
    print("                    🏷️  拍卖竞标系统 CLI版")
    print("="*60)
    print()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print_header()
    
    print("请选择您的角色:")
    print("1. 启动拍卖服务器")
    print("2. 以主持人身份连接")
    print("3. 以竞标者身份连接")
    print("4. 退出")
    print()
    
    choice = input("请选择 (1-4): ").strip()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable
    
    if choice == '1':
        server_path = os.path.join(script_dir, 'server.py')
        print(f"\n正在启动服务器...")
        print(f"服务器地址: localhost:9999")
        print(f"提示: 请在新终端中运行 host.py 或 bidder.py 连接服务器")
        print(f"按 Ctrl+C 停止服务器\n")
        subprocess.run([python_exe, server_path])
        
    elif choice == '2':
        host_path = os.path.join(script_dir, 'host.py')
        print(f"\n正在启动主持人客户端...")
        subprocess.run([python_exe, host_path])
        
    elif choice == '3':
        bidder_path = os.path.join(script_dir, 'bidder.py')
        print(f"\n正在启动竞标者客户端...")
        subprocess.run([python_exe, bidder_path])
        
    elif choice == '4':
        print("\n再见!")
        sys.exit(0)
    else:
        print("\n无效选择，请重新运行程序")
        time.sleep(2)
        main()

if __name__ == '__main__':
    main()
