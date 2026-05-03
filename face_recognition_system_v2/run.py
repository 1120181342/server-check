import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app import app, init_components


def main():
    print("=" * 50)
    print("  公司人脸识别系统 v2.0")
    print("  优化版: 高性能 · 高稳定性")
    print("=" * 50)
    print()
    
    config = Config()
    
    print(f"  配置信息:")
    print(f"  - 数据目录: {config.DATA_DIR}")
    print(f"  - 数据库: {config.DATABASE_PATH}")
    print(f"  - 端口: {config.PORT}")
    print(f"  - 调试模式: {'开启' if config.DEBUG else '关闭'}")
    print()
    
    print(f"  性能优化:")
    print(f"  - 帧降采样因子: {config.PERFORMANCE.frame_downscale_factor}")
    print(f"  - 跳帧检测: {config.PERFORMANCE.skip_frames} 帧")
    print(f"  - 识别工作线程: {config.PERFORMANCE.max_recognition_workers}")
    print(f"  - 数据库连接池: {config.PERFORMANCE.db_connection_pool_size}")
    print()
    
    print(f"  稳定性保障:")
    print(f"  - 熔断器阈值: {config.STABILITY.circuit_breaker_threshold} 次失败")
    print(f"  - 熔断器恢复超时: {config.STABILITY.circuit_breaker_timeout} 秒")
    print(f"  - 健康检查间隔: {config.STABILITY.health_check_interval} 秒")
    print()
    
    print("  正在初始化组件...")
    init_components()
    print("  组件初始化完成!")
    print()
    
    print("=" * 50)
    print(f"  服务启动: http://{config.HOST}:{config.PORT}")
    print("=" * 50)
    print()
    
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT, threaded=True)


if __name__ == '__main__':
    main()
