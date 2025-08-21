# -*- coding: utf-8 -*-
"""
V2.1 数据筛选和搜索功能 - 筛选管理器
提供高效的数据筛选、缓存和异步处理功能
"""

import time
import threading
import sys
import os
from typing import List, Dict, Optional, Tuple, Callable, Any
from concurrent.futures import ThreadPoolExecutor, Future
from functools import lru_cache
import weakref
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

from core.data_manager import SNRDataPoint
from filters.filter_models import FilterCriteria, FilterStats, FilterResult


class FilterCache:
    """
    筛选结果缓存管理器
    使用LRU策略和弱引用优化内存使用
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[int, Tuple[List[SNRDataPoint], FilterStats, float]] = {}
        self._access_times: Dict[int, float] = {}
        self._lock = threading.RLock()
        
        # 统计信息
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, criteria: FilterCriteria) -> Optional[FilterResult]:
        """获取缓存的筛选结果"""
        cache_key = hash(criteria)
        
        with self._lock:
            if cache_key in self._cache:
                result, stats, timestamp = self._cache[cache_key]
                self._access_times[cache_key] = time.time()
                self.hits += 1
                return result, stats
            
            self.misses += 1
            return None
    
    def put(self, criteria: FilterCriteria, result: List[SNRDataPoint], stats: FilterStats) -> None:
        """缓存筛选结果"""
        cache_key = hash(criteria)
        current_time = time.time()
        
        with self._lock:
            # 检查缓存大小，必要时清理
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()
            
            self._cache[cache_key] = (result, stats, current_time)
            self._access_times[cache_key] = current_time
    
    def _evict_lru(self) -> None:
        """清理最近最少使用的缓存项"""
        if not self._access_times:
            return
        
        # 找到最久未访问的项
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        
        # 删除缓存项
        del self._cache[lru_key]
        del self._access_times[lru_key]
        self.evictions += 1
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions
        }
    
    def __len__(self) -> int:
        return len(self._cache)


class FilterManager:
    """
    筛选管理器
    提供高效的数据筛选、缓存和异步处理功能
    """
    
    def __init__(self, cache_size: int = 100, max_workers: int = 4):
        self.cache = FilterCache(cache_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 性能统计
        self.total_filters = 0
        self.total_filter_time = 0.0
        self.cache_enabled = True
    
    def filter_data(self, data: List[SNRDataPoint], criteria: FilterCriteria) -> FilterResult:
        """
        同步筛选数据
        
        Args:
            data: 要筛选的数据列表
            criteria: 筛选条件
            
        Returns:
            筛选结果和统计信息的元组
        """
        start_time = time.time()
        
        try:
            # 检查缓存
            if self.cache_enabled:
                cached_result = self.cache.get(criteria)
                if cached_result is not None:
                    self.logger.debug(f"缓存命中: {criteria}")
                    return cached_result
            
            # 执行筛选
            filtered_data = self._apply_filter(data, criteria)
            
            # 计算统计信息
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            stats = self._calculate_stats(data, filtered_data, criteria, execution_time)
            
            # 缓存结果
            if self.cache_enabled:
                self.cache.put(criteria, filtered_data, stats)
            
            # 更新性能统计
            with self._lock:
                self.total_filters += 1
                self.total_filter_time += execution_time
            
            self.logger.debug(f"筛选完成: {len(filtered_data)}/{len(data)} 条记录, 耗时: {execution_time:.1f}ms")
            
            return filtered_data, stats
            
        except Exception as e:
            self.logger.error(f"筛选过程中发生错误: {e}")
            raise
    
    def filter_data_async(self, data: List[SNRDataPoint], criteria: FilterCriteria) -> Future[FilterResult]:
        """
        异步筛选数据
        
        Args:
            data: 要筛选的数据列表
            criteria: 筛选条件
            
        Returns:
            Future对象，包含筛选结果
        """
        return self.executor.submit(self.filter_data, data, criteria)
    
    def _apply_filter(self, data: List[SNRDataPoint], criteria: FilterCriteria) -> List[SNRDataPoint]:
        """
        应用筛选条件
        
        Args:
            data: 原始数据
            criteria: 筛选条件
            
        Returns:
            筛选后的数据列表
        """
        if criteria.is_empty():
            return data.copy()
        
        filtered_data = []
        
        for point in data:
            if self._matches_criteria(point, criteria):
                filtered_data.append(point)
        
        return filtered_data
    
    def _matches_criteria(self, point: SNRDataPoint, criteria: FilterCriteria) -> bool:
        """
        检查数据点是否匹配筛选条件
        
        Args:
            point: 数据点
            criteria: 筛选条件
            
        Returns:
            是否匹配
        """
        # 检查PRE参数范围
        if criteria.pre_min is not None and point.pre < criteria.pre_min:
            return False
        if criteria.pre_max is not None and point.pre > criteria.pre_max:
            return False
        
        # 检查MAIN参数范围
        if criteria.main_min is not None and point.main < criteria.main_min:
            return False
        if criteria.main_max is not None and point.main > criteria.main_max:
            return False
        
        # 检查POST参数范围
        if criteria.post_min is not None and point.post < criteria.post_min:
            return False
        if criteria.post_max is not None and point.post > criteria.post_max:
            return False
        
        # 检查SNR值范围
        if criteria.snr_min is not None and point.snr < criteria.snr_min:
            return False
        if criteria.snr_max is not None and point.snr > criteria.snr_max:
            return False
        
        return True
    
    def _calculate_stats(self, original_data: List[SNRDataPoint], 
                        filtered_data: List[SNRDataPoint],
                        criteria: FilterCriteria,
                        execution_time: float) -> FilterStats:
        """
        计算筛选统计信息
        
        Args:
            original_data: 原始数据
            filtered_data: 筛选后数据
            criteria: 筛选条件
            execution_time: 执行时间(毫秒)
            
        Returns:
            统计信息对象
        """
        stats = FilterStats(
            total_matched=len(filtered_data),
            total_original=len(original_data),
            filter_criteria=criteria,
            execution_time_ms=execution_time
        )
        
        if filtered_data:
            # 计算参数范围
            pre_values = [p.pre for p in filtered_data]
            main_values = [p.main for p in filtered_data]
            post_values = [p.post for p in filtered_data]
            snr_values = [p.snr for p in filtered_data]
            
            stats.pre_range = (min(pre_values), max(pre_values))
            stats.main_range = (min(main_values), max(main_values))
            stats.post_range = (min(post_values), max(post_values))
            stats.snr_range = (min(snr_values), max(snr_values))
            
            # 计算唯一值数量
            stats.unique_pre_count = len(set(pre_values))
            stats.unique_main_count = len(set(main_values))
            stats.unique_post_count = len(set(post_values))
            
            # 计算SNR统计
            stats.avg_snr = sum(snr_values) / len(snr_values)
            
            # 找到最优和最差SNR点
            stats.max_snr_point = max(filtered_data, key=lambda p: p.snr)
            stats.min_snr_point = min(filtered_data, key=lambda p: p.snr)
        
        return stats
    
    def batch_filter(self, data: List[SNRDataPoint], 
                    criteria_list: List[FilterCriteria]) -> List[FilterResult]:
        """
        批量筛选数据
        
        Args:
            data: 要筛选的数据
            criteria_list: 筛选条件列表
            
        Returns:
            筛选结果列表
        """
        results = []
        
        for criteria in criteria_list:
            result = self.filter_data(data, criteria)
            results.append(result)
        
        return results
    
    def batch_filter_async(self, data: List[SNRDataPoint], 
                          criteria_list: List[FilterCriteria]) -> List[Future[FilterResult]]:
        """
        异步批量筛选数据
        
        Args:
            data: 要筛选的数据
            criteria_list: 筛选条件列表
            
        Returns:
            Future对象列表
        """
        futures = []
        
        for criteria in criteria_list:
            future = self.filter_data_async(data, criteria)
            futures.append(future)
        
        return futures
    
    def get_filter_suggestions(self, data: List[SNRDataPoint], 
                             target_count: int = 100) -> List[FilterCriteria]:
        """
        根据数据分布生成筛选建议
        
        Args:
            data: 数据列表
            target_count: 目标筛选结果数量
            
        Returns:
            建议的筛选条件列表
        """
        if not data:
            return []
        
        suggestions = []
        
        # 基于SNR值的建议
        snr_values = [p.snr for p in data]
        snr_sorted = sorted(snr_values, reverse=True)
        
        if len(snr_sorted) > target_count:
            threshold = snr_sorted[target_count - 1]
            suggestions.append(FilterCriteria(
                snr_min=threshold,
                name=f"高SNR筛选 (前{target_count}条)",
                description=f"SNR >= {threshold:.2f}"
            ))
        
        # 基于参数分布的建议
        pre_values = [p.pre for p in data]
        main_values = [p.main for p in data]
        post_values = [p.post for p in data]
        
        # 生成四分位数筛选建议
        for param_name, values in [("PRE", pre_values), ("MAIN", main_values), ("POST", post_values)]:
            if values:
                sorted_values = sorted(values)
                q1_idx = len(sorted_values) // 4
                q3_idx = 3 * len(sorted_values) // 4
                
                q1_val = sorted_values[q1_idx]
                q3_val = sorted_values[q3_idx]
                
                if param_name == "PRE":
                    criteria = FilterCriteria(
                        pre_min=q1_val, pre_max=q3_val,
                        name=f"{param_name}中位数筛选",
                        description=f"{param_name}: [{q1_val}, {q3_val}]"
                    )
                elif param_name == "MAIN":
                    criteria = FilterCriteria(
                        main_min=q1_val, main_max=q3_val,
                        name=f"{param_name}中位数筛选",
                        description=f"{param_name}: [{q1_val}, {q3_val}]"
                    )
                else:  # POST
                    criteria = FilterCriteria(
                        post_min=q1_val, post_max=q3_val,
                        name=f"{param_name}中位数筛选",
                        description=f"{param_name}: [{q1_val}, {q3_val}]"
                    )
                
                suggestions.append(criteria)
        
        return suggestions
    
    def optimize_filter(self, data: List[SNRDataPoint], 
                       criteria: FilterCriteria,
                       target_count: int) -> FilterCriteria:
        """
        优化筛选条件以接近目标数量
        
        Args:
            data: 数据列表
            criteria: 初始筛选条件
            target_count: 目标结果数量
            
        Returns:
            优化后的筛选条件
        """
        current_result, _ = self.filter_data(data, criteria)
        current_count = len(current_result)
        
        if abs(current_count - target_count) <= target_count * 0.1:  # 10%容差
            return criteria
        
        # 简单的二分搜索优化（针对SNR筛选）
        if criteria.has_snr_filter() and current_result:
            snr_values = [p.snr for p in data]
            snr_sorted = sorted(snr_values, reverse=True)
            
            if target_count < len(snr_sorted):
                optimal_threshold = snr_sorted[target_count - 1]
                
                optimized_criteria = FilterCriteria(
                    pre_min=criteria.pre_min,
                    pre_max=criteria.pre_max,
                    main_min=criteria.main_min,
                    main_max=criteria.main_max,
                    post_min=criteria.post_min,
                    post_max=criteria.post_max,
                    snr_min=optimal_threshold,
                    snr_max=criteria.snr_max,
                    name=f"优化的{criteria.name}",
                    description=f"优化后的筛选条件，目标数量: {target_count}"
                )
                
                return optimized_criteria
        
        return criteria
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.logger.info("筛选缓存已清空")
    
    def set_cache_enabled(self, enabled: bool) -> None:
        """启用或禁用缓存"""
        self.cache_enabled = enabled
        self.logger.info(f"筛选缓存已{'启用' if enabled else '禁用'}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            性能统计字典
        """
        with self._lock:
            avg_filter_time = (self.total_filter_time / self.total_filters) if self.total_filters > 0 else 0
            
            return {
                'total_filters': self.total_filters,
                'total_filter_time_ms': self.total_filter_time,
                'avg_filter_time_ms': avg_filter_time,
                'cache_stats': self.cache.get_stats(),
                'cache_enabled': self.cache_enabled
            }
    
    def reset_stats(self) -> None:
        """重置性能统计"""
        with self._lock:
            self.total_filters = 0
            self.total_filter_time = 0.0
            self.cache.hits = 0
            self.cache.misses = 0
            self.cache.evictions = 0
    
    def shutdown(self) -> None:
        """关闭筛选管理器"""
        self.executor.shutdown(wait=True)
        self.clear_cache()
        self.logger.info("筛选管理器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# 全局筛选管理器实例
_filter_manager_instance: Optional[FilterManager] = None
_filter_manager_lock = threading.Lock()


def get_filter_manager() -> FilterManager:
    """
    获取全局筛选管理器实例（单例模式）
    
    Returns:
        FilterManager实例
    """
    global _filter_manager_instance
    
    if _filter_manager_instance is None:
        with _filter_manager_lock:
            if _filter_manager_instance is None:
                _filter_manager_instance = FilterManager()
    
    return _filter_manager_instance


def reset_filter_manager() -> None:
    """
    重置全局筛选管理器实例
    """
    global _filter_manager_instance
    
    with _filter_manager_lock:
        if _filter_manager_instance is not None:
            _filter_manager_instance.shutdown()
            _filter_manager_instance = None


# 便捷函数
def quick_filter(data: List[SNRDataPoint], criteria: FilterCriteria) -> FilterResult:
    """
    快速筛选数据（使用全局管理器）
    
    Args:
        data: 要筛选的数据
        criteria: 筛选条件
        
    Returns:
        筛选结果
    """
    manager = get_filter_manager()
    return manager.filter_data(data, criteria)


def quick_filter_async(data: List[SNRDataPoint], criteria: FilterCriteria) -> Future[FilterResult]:
    """
    快速异步筛选数据（使用全局管理器）
    
    Args:
        data: 要筛选的数据
        criteria: 筛选条件
        
    Returns:
        Future对象
    """
    manager = get_filter_manager()
    return manager.filter_data_async(data, criteria)