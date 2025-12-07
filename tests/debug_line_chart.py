#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试折线图无数据问题的脚本
"""

import sys
import os
import tkinter as tk

# 添加项目根目录和子目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'filters'))
sys.path.insert(0, os.path.join(project_root, 'core'))

import numpy as np
import pandas as pd
from core.data_manager import SNRDataPoint, DataManager
from snr_visualizer_optimized import SNRVisualizerOptimized

def debug_line_chart_issue():
    """调试折线图无数据问题"""
    print("=== 调试折线图无数据问题 ===")
    
    # 创建一个简单的Tkinter根窗口用于测试
    root = tk.Tk()
    root.withdraw()  # 隐藏窗口
    
    # 创建应用程序实例
    app = SNRVisualizerOptimized(root)
    
    # 创建测试数据
    test_data = [
        (0x1000, 0x2000, 0x3000, 25.5),
        (0x1000, 0x2000, 0x3001, 26.2),
        (0x1000, 0x2001, 0x3000, 24.8),
        (0x1001, 0x2000, 0x3000, 27.1),
        (0x1001, 0x2001, 0x3001, 23.9)
    ]
    
    # 创建DataFrame
    df = pd.DataFrame(test_data, columns=['pre', 'main', 'post', 'snr'])
    
    # 设置测试数据
    app.data = test_data
    app.df = df
    app.pre_values = [0x1000, 0x1001]
    app.main_values = [0x2000, 0x2001]
    app.post_values = [0x3000, 0x3001]
    app.current_pre = 0x1000
    app.current_main = 0x2000
    app.current_post = 0x3000
    
    print("1. 检查数据状态...")
    print(f"   app.data: {len(app.data) if app.data else 0} 条记录")
    print(f"   app.df: {len(app.df) if app.df is not None else 0} 行")
    print(f"   current_pre: {app.current_pre}")
    print(f"   current_main: {app.current_main}")
    print(f"   current_post: {app.current_post}")
    
    print("\n2. 检查DataManager...")
    # 测试DataManager
    data_manager = app.data_manager
    print(f"   data_manager: {data_manager}")
    print(f"   data_points: {len(data_manager.data_points) if data_manager.data_points else 0}")
    print(f"   dataframe: {len(data_manager.dataframe) if data_manager.dataframe is not None else 0}")
    
    # 手动设置DataManager数据
    data_points = [SNRDataPoint(row[0], row[1], row[2], row[3]) for row in test_data]
    data_manager.data_points = data_points
    data_manager.dataframe = df
    data_manager.statistics = data_manager.calculator.calculate_statistics(data_points)
    
    print(f"   设置后 data_points: {len(data_manager.data_points)}")
    print(f"   设置后 dataframe: {len(data_manager.dataframe)}")
    
    print("\n3. 测试_get_line_chart_data_async...")
    # 测试异步获取折线图数据
    line_data = app._get_line_chart_data_async()
    print(f"   获取的折线图数据: {line_data}")
    
    if 'error' in line_data:
        print(f"   错误信息: {line_data['error']}")
    elif line_data.get('success', False):
        grouped_data = line_data.get('data', {})
        print(f"   分组数据: {grouped_data}")
        for group_key, data in grouped_data.items():
            print(f"     组 {group_key}: x={data.get('x', [])}, y={data.get('y', [])}")
    else:
        print("   数据获取失败")
    
    print("\n4. 测试_draw_line_chart...")
    # 测试绘制折线图
    app.ax.clear()
    app._draw_line_chart(line_data)
    
    # 检查是否有绘图内容
    lines = app.ax.get_lines()
    print(f"   绘制的线条数: {len(lines)}")
    
    if len(lines) > 0:
        print("   折线图绘制成功!")
        for i, line in enumerate(lines):
            x_data = line.get_xdata()
            y_data = line.get_ydata()
            print(f"     线条 {i}: {len(x_data)} 个点")
    else:
        print("   折线图绘制失败!")
        # 检查是否有错误文本
        texts = [child for child in app.ax.get_children() if hasattr(child, 'get_text')]
        for text in texts:
            if hasattr(text, 'get_text'):
                text_content = text.get_text()
                if '❌' in text_content or '错误' in text_content:
                    print(f"   错误信息: {text_content}")
    
    print("\n5. 检查绘图参数...")
    # 检查绘图参数
    params = {
        'pre': app.current_pre,
        'main': app.current_main,
        'post': app.current_post,
        'group_by': 'main',
        'x_axis': 'pre'
    }
    print(f"   绘图参数: {params}")
    
    line_data2 = data_manager.get_line_chart_data(params)
    print(f"   使用DataManager获取数据: {line_data2}")
    
    print("\n调试完成！")
    
    # 销毁测试窗口
    root.destroy()

if __name__ == "__main__":
    debug_line_chart_issue()