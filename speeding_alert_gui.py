#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车载超速提示系统 - GUI版本
提供直观的图形界面交互，包括：
1. 实时速度显示
2. 限速显示
3. 超速警告视觉效果
4. 系统控制
5. 性能指标显示
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
import sys
import os

# 确保能导入核心模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from speeding_alert_system import (
    SpeedingAlertSystem,
    SpeedData,
    SpeedLimit,
    AlertInfo
)


class SpeedometerCanvas(tk.Canvas):
    """
    速度仪表盘组件
    提供直观的速度显示
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_speed = 0
        self.speed_limit = 60
        self.is_speeding = False
        
        # 设置背景
        self.configure(bg='#2d2d2d', highlightthickness=0)
        
        # 绑定尺寸变化事件
        self.bind('<Configure>', self._on_resize)
        
        # 初始绘制
        self._draw_speedometer()
    
    def _on_resize(self, event):
        """窗口尺寸变化时重绘"""
        self._draw_speedometer()
    
    def _draw_speedometer(self):
        """绘制速度仪表盘"""
        self.delete('all')
        
        # 获取窗口尺寸
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        # 计算中心和半径
        center_x = width // 2
        center_y = height // 2
        radius = min(center_x, center_y) - 30
        
        # 绘制背景圆环
        self.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill='#1e1e1e', outline='#444444', width=3
        )
        
        # 绘制刻度
        max_speed = 150
        scale_range = 240  # 刻度范围（角度）
        start_angle = -30  # 起始角度
        
        # 主刻度
        for i in range(0, max_speed + 1, 20):
            angle = start_angle + (i / max_speed) * scale_range
            angle_rad = math.radians(angle)
            
            # 刻度线
            outer_r = radius - 5
            inner_r = radius - 20
            
            x1 = center_x + outer_r * math.cos(angle_rad)
            y1 = center_y - outer_r * math.sin(angle_rad)
            x2 = center_x + inner_r * math.cos(angle_rad)
            y2 = center_y - inner_r * math.sin(angle_rad)
            
            # 超过限速的刻度用红色
            if i > self.speed_limit:
                color = '#ff4444'
            else:
                color = '#888888'
            
            self.create_line(x1, y1, x2, y2, fill=color, width=2)
            
            # 刻度标签
            label_r = radius - 35
            x_label = center_x + label_r * math.cos(angle_rad)
            y_label = center_y - label_r * math.sin(angle_rad)
            
            self.create_text(
                x_label, y_label,
                text=str(i),
                fill='#aaaaaa',
                font=('Arial', 10, 'bold')
            )
        
        # 次刻度
        for i in range(0, max_speed + 1, 10):
            if i % 20 == 0:
                continue
            
            angle = start_angle + (i / max_speed) * scale_range
            angle_rad = math.radians(angle)
            
            outer_r = radius - 5
            inner_r = radius - 12
            
            x1 = center_x + outer_r * math.cos(angle_rad)
            y1 = center_y - outer_r * math.sin(angle_rad)
            x2 = center_x + inner_r * math.cos(angle_rad)
            y2 = center_y - inner_r * math.sin(angle_rad)
            
            if i > self.speed_limit:
                color = '#ff6666'
            else:
                color = '#666666'
            
            self.create_line(x1, y1, x2, y2, fill=color, width=1)
        
        # 绘制限速线
        limit_angle = start_angle + (self.speed_limit / max_speed) * scale_range
        limit_angle_rad = math.radians(limit_angle)
        
        # 红色区域标记
        for angle in range(int(limit_angle), int(start_angle + scale_range) + 1, 2):
            angle_rad = math.radians(angle)
            outer_r = radius - 8
            inner_r = radius - 15
            
            x1 = center_x + outer_r * math.cos(angle_rad)
            y1 = center_y - outer_r * math.sin(angle_rad)
            x2 = center_x + inner_r * math.cos(angle_rad)
            y2 = center_y - inner_r * math.sin(angle_rad)
            
            self.create_line(x1, y1, x2, y2, fill='#ff4444', width=2, stipple='gray25')
        
        # 绘制指针
        speed_angle = start_angle + (self.current_speed / max_speed) * scale_range
        speed_angle_rad = math.radians(speed_angle)
        
        # 指针颜色
        if self.is_speeding:
            pointer_color = '#ff0000'
        else:
            pointer_color = '#00ff00'
        
        # 指针主体
        pointer_length = radius - 40
        pointer_end_x = center_x + pointer_length * math.cos(speed_angle_rad)
        pointer_end_y = center_y - pointer_length * math.sin(speed_angle_rad)
        
        # 指针尾部（短一点）
        tail_length = 15
        tail_angle_rad = math.radians(speed_angle + 180)
        tail_end_x = center_x + tail_length * math.cos(tail_angle_rad)
        tail_end_y = center_y - tail_length * math.sin(tail_angle_rad)
        
        # 绘制指针
        self.create_line(
            tail_end_x, tail_end_y, pointer_end_x, pointer_end_y,
            fill=pointer_color, width=3, capstyle='round'
        )
        
        # 中心圆点
        self.create_oval(
            center_x - 10, center_y - 10,
            center_x + 10, center_y + 10,
            fill=pointer_color, outline='#ffffff', width=2
        )
        
        # 速度数值显示
        self.create_text(
            center_x, center_y + 60,
            text=f"{self.current_speed:.0f}",
            fill='#ffffff',
            font=('Arial', 48, 'bold')
        )
        
        self.create_text(
            center_x, center_y + 90,
            text="km/h",
            fill='#888888',
            font=('Arial', 14)
        )
        
        # 超速警告标识
        if self.is_speeding:
            # 闪烁效果
            if int(time.time() * 5) % 2 == 0:
                warning_text = "⚠ 超速警告!"
                self.create_text(
                    center_x, center_y + 120,
                    text=warning_text,
                    fill='#ff0000',
                    font=('Arial', 16, 'bold')
                )


import math


class AlertIndicator(tk.Frame):
    """
    警告指示器组件
    显示超速警告的视觉效果
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.is_alerting = False
        self.alert_start_time = None
        self.alert_duration = 3.0
        
        # 设置样式
        self.configure(bg='#1e1e1e')
        
        # 创建UI组件
        self._create_widgets()
        
        # 启动更新定时器
        self._update_indicator()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 警告图标区域
        self.icon_frame = tk.Frame(self, bg='#1e1e1e')
        self.icon_frame.pack(pady=10)
        
        # 警告灯（圆形）
        self.warning_light = tk.Canvas(
            self.icon_frame,
            width=80, height=80,
            bg='#1e1e1e', highlightthickness=0
        )
        self.warning_light.pack()
        
        # 初始绘制
        self._draw_light('#333333')
        
        # 警告文本
        self.alert_text = tk.Label(
            self,
            text="系统正常",
            font=('Arial', 14, 'bold'),
            fg='#00ff00',
            bg='#1e1e1e'
        )
        self.alert_text.pack(pady=5)
        
        # 提示倒计时
        self.countdown_label = tk.Label(
            self,
            text="",
            font=('Arial', 12),
            fg='#ffaa00',
            bg='#1e1e1e'
        )
        self.countdown_label.pack(pady=5)
    
    def _draw_light(self, color):
        """绘制警告灯"""
        self.warning_light.delete('all')
        
        # 外圆
        self.warning_light.create_oval(
            5, 5, 75, 75,
            fill=color,
            outline='#555555',
            width=3
        )
        
        # 内圆（高光效果）
        self.warning_light.create_oval(
            15, 15, 65, 65,
            fill=color,
            outline='',
            stipple='gray50'
        )
    
    def start_alert(self, duration: float = 3.0):
        """开始警告"""
        self.is_alerting = True
        self.alert_start_time = time.time()
        self.alert_duration = duration
    
    def stop_alert(self):
        """停止警告"""
        self.is_alerting = False
        self.alert_start_time = None
    
    def _update_indicator(self):
        """更新指示器状态"""
        if self.is_alerting and self.alert_start_time:
            elapsed = time.time() - self.alert_start_time
            remaining = max(0, self.alert_duration - elapsed)
            
            if remaining > 0:
                # 闪烁效果
                if int(time.time() * 5) % 2 == 0:
                    self._draw_light('#ff0000')
                    self.alert_text.configure(fg='#ff0000', text="⚠ 超速警告!")
                else:
                    self._draw_light('#ff4444')
                    self.alert_text.configure(fg='#ff4444', text="⚠ 超速警告!")
                
                self.countdown_label.configure(text=f"提示剩余: {remaining:.1f} 秒")
            else:
                self.stop_alert()
        else:
            self._draw_light('#333333')
            self.alert_text.configure(fg='#00ff00', text="系统正常")
            self.countdown_label.configure(text="")
        
        # 每100ms更新一次
        self.after(100, self._update_indicator)


