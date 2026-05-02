from app import app, reload_face_encodings

if __name__ == '__main__':
    print("=" * 50)
    print("公司人脸识别系统启动中...")
    print("=" * 50)
    print()
    
    print("[初始化] 加载人脸数据库...")
    count = reload_face_encodings()
    print(f"[初始化] 已加载 {count} 个人脸数据")
    
    print()
    print("[系统] 服务即将启动...")
    print("[系统] 访问地址: http://localhost:5000")
    print("[系统] 按 Ctrl+C 停止服务")
    print()
    print("=" * 50)
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
