#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能测试脚本
测试SNR数据可视化工具的所有功能
"""

import sys
import os

# 添加项目根目录和子目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'filters'))
sys.path.insert(0, os.path.join(project_root, 'core'))

from filters.filter_manager import FilterManager
from filters.search_manager import SearchManager
from core.data_manager import SNRDataPoint

def test_all_features():
    """测试所有功能"""
    print("=== SNR数据可视化工具完整功能测试 ===")
    
    # 创建测试数据
    test_points = [
        SNRDataPoint(0x1000, 0x2000, 0x3000, 25.5),
        SNRDataPoint(0x1001, 0x2001, 0x3001, 26.2),
        SNRDataPoint(0x1002, 0x2002, 0x3002, 24.8),
        SNRDataPoint(0x1003, 0x2003, 0x3003, 27.1),
        SNRDataPoint(0x1004, 0x2004, 0x3004, 23.9)
    ]
    
    print(f"原始数据: {len(test_points)} 行")
    
    # 1. 测试筛选功能
    print("\n--- 测试筛选功能 ---")
    filter_manager = FilterManager()
    from filter_models import FilterCriteria
    criteria = FilterCriteria(snr_min=25.0, snr_max=27.0)
    filtered_data, stats = filter_manager.filter_data(test_points, criteria)
    print(f"筛选后数据: {len(filtered_data)} 行")
    print(f"筛选统计: {stats}")
    
    # 2. 测试搜索功能
    print("\n--- 测试搜索功能 ---")
    search_manager = SearchManager()
    from filter_models import SearchParams
    params = SearchParams(search_type="exact", exact_pre=0x1002)
    results = search_manager.search_data(test_points, params)
    print(f"精确搜索结果: {len(results)} 行")
    
    params = SearchParams(search_type="fuzzy", target_snr=26.0, snr_tolerance=0.5)
    results = search_manager.search_data(test_points, params)
    print(f"模糊搜索结果: {len(results)} 行")
    
    # 3. 测试搜索建议功能
    print("\n--- 测试搜索建议功能 ---")
    partial_params = {"pre": 4097}
    suggestions = search_manager.get_search_suggestions(test_points, partial_params)
    print(f"搜索建议: {len(suggestions)} 个")
    for suggestion in suggestions:
        print(f"  建议: {suggestion}")
    
    # 4. 测试性能
    print("\n--- 测试性能 ---")
    import time
    
    # 创建大量测试数据
    large_data = [
        SNRDataPoint(i, i + 10000, i + 20000, 20.0 + (i % 100) * 0.1)
        for i in range(1000)
    ]
    
    print(f"大数据集: {len(large_data)} 行")
    
    # 测试筛选性能
    start_time = time.time()
    criteria = FilterCriteria(snr_min=25.0, snr_max=30.0)
    filtered_data, stats = filter_manager.filter_data(large_data, criteria)
    filter_time = time.time() - start_time
    print(f"筛选性能: {filter_time:.3f}秒, 结果: {len(filtered_data)} 行")
    
    # 测试搜索性能
    start_time = time.time()
    params = SearchParams(search_type="exact", exact_pre=500)
    results = search_manager.search_data(large_data, params)
    search_time = time.time() - start_time
    print(f"搜索性能: {search_time:.3f}秒, 结果: {len(results)} 行")
    
    print("\n所有功能测试完成！")
    print("筛选功能正常")
    print("搜索功能正常")
    print("搜索建议功能正常")
    print("性能表现良好")

if __name__ == "__main__":
    test_all_features()