class SpeedLimitDisplay(tk.Frame):
    """
    速度限制显示组件
    显示当前限速信息
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.speed_limit = 60
        self.location = "未知位置"
        self.is_temporary = False
        
        # 设置样式
        self.configure(bg='#2d2d2d')
        
        # 创建UI组件
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 限速标志（圆形，类似真实的限速标志）
        self.sign_canvas = tk.Canvas(
            self,
            width=100, height=100,
            bg='#2d2d2d', highlightthickness=0
        )
        self.sign_canvas.pack(pady=10)
        
        # 位置标签
        self.location_label = tk.Label(
            self,
            text=f"位置: {self.location}",
            font=('Arial', 10),
            fg='#aaaaaa',
            bg='#2d2d2d'
        )
        self.location_label.pack(pady=5)
        
        # 临时限速标识
        self.temp_label = tk.Label(
            self,
            text="",
            font=('Arial', 10, 'bold'),
            fg='#ffaa00',
            bg='#2d2d2d'
        )
        self.temp_label.pack(pady=2)
        
        # 初始绘制
        self._draw_speed_limit_sign()
    
    def _draw_speed_limit_sign(self):
        """绘制限速标志"""
        self.sign_canvas.delete('all')
        
        # 白色圆形背景（红圈白底黑字）
        self.sign_canvas.create_oval(
            10, 10, 90, 90,
            fill='#ffffff',
            outline='#ff0000',
            width=8
        )
        
        # 限速数值
        self.sign_canvas.create_text(
            50, 50,
            text=str(int(self.speed_limit)),
            fill='#000000',
            font=('Arial', 32, 'bold')
        )
    
    def update_limit(self, speed_limit: float, location: str, is_temporary: bool = False):
        """更新限速信息"""
        self.speed_limit = speed_limit
        self.location = location
        self.is_temporary = is_temporary
        
        # 更新显示
        self._draw_speed_limit_sign()
        self.location_label.configure(text=f"位置: {location}")
        
        if is_temporary:
            self.temp_label.configure(text="(临时限速)")
        else:
            self.temp_label.configure(text="")


class PerformanceDisplay(tk.Frame):
    """
    性能指标显示组件
    显示系统性能数据
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 设置样式
        self.configure(bg='#2d2d2d')
        
        # 创建UI组件
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 标题
        title_label = tk.Label(
            self,
            text="性能指标",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d'
        )
        title_label.pack(pady=5)
        
        # 性能指标框架
        metrics_frame = tk.Frame(self, bg='#2d2d2d')
        metrics_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # 定义性能指标
        self.metrics = {
            "speed_check_count": {"label": "速度检查次数", "value": 0, "unit": "次"},
            "overspeed_count": {"label": "超速检测次数", "value": 0, "unit": "次"},
            "avg_response_time_ms": {"label": "平均响应时间", "value": 0, "unit": "ms"},
            "max_response_time_ms": {"label": "最大响应时间", "value": 0, "unit": "ms"},
            "min_response_time_ms": {"label": "最小响应时间", "value": 0, "unit": "ms"}
        }
        
        self.metric_labels = {}
        
        # 创建指标显示
        for i, (key, info) in enumerate(self.metrics.items()):
            row = i // 2
            col = i % 2
            
            # 指标框架
            metric_frame = tk.Frame(metrics_frame, bg='#3a3a3a', padx=10, pady=5)
            metric_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # 标签
            label = tk.Label(
                metric_frame,
                text=info["label"],
                font=('Arial', 9),
                fg='#aaaaaa',
                bg='#3a3a3a'
            )
            label.pack(anchor='w')
            
            # 值
            value_label = tk.Label(
                metric_frame,
                text=f"{info['value']} {info['unit']}",
                font=('Arial', 11, 'bold'),
                fg='#00ff00',
                bg='#3a3a3a'
            )
            value_label.pack(anchor='w')
            
            self.metric_labels[key] = value_label
        
        # 配置网格权重
        for i in range(3):
            metrics_frame.grid_rowconfigure(i, weight=1)
        for i in range(2):
            metrics_frame.grid_columnconfigure(i, weight=1)
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """更新性能指标"""
        for key, info in self.metrics.items():
            if key in metrics:
                value = metrics[key]
                
                # 格式化显示
                if key in ["avg_response_time_ms", "max_response_time_ms", "min_response_time_ms"]:
                    if value == float('inf'):
                        display_text = f"无数据 {info['unit']}"
                    else:
                        display_text = f"{value:.3f} {info['unit']}"
                else:
                    display_text = f"{value} {info['unit']}"
                
                # 更新标签
                self.metric_labels[key].configure(text=display_text)
                
                # 根据值设置颜色
                if key in ["avg_response_time_ms", "max_response_time_ms"]:
                    if value < 100:
                        color = '#00ff00'  # 绿色 - 优秀
                    elif value < 500:
                        color = '#ffaa00'  # 黄色 - 良好
                    else:
                        color = '#ff4444'  # 红色 - 警告
                    self.metric_labels[key].configure(fg=color)


