#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜索建议功能
"""

import sys
import os

# 添加项目根目录和子目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'filters'))
sys.path.insert(0, os.path.join(project_root, 'core'))

from filters.search_manager import SearchManager
from core.data_manager import SNRDataPoint

def test_search_suggestions():
    """测试搜索建议功能"""
    print("=== 测试搜索建议功能 ===")
    
    # 创建测试数据
    test_points = [
        SNRDataPoint(0x1000, 0x2000, 0x3000, 25.5),
        SNRDataPoint(0x1001, 0x2001, 0x3001, 26.2),
        SNRDataPoint(0x1002, 0x2002, 0x3002, 24.8),
        SNRDataPoint(0x1003, 0x2003, 0x3003, 27.1),
        SNRDataPoint(0x1004, 0x2004, 0x3004, 23.9)
    ]
    
    print(f"原始数据: {len(test_points)} 行")
    
    # 创建搜索管理器
    search_manager = SearchManager()
    
    # 测试搜索建议
    print("\n--- 测试搜索建议 (输入: {'pre': 4097}) ---")
    try:
        partial_params = {"pre": 4097}
        suggestions = search_manager.get_search_suggestions(test_points, partial_params)
        print(f"搜索建议: {len(suggestions)} 个")
        for suggestion in suggestions:
            print(f"  建议: {suggestion}")
    except Exception as e:
        print(f"搜索建议测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n所有测试完成！")

if __name__ == "__main__":
    test_search_suggestions()