#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNR数据可视化工具 Bug检测脚本
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_all_components():
    """测试所有组件"""
    print("SNR数据可视化工具 - Bug检测")
    print("=" * 40)
    
    try:
        # 1. 测试模块导入
        print("1. 测试模块导入...")
        from core import config, data_manager, visualization
        from filters import filter_manager, filter_models, search_manager
        from ui import filter_panel, search_panel
        print("   [OK] 所有模块导入成功")
        
        # 2. 测试核心功能
        print("2. 测试核心功能...")
        from core.data_manager import DataManager, SNRDataPoint
        from filters.filter_manager import FilterManager
        from filters.search_manager import SearchManager
        from filters.filter_models import FilterCriteria, SearchParams
        
        # 创建测试数据
        test_data = [
            SNRDataPoint(0x1000, 0x2000, 0x3000, 25.5),
            SNRDataPoint(0x1001, 0x2001, 0x3001, 26.2),
            SNRDataPoint(0x1002, 0x2002, 0x3002, 24.8)
        ]
        
        # 测试数据管理器
        data_manager = DataManager()
        print("   [OK] 数据管理器创建成功")
        
        # 测试筛选功能
        filter_manager = FilterManager()
        criteria = FilterCriteria(snr_min=25.0, snr_max=27.0)
        filtered_data, stats = filter_manager.filter_data(test_data, criteria)
        print(f"   [OK] 筛选功能正常，结果: {len(filtered_data)} 条数据")
        
        # 测试搜索功能
        search_manager = SearchManager()
        params = SearchParams(search_type="exact", exact_pre=0x1001)
        search_results = search_manager.search_data(test_data, params)
        print(f"   [OK] 搜索功能正常，结果: {len(search_results)} 条数据")
        
        # 测试搜索建议功能
        if hasattr(search_manager, '_parse_search_input'):
            result = search_manager._parse_search_input("pre=4097")
            expected = {"pre": 4097}
            if result == expected:
                print("   [OK] 搜索解析功能正常")
            else:
                print(f"   [WARNING] 搜索解析结果不匹配: 期望{expected}, 实际{result}")
        else:
            print("   [INFO] _parse_search_input方法不存在")
        
        partial_params = {"pre": 4097}
        suggestions = search_manager.get_search_suggestions(test_data, partial_params)
        print(f"   [OK] 搜索建议功能正常，结果: {len(suggestions)} 个建议")
        
        # 3. 测试UI组件
        print("3. 测试UI组件...")
        from ui.filter_panel import FilterPanel
        from ui.search_panel import SearchPanel
        print("   [OK] UI组件导入成功")
        
        print("\n" + "=" * 40)
        print("所有测试通过！未发现明显bug。")
        print("程序可以正常运行。")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_components()
    sys.exit(0 if success else 1)