class LogDisplay(tk.Frame):
    """
    日志显示组件
    显示系统日志和事件
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 设置样式
        self.configure(bg='#2d2d2d')
        
        # 创建UI组件
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 标题
        title_label = tk.Label(
            self,
            text="系统日志",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d'
        )
        title_label.pack(pady=5)
        
        # 文本区域
        self.log_text = scrolledtext.ScrolledText(
            self,
            height=8,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#cccccc',
            insertbackground='#ffffff',
            state='disabled'
        )
        self.log_text.pack(pady=5, padx=10, fill='both', expand=True)
        
        # 配置颜色标签
        self.log_text.tag_configure('info', foreground='#00aaff')
        self.log_text.tag_configure('warning', foreground='#ffaa00')
        self.log_text.tag_configure('error', foreground='#ff4444')
        self.log_text.tag_configure('success', foreground='#00ff00')
        self.log_text.tag_configure('timestamp', foreground='#666666')
    
    def add_log(self, message: str, level: str = 'info'):
        """添加日志条目"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 启用编辑
        self.log_text.configure(state='normal')
        
        # 添加时间戳
        self.log_text.insert('end', f'[{timestamp}] ', 'timestamp')
        
        # 添加消息
        self.log_text.insert('end', f'{message}\n', level)
        
        # 滚动到底部
        self.log_text.see('end')
        
        # 禁用编辑
        self.log_text.configure(state='disabled')


