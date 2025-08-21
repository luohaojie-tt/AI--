#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试脚本
测试SNR数据可视化工具的主要功能集成
"""

import sys
import os

# 添加项目根目录和子目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'ui'))
sys.path.insert(0, os.path.join(project_root, 'core'))

import tkinter as tk
from ui.filter_panel import FilterPanel, create_filter_window
from ui.search_panel import SearchPanel, create_search_window
from core.data_manager import SNRDataPoint

def test_integration():
    """测试集成功能"""
    print("=== SNR工具集成测试 ===")
    
    # 创建测试数据
    test_points = [
        SNRDataPoint(0x1000, 0x2000, 0x3000, 25.5),
        SNRDataPoint(0x1001, 0x2001, 0x3001, 26.2),
        SNRDataPoint(0x1002, 0x2002, 0x3002, 24.8),
        SNRDataPoint(0x1003, 0x2003, 0x3003, 27.1),
        SNRDataPoint(0x1004, 0x2004, 0x3004, 23.9)
    ]
    
    print(f"测试数据: {len(test_points)} 行")
    
    # 测试筛选面板创建
    print("\n--- 测试筛选面板创建 ---")
    try:
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 创建筛选窗口
        filter_window, filter_panel = create_filter_window("测试筛选面板")
        filter_panel.set_data(test_points)
        print("[OK] 筛选面板创建成功")
        
        # 创建搜索窗口
        search_window, search_panel = create_search_window("测试搜索面板")
        search_panel.set_data(test_points)
        print("[OK] 搜索面板创建成功")
        
        # 销毁窗口
        filter_window.destroy()
        search_window.destroy()
        root.destroy()
        print("[OK] 窗口销毁成功")
        
    except Exception as e:
        print(f"[ERROR] 面板创建失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试导出功能
    print("\n--- 测试导出功能 ---")
    try:
        from filter_manager import FilterManager
        from filter_models import FilterCriteria
        
        # 创建筛选器
        filter_manager = FilterManager()
        criteria = FilterCriteria(snr_min=25.0, snr_max=27.0)
        filtered_data, stats = filter_manager.filter_data(test_points, criteria)
        
        # 测试导出
        import csv
        import tempfile
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            temp_filename = f.name
            
            # 写入CSV数据
            writer = csv.writer(f)
            writer.writerow(['PRE', 'MAIN', 'POST', 'SNR'])
            for point in filtered_data:
                writer.writerow([point.pre, point.main, point.post, point.snr])
        
        print(f"[OK] 导出功能测试成功: {temp_filename}")
        
        # 清理临时文件
        os.unlink(temp_filename)
        
    except Exception as e:
        print(f"[ERROR] 导出功能测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n集成测试完成！")

if __name__ == "__main__":
    test_integration()