class SpeedingAlertGUI:
    """
    超速提示系统主GUI类
    整合所有组件，提供完整的用户界面
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("车载超速提示系统")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # 系统实例
        self.system: Optional[SpeedingAlertSystem] = None
        self.is_system_running = False
        
        # 监控线程
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitor_event = threading.Event()
        
        # 创建UI
        self._create_menu()
        self._create_main_layout()
        
        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 初始化系统
        self._initialize_system()
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="启动系统", command=self._start_system)
        file_menu.add_command(label="停止系统", command=self._stop_system)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="设置模拟速度", command=self._open_speed_dialog)
        settings_menu.add_command(label="设置速度限制", command=self._open_limit_dialog)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_main_layout(self):
        """创建主布局"""
        # 主框架
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 顶部状态栏
        self._create_status_bar(main_frame)
        
        # 中间内容区
        content_frame = tk.Frame(main_frame, bg='#1e1e1e')
        content_frame.pack(fill='both', expand=True, pady=10)
        
        # 左侧：速度仪表盘
        left_frame = tk.Frame(content_frame, bg='#2d2d2d', padx=10, pady=10)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # 仪表盘标题
        speedometer_title = tk.Label(
            left_frame,
            text="当前速度",
            font=('Arial', 14, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d'
        )
        speedometer_title.pack(pady=5)
        
        # 速度仪表盘
        self.speedometer = SpeedometerCanvas(left_frame, width=300, height=300)
        self.speedometer.pack(pady=10, fill='both', expand=True)
        
        # 中间：警告指示器和限速显示
        center_frame = tk.Frame(content_frame, bg='#1e1e1e', padx=10)
        center_frame.pack(side='left', fill='both')
        
        # 警告指示器
        alert_frame = tk.LabelFrame(
            center_frame,
            text="警告状态",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d',
            padx=10,
            pady=10
        )
        alert_frame.pack(fill='x', pady=10)
        
        self.alert_indicator = AlertIndicator(alert_frame)
        self.alert_indicator.pack(fill='x')
        
        # 限速显示
        limit_frame = tk.LabelFrame(
            center_frame,
            text="速度限制",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d',
            padx=10,
            pady=10
        )
        limit_frame.pack(fill='x', pady=10)
        
        self.speed_limit_display = SpeedLimitDisplay(limit_frame)
        self.speed_limit_display.pack(fill='x')
        
        # 右侧：控制按钮和性能指标
        right_frame = tk.Frame(content_frame, bg='#2d2d2d', padx=10, pady=10)
        right_frame.pack(side='right', fill='both')
        
        # 控制按钮区域
        control_frame = tk.LabelFrame(
            right_frame,
            text="系统控制",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d',
            padx=10,
            pady=10
        )
        control_frame.pack(fill='x', pady=10)
        
        # 启动按钮
        self.start_button = tk.Button(
            control_frame,
            text="启动系统",
            font=('Arial', 12, 'bold'),
            bg='#00aa00',
            fg='#ffffff',
            padx=20,
            pady=10,
            command=self._start_system
        )
        self.start_button.pack(fill='x', pady=5)
        
        # 停止按钮
        self.stop_button = tk.Button(
            control_frame,
            text="停止系统",
            font=('Arial', 12, 'bold'),
            bg='#aa0000',
            fg='#ffffff',
            padx=20,
            pady=10,
            command=self._stop_system,
            state='disabled'
        )
        self.stop_button.pack(fill='x', pady=5)
        
        # 测试按钮区域
        test_frame = tk.LabelFrame(
            right_frame,
            text="测试功能",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d',
            padx=10,
            pady=10
        )
        test_frame.pack(fill='x', pady=10)
        
        # 设置速度按钮
        tk.Button(
            test_frame,
            text="设置模拟速度",
            font=('Arial', 10),
            bg='#0066aa',
            fg='#ffffff',
            padx=10,
            pady=5,
            command=self._open_speed_dialog
        ).pack(fill='x', pady=3)
        
        # 设置限速按钮
        tk.Button(
            test_frame,
            text="设置速度限制",
            font=('Arial', 10),
            bg='#0066aa',
            fg='#ffffff',
            padx=10,
            pady=5,
            command=self._open_limit_dialog
        ).pack(fill='x', pady=3)
        
        # 快速测试按钮
        quick_test_frame = tk.Frame(test_frame, bg='#2d2d2d')
        quick_test_frame.pack(fill='x', pady=5)
        
        tk.Button(
            quick_test_frame,
            text="正常速度\n(55 km/h)",
            font=('Arial', 9),
            bg='#008800',
            fg='#ffffff',
            padx=5,
            pady=5,
            command=lambda: self._quick_set_speed(55.0)
        ).pack(side='left', fill='x', expand=True, padx=2)
        
        tk.Button(
            quick_test_frame,
            text="超速\n(75 km/h)",
            font=('Arial', 9),
            bg='#aa0000',
            fg='#ffffff',
            padx=5,
            pady=5,
            command=lambda: self._quick_set_speed(75.0)
        ).pack(side='left', fill='x', expand=True, padx=2)
        
        # 性能指标
        self.performance_display = PerformanceDisplay(right_frame)
        self.performance_display.pack(fill='x', pady=10)
        
        # 底部日志区域
        log_frame = tk.LabelFrame(
            main_frame,
            text="系统日志",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d',
            padx=10,
            pady=10
        )
        log_frame.pack(fill='x', pady=10)
        
        self.log_display = LogDisplay(log_frame, height=6)
        self.log_display.pack(fill='x')
    
    def _create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg='#333333', padx=10, pady=5)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # 系统状态
        self.status_label = tk.Label(
            status_frame,
            text="系统状态: 未启动",
            font=('Arial', 10),
            fg='#ff4444',
            bg='#333333'
        )
        self.status_label.pack(side='left')
        
        # 连接状态
        self.connection_label = tk.Label(
            status_frame,
            text="| 车辆连接: 未连接",
            font=('Arial', 10),
            fg='#ff4444',
            bg='#333333'
        )
        self.connection_label.pack(side='left', padx=10)
        
        # 当前时间
        self.time_label = tk.Label(
            status_frame,
            text="",
            font=('Arial', 10),
            fg='#aaaaaa',
            bg='#333333'
        )
        self.time_label.pack(side='right')
        
        # 启动时间更新
        self._update_time()
    
    def _update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.time_label.configure(text=current_time)
        # 每秒更新一次
        self.root.after(1000, self._update_time)
    
    def _initialize_system(self):
        """初始化系统"""
        try:
            self.system = SpeedingAlertSystem(
                vehicle_id="GUI-001",
                initial_speed_limit=60.0,
                alert_duration=3.0
            )
            
            # 注册回调
            self.system.alert_manager.register_alert_callback("gui", self._on_alert_event)
            self.system.limit_monitor.register_limit_change_callback("gui", self._on_limit_change)
            
            self.log_display.add_log("系统初始化成功", 'success')
            
        except Exception as e:
            self.log_display.add_log(f"系统初始化失败: {e}", 'error')
            messagebox.showerror("错误", f"系统初始化失败:\n{e}")
    
    def _start_system(self):
        """启动系统"""
        if not self.system:
            messagebox.showerror("错误", "系统未初始化")
            return
        
        if self.is_system_running:
            messagebox.showinfo("提示", "系统已经在运行中")
            return
        
        try:
            # 启动系统
            self.system.start()
            self.is_system_running = True
            
            # 更新UI状态
            self._update_ui_state(True)
            
            # 启动监控线程
            self.stop_monitor_event.clear()
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.log_display.add_log("系统启动成功", 'success')
            
        except Exception as e:
            self.log_display.add_log(f"系统启动失败: {e}", 'error')
            messagebox.showerror("错误", f"系统启动失败:\n{e}")
    
    def _stop_system(self):
        """停止系统"""
        if not self.system:
            return
        
        if not self.is_system_running:
            messagebox.showinfo("提示", "系统尚未启动")
            return
        
        try:
            # 停止监控线程
            self.stop_monitor_event.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
            
            # 停止系统
            self.system.stop()
            self.is_system_running = False
            
            # 更新UI状态
            self._update_ui_state(False)
            
            # 停止警告
            self.alert_indicator.stop_alert()
            
            self.log_display.add_log("系统已停止", 'info')
            
        except Exception as e:
            self.log_display.add_log(f"系统停止失败: {e}", 'error')
    
    def _update_ui_state(self, running: bool):
        """更新UI状态"""
        if running:
            self.status_label.configure(text="系统状态: 运行中", fg='#00ff00')
            self.connection_label.configure(text="| 车辆连接: 已连接", fg='#00ff00')
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
        else:
            self.status_label.configure(text="系统状态: 已停止", fg='#ff4444')
            self.connection_label.configure(text="| 车辆连接: 未连接", fg='#ff4444')
            self.start_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
    
    def _monitor_loop(self):
        """监控循环"""
        while not self.stop_monitor_event.is_set():
            try:
                if self.system and self.is_system_running:
                    # 获取系统状态
                    status = self.system.get_system_status()
                    
                    # 更新仪表盘
                    if status['current_speed'] is not None:
                        self.speedometer.current_speed = status['current_speed']
                        self.speedometer.speed_limit = status['speed_limit']
                        self.speedometer.is_speeding = status['current_speed'] > status['speed_limit']
                        
                        # 触发重绘
                        self.root.after(0, self.speedometer._draw_speedometer)
                    
                    # 更新性能指标
                    self.root.after(0, lambda: self.performance_display.update_metrics(
                        status['performance_metrics']
                    ))
                    
                    # 检查活跃提示
                    if status['active_alert']:
                        self.root.after(0, lambda: self.alert_indicator.start_alert(3.0))
                
            except Exception as e:
                print(f"监控循环错误: {e}")
            
            # 每100ms更新一次
            time.sleep(0.1)
    
    def _on_alert_event(self, alert_info: AlertInfo, event_type: str):
        """提示事件回调"""
        if event_type == "start":
            self.log_display.add_log(
                f"超速警告! 速度: {alert_info.current_speed:.1f} km/h, 限速: {alert_info.speed_limit:.1f} km/h",
                'warning'
            )
        elif event_type == "end":
            self.log_display.add_log("提示已结束", 'info')
    
    def _on_limit_change(self, speed_limit: SpeedLimit):
        """限速变化回调"""
        temp_text = " (临时限速)" if speed_limit.is_temporary else ""
        self.log_display.add_log(
            f"限速更新: {speed_limit.limit} km/h - {speed_limit.location}{temp_text}",
            'info'
        )
        
        # 更新限速显示
        self.root.after(0, lambda: self.speed_limit_display.update_limit(
            speed_limit.limit,
            speed_limit.location,
            speed_limit.is_temporary
        ))
        
        # 更新仪表盘的限速
        self.speedometer.speed_limit = speed_limit.limit
    
    def _open_speed_dialog(self):
        """打开设置速度对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置模拟速度")
        dialog.geometry("300x150")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_reqwidth()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 标签
        tk.Label(
            dialog,
            text="请输入模拟速度 (km/h):",
            font=('Arial', 11),
            fg='#ffffff',
            bg='#2d2d2d'
        ).pack(pady=20)
        
        # 输入框
        speed_var = tk.StringVar(value="55.0")
        speed_entry = tk.Entry(
            dialog,
            textvariable=speed_var,
            font=('Arial', 14),
            justify='center',
            width=15
        )
        speed_entry.pack(pady=10)
        
        # 按钮框架
        button_frame = tk.Frame(dialog, bg='#2d2d2d')
        button_frame.pack(pady=10)
        
        def apply_speed():
            try:
                speed = float(speed_var.get())
                if 0 <= speed <= 200:
                    if self.system:
                        self.system.set_simulated_speed(speed)
                        self.log_display.add_log(f"已设置模拟速度: {speed} km/h", 'info')
                    dialog.destroy()
                else:
                    messagebox.showwarning("警告", "速度值应在0-200之间")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        tk.Button(
            button_frame,
            text="确定",
            font=('Arial', 10),
            bg='#008800',
            fg='#ffffff',
            padx=20,
            command=apply_speed
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="取消",
            font=('Arial', 10),
            bg='#880000',
            fg='#ffffff',
            padx=20,
            command=dialog.destroy
        ).pack(side='left', padx=10)
    
    def _open_limit_dialog(self):
        """打开设置限速对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置速度限制")
        dialog.geometry("350x250")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_reqwidth()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 限速输入
        tk.Label(
            dialog,
            text="速度限制 (km/h):",
            font=('Arial', 11),
            fg='#ffffff',
            bg='#2d2d2d'
        ).pack(pady=(20, 5))
        
        limit_var = tk.StringVar(value="60.0")
        limit_entry = tk.Entry(
            dialog,
            textvariable=limit_var,
            font=('Arial', 14),
            justify='center',
            width=15
        )
        limit_entry.pack(pady=5)
        
        # 位置输入
        tk.Label(
            dialog,
            text="位置描述:",
            font=('Arial', 11),
            fg='#ffffff',
            bg='#2d2d2d'
        ).pack(pady=(10, 5))
        
        location_var = tk.StringVar(value="当前路段")
        location_entry = tk.Entry(
            dialog,
            textvariable=location_var,
            font=('Arial', 12),
            justify='center',
            width=25
        )
        location_entry.pack(pady=5)
        
        # 临时限速复选框
        is_temporary_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            dialog,
            text="临时限速",
            font=('Arial', 10),
            fg='#ffffff',
            bg='#2d2d2d',
            selectcolor='#444444',
            variable=is_temporary_var
        ).pack(pady=10)
        
        # 按钮框架
        button_frame = tk.Frame(dialog, bg='#2d2d2d')
        button_frame.pack(pady=10)
        
        def apply_limit():
            try:
                limit = float(limit_var.get())
                location = location_var.get().strip() or "当前路段"
                is_temporary = is_temporary_var.get()
                
                if 20 <= limit <= 120:
                    if self.system:
                        self.system.update_speed_limit(location, limit, is_temporary)
                    dialog.destroy()
                else:
                    messagebox.showwarning("警告", "速度限制值应在20-120之间")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        tk.Button(
            button_frame,
            text="确定",
            font=('Arial', 10),
            bg='#008800',
            fg='#ffffff',
            padx=20,
            command=apply_limit
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="取消",
            font=('Arial', 10),
            bg='#880000',
            fg='#ffffff',
            padx=20,
            command=dialog.destroy
        ).pack(side='left', padx=10)
    
    def _quick_set_speed(self, speed: float):
        """快速设置速度"""
        if self.system:
            self.system.set_simulated_speed(speed)
            self.log_display.add_log(f"已设置模拟速度: {speed} km/h", 'info')
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = """
车载超速提示系统 v1.0

功能特性:
• 实时速度监测
• 限速变化检测
• 超速自动警告 (3秒)
• 1秒内响应超速
• 性能指标监控

技术实现:
• 模块化架构设计
• 线程安全操作
• 事件驱动回调
• GUI可视化界面
        """
        messagebox.showinfo("关于", about_text)
    
    def _on_closing(self):
        """关闭窗口处理"""
        if self.is_system_running:
            if messagebox.askyesno("确认", "系统正在运行，确定要退出吗？"):
                self._stop_system()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置主题
    root.style = ttk.Style()
    try:
        root.style.theme_use('clam')
    except:
        pass
    
    # 创建应用
    app = SpeedingAlertGUI(root)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()
