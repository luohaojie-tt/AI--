# -*- coding: utf-8 -*-
"""
V2.1 数据筛选和搜索功能 - 搜索管理器
提供精确搜索和模糊搜索功能，支持缓存和性能优化
"""

import time
import threading
import math
import sys
import os
from typing import List, Dict, Optional, Tuple, Callable, Any, Union
from concurrent.futures import ThreadPoolExecutor, Future
from functools import lru_cache
import logging
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

from core.data_manager import SNRDataPoint
from filters.filter_models import SearchParams, SearchResult


@dataclass
class SearchMatch:
    """
    搜索匹配结果
    包含匹配的数据点和相似度分数
    """
    point: SNRDataPoint
    score: float  # 相似度分数 (0-1, 1为完全匹配)
    match_type: str  # "exact" 或 "fuzzy"
    matched_fields: List[str]  # 匹配的字段列表
    
    def __post_init__(self):
        """验证分数范围"""
        if not 0 <= self.score <= 1:
            raise ValueError(f"相似度分数必须在0-1之间: {self.score}")


class SearchCache:
    """
    搜索结果缓存管理器
    使用LRU策略优化搜索性能
    """
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self._cache: Dict[int, Tuple[List[SearchMatch], float]] = {}
        self._access_times: Dict[int, float] = {}
        self._lock = threading.RLock()
        
        # 统计信息
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, params: SearchParams) -> Optional[List[SearchMatch]]:
        """获取缓存的搜索结果"""
        cache_key = hash(params)
        
        with self._lock:
            if cache_key in self._cache:
                result, timestamp = self._cache[cache_key]
                self._access_times[cache_key] = time.time()
                self.hits += 1
                return result
            
            self.misses += 1
            return None
    
    def put(self, params: SearchParams, result: List[SearchMatch]) -> None:
        """缓存搜索结果"""
        cache_key = hash(params)
        current_time = time.time()
        
        with self._lock:
            # 检查缓存大小，必要时清理
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()
            
            self._cache[cache_key] = (result, current_time)
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


class SearchManager:
    """
    搜索管理器
    提供精确搜索和模糊搜索功能，支持缓存和性能优化
    """
    
    def __init__(self, cache_size: int = 50, max_workers: int = 2):
        self.cache = SearchCache(cache_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 性能统计
        self.total_searches = 0
        self.total_search_time = 0.0
        self.cache_enabled = True
        
        # 搜索配置
        self.max_results = 1000  # 最大返回结果数
        self.fuzzy_threshold = 0.1  # 模糊搜索最低相似度阈值
    
    def search_data(self, data: List[SNRDataPoint], params: SearchParams) -> List[SearchMatch]:
        """
        同步搜索数据
        
        Args:
            data: 要搜索的数据列表
            params: 搜索参数
            
        Returns:
            搜索匹配结果列表，按相似度降序排列
        """
        start_time = time.time()
        
        try:
            # 检查缓存
            if self.cache_enabled:
                cached_result = self.cache.get(params)
                if cached_result is not None:
                    self.logger.debug(f"搜索缓存命中: {params}")
                    return cached_result
            
            # 执行搜索
            if params.search_type == "exact":
                matches = self._exact_search(data, params)
            elif params.search_type == "fuzzy":
                matches = self._fuzzy_search(data, params)
            else:
                raise ValueError(f"不支持的搜索类型: {params.search_type}")
            
            # 排序结果（按相似度降序）
            matches.sort(key=lambda m: m.score, reverse=True)
            
            # 限制结果数量
            if len(matches) > self.max_results:
                matches = matches[:self.max_results]
            
            # 缓存结果
            if self.cache_enabled:
                self.cache.put(params, matches)
            
            # 更新性能统计
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            with self._lock:
                self.total_searches += 1
                self.total_search_time += execution_time
            
            self.logger.debug(f"搜索完成: {len(matches)} 个匹配结果, 耗时: {execution_time:.1f}ms")
            
            return matches
            
        except Exception as e:
            self.logger.error(f"搜索过程中发生错误: {e}")
            raise
    
    def search_data_async(self, data: List[SNRDataPoint], params: SearchParams) -> Future[List[SearchMatch]]:
        """
        异步搜索数据
        
        Args:
            data: 要搜索的数据列表
            params: 搜索参数
            
        Returns:
            Future对象，包含搜索结果
        """
        return self.executor.submit(self.search_data, data, params)
    
    def _exact_search(self, data: List[SNRDataPoint], params: SearchParams) -> List[SearchMatch]:
        """
        精确搜索实现
        
        Args:
            data: 数据列表
            params: 搜索参数
            
        Returns:
            精确匹配的结果列表
        """
        matches = []
        
        for point in data:
            matched_fields = []
            is_match = True
            
            # 检查PRE参数
            if params.exact_pre is not None:
                if point.pre == params.exact_pre:
                    matched_fields.append("pre")
                else:
                    is_match = False
            
            # 检查MAIN参数
            if params.exact_main is not None:
                if point.main == params.exact_main:
                    matched_fields.append("main")
                else:
                    is_match = False
            
            # 检查POST参数
            if params.exact_post is not None:
                if point.post == params.exact_post:
                    matched_fields.append("post")
                else:
                    is_match = False
            
            # 检查SNR值（精确匹配）
            if params.target_snr is not None:
                if abs(point.snr - params.target_snr) < 1e-6:  # 浮点数精确比较
                    matched_fields.append("snr")
                else:
                    is_match = False
            
            # 如果所有条件都匹配，添加到结果中
            if is_match and matched_fields:
                match = SearchMatch(
                    point=point,
                    score=1.0,  # 精确匹配得分为1.0
                    match_type="exact",
                    matched_fields=matched_fields
                )
                matches.append(match)
        
        return matches
    
    def _fuzzy_search(self, data: List[SNRDataPoint], params: SearchParams) -> List[SearchMatch]:
        """
        模糊搜索实现
        
        Args:
            data: 数据列表
            params: 搜索参数
            
        Returns:
            模糊匹配的结果列表
        """
        matches = []
        
        for point in data:
            score = 0.0
            matched_fields = []
            total_criteria = 0
            
            # 检查PRE参数（精确匹配）
            if params.exact_pre is not None:
                total_criteria += 1
                if point.pre == params.exact_pre:
                    score += 1.0
                    matched_fields.append("pre")
            
            # 检查MAIN参数（精确匹配）
            if params.exact_main is not None:
                total_criteria += 1
                if point.main == params.exact_main:
                    score += 1.0
                    matched_fields.append("main")
            
            # 检查POST参数（精确匹配）
            if params.exact_post is not None:
                total_criteria += 1
                if point.post == params.exact_post:
                    score += 1.0
                    matched_fields.append("post")
            
            # 检查SNR值（容差匹配）
            if params.target_snr is not None:
                total_criteria += 1
                snr_diff = abs(point.snr - params.target_snr)
                
                if snr_diff <= params.snr_tolerance:
                    # 计算SNR相似度分数（线性衰减）
                    if params.snr_tolerance > 0:
                        snr_score = 1.0 - (snr_diff / params.snr_tolerance)
                    else:
                        snr_score = 1.0 if snr_diff == 0 else 0.0
                    
                    score += snr_score
                    matched_fields.append("snr")
            
            # 计算平均相似度分数
            if total_criteria > 0:
                avg_score = score / total_criteria
                
                # 只保留超过阈值的匹配
                if avg_score >= self.fuzzy_threshold and matched_fields:
                    match = SearchMatch(
                        point=point,
                        score=avg_score,
                        match_type="fuzzy",
                        matched_fields=matched_fields
                    )
                    matches.append(match)
        
        return matches
    
    def search_similar_snr(self, data: List[SNRDataPoint], 
                          target_snr: float, 
                          tolerance: float = 0.1,
                          max_results: int = 10) -> List[SearchMatch]:
        """
        搜索相似SNR值的数据点
        
        Args:
            data: 数据列表
            target_snr: 目标SNR值
            tolerance: 容差范围
            max_results: 最大结果数
            
        Returns:
            相似SNR值的匹配结果
        """
        params = SearchParams(
            target_snr=target_snr,
            snr_tolerance=tolerance,
            search_type="fuzzy"
        )
        
        matches = self.search_data(data, params)
        
        # 只保留SNR匹配的结果
        snr_matches = [m for m in matches if "snr" in m.matched_fields]
        
        # 限制结果数量
        return snr_matches[:max_results]
    
    def search_exact_parameters(self, data: List[SNRDataPoint],
                               pre: Optional[int] = None,
                               main: Optional[int] = None,
                               post: Optional[int] = None) -> List[SearchMatch]:
        """
        搜索精确参数匹配的数据点
        
        Args:
            data: 数据列表
            pre: PRE参数值
            main: MAIN参数值
            post: POST参数值
            
        Returns:
            精确参数匹配的结果
        """
        params = SearchParams(
            exact_pre=pre,
            exact_main=main,
            exact_post=post,
            search_type="exact"
        )
        
        return self.search_data(data, params)
    
    def find_best_snr_in_range(self, data: List[SNRDataPoint],
                               pre_range: Optional[Tuple[int, int]] = None,
                               main_range: Optional[Tuple[int, int]] = None,
                               post_range: Optional[Tuple[int, int]] = None,
                               top_n: int = 5) -> List[SNRDataPoint]:
        """
        在指定参数范围内找到最佳SNR值的数据点
        
        Args:
            data: 数据列表
            pre_range: PRE参数范围 (min, max)
            main_range: MAIN参数范围 (min, max)
            post_range: POST参数范围 (min, max)
            top_n: 返回前N个最佳结果
            
        Returns:
            最佳SNR值的数据点列表
        """
        # 筛选符合范围的数据点
        filtered_data = []
        
        for point in data:
            # 检查PRE范围
            if pre_range and not (pre_range[0] <= point.pre <= pre_range[1]):
                continue
            
            # 检查MAIN范围
            if main_range and not (main_range[0] <= point.main <= main_range[1]):
                continue
            
            # 检查POST范围
            if post_range and not (post_range[0] <= point.post <= post_range[1]):
                continue
            
            filtered_data.append(point)
        
        # 按SNR值降序排序
        filtered_data.sort(key=lambda p: p.snr, reverse=True)
        
        # 返回前N个结果
        return filtered_data[:top_n]
    
    def get_search_suggestions(self, data: List[SNRDataPoint], 
                              partial_params: Dict[str, Any]) -> List[SearchParams]:
        """
        根据部分参数生成搜索建议
        
        Args:
            data: 数据列表
            partial_params: 部分搜索参数
            
        Returns:
            建议的搜索参数列表
        """
        suggestions = []
        
        # 基于现有数据生成建议
        if data:
            # 获取所有唯一值
            pre_values = sorted(set(p.pre for p in data))
            main_values = sorted(set(p.main for p in data))
            post_values = sorted(set(p.post for p in data))
            snr_values = [p.snr for p in data]
            
            # 生成精确搜索建议
            if "pre" in partial_params:
                target_pre = partial_params["pre"]
                if target_pre in pre_values:
                    suggestions.append(SearchParams(
                        exact_pre=target_pre,
                        search_type="exact"
                    ))
            
            if "main" in partial_params:
                target_main = partial_params["main"]
                if target_main in main_values:
                    suggestions.append(SearchParams(
                        exact_main=target_main,
                        search_type="exact"
                    ))
            
            if "post" in partial_params:
                target_post = partial_params["post"]
                if target_post in post_values:
                    suggestions.append(SearchParams(
                        exact_post=target_post,
                        search_type="exact"
                    ))
            
            # 生成SNR模糊搜索建议
            if "snr" in partial_params:
                target_snr = partial_params["snr"]
                
                # 不同容差的建议
                for tolerance in [0.05, 0.1, 0.2, 0.5]:
                    suggestions.append(SearchParams(
                        target_snr=target_snr,
                        snr_tolerance=tolerance,
                        search_type="fuzzy"
                    ))
            
            # 生成组合搜索建议
            if len(partial_params) > 1:
                combo_params = SearchParams(search_type="exact")
                
                if "pre" in partial_params:
                    combo_params.exact_pre = partial_params["pre"]
                if "main" in partial_params:
                    combo_params.exact_main = partial_params["main"]
                if "post" in partial_params:
                    combo_params.exact_post = partial_params["post"]
                
                if not combo_params.is_empty():
                    suggestions.append(combo_params)
        
        return suggestions
    
    def _parse_search_input(self, search_input: str) -> Dict[str, Any]:
        """
        解析搜索输入字符串
        
        Args:
            search_input: 搜索输入字符串，如 "pre=4097" 或 "snr=26.0"
            
        Returns:
            解析后的参数字典
        """
        params = {}
        
        # 支持格式："pre=4097", "snr=26.0", "main=8193"
        if '=' in search_input:
            try:
                key, value = search_input.split('=', 1)
                key = key.strip().lower()
                
                if key in ['pre', 'main', 'post']:
                    params[key] = int(value.strip(), 0)  # 支持十六进制
                elif key == 'snr':
                    params[key] = float(value.strip())
            except ValueError:
                pass  # 忽略解析错误
        
        return params
    
    def batch_search(self, data: List[SNRDataPoint], 
                    params_list: List[SearchParams]) -> List[List[SearchMatch]]:
        """
        批量搜索数据
        
        Args:
            data: 要搜索的数据
            params_list: 搜索参数列表
            
        Returns:
            搜索结果列表
        """
        results = []
        
        for params in params_list:
            result = self.search_data(data, params)
            results.append(result)
        
        return results
    
    def batch_search_async(self, data: List[SNRDataPoint], 
                          params_list: List[SearchParams]) -> List[Future[List[SearchMatch]]]:
        """
        异步批量搜索数据
        
        Args:
            data: 要搜索的数据
            params_list: 搜索参数列表
            
        Returns:
            Future对象列表
        """
        futures = []
        
        for params in params_list:
            future = self.search_data_async(data, params)
            futures.append(future)
        
        return futures
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.logger.info("搜索缓存已清空")
    
    def set_cache_enabled(self, enabled: bool) -> None:
        """启用或禁用缓存"""
        self.cache_enabled = enabled
        self.logger.info(f"搜索缓存已{'启用' if enabled else '禁用'}")
    
    def set_fuzzy_threshold(self, threshold: float) -> None:
        """设置模糊搜索阈值"""
        if not 0 <= threshold <= 1:
            raise ValueError(f"阈值必须在0-1之间: {threshold}")
        
        self.fuzzy_threshold = threshold
        self.logger.info(f"模糊搜索阈值已设置为: {threshold}")
    
    def set_max_results(self, max_results: int) -> None:
        """设置最大返回结果数"""
        if max_results <= 0:
            raise ValueError(f"最大结果数必须大于0: {max_results}")
        
        self.max_results = max_results
        self.logger.info(f"最大返回结果数已设置为: {max_results}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            性能统计字典
        """
        with self._lock:
            avg_search_time = (self.total_search_time / self.total_searches) if self.total_searches > 0 else 0
            
            return {
                'total_searches': self.total_searches,
                'total_search_time_ms': self.total_search_time,
                'avg_search_time_ms': avg_search_time,
                'cache_stats': self.cache.get_stats(),
                'cache_enabled': self.cache_enabled,
                'fuzzy_threshold': self.fuzzy_threshold,
                'max_results': self.max_results
            }
    
    def reset_stats(self) -> None:
        """重置性能统计"""
        with self._lock:
            self.total_searches = 0
            self.total_search_time = 0.0
            self.cache.hits = 0
            self.cache.misses = 0
            self.cache.evictions = 0
    
    def shutdown(self) -> None:
        """关闭搜索管理器"""
        self.executor.shutdown(wait=True)
        self.clear_cache()
        self.logger.info("搜索管理器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# 全局搜索管理器实例
_search_manager_instance: Optional[SearchManager] = None
_search_manager_lock = threading.Lock()


def get_search_manager() -> SearchManager:
    """
    获取全局搜索管理器实例（单例模式）
    
    Returns:
        SearchManager实例
    """
    global _search_manager_instance
    
    if _search_manager_instance is None:
        with _search_manager_lock:
            if _search_manager_instance is None:
                _search_manager_instance = SearchManager()
    
    return _search_manager_instance


def reset_search_manager() -> None:
    """
    重置全局搜索管理器实例
    """
    global _search_manager_instance
    
    with _search_manager_lock:
        if _search_manager_instance is not None:
            _search_manager_instance.shutdown()
            _search_manager_instance = None


# 便捷函数
def quick_search(data: List[SNRDataPoint], params: SearchParams) -> List[SearchMatch]:
    """
    快速搜索数据（使用全局管理器）
    
    Args:
        data: 要搜索的数据
        params: 搜索参数
        
    Returns:
        搜索结果
    """
    manager = get_search_manager()
    return manager.search_data(data, params)


def quick_search_async(data: List[SNRDataPoint], params: SearchParams) -> Future[List[SearchMatch]]:
    """
    快速异步搜索数据（使用全局管理器）
    
    Args:
        data: 要搜索的数据
        params: 搜索参数
        
    Returns:
        Future对象
    """
    manager = get_search_manager()
    return manager.search_data_async(data, params)


def find_exact_match(data: List[SNRDataPoint],
                    pre: Optional[int] = None,
                    main: Optional[int] = None,
                    post: Optional[int] = None) -> List[SNRDataPoint]:
    """
    查找精确参数匹配的数据点（便捷函数）
    
    Args:
        data: 数据列表
        pre: PRE参数值
        main: MAIN参数值
        post: POST参数值
        
    Returns:
        匹配的数据点列表
    """
    manager = get_search_manager()
    matches = manager.search_exact_parameters(data, pre, main, post)
    return [match.point for match in matches]


def find_similar_snr(data: List[SNRDataPoint],
                     target_snr: float,
                     tolerance: float = 0.1,
                     max_results: int = 10) -> List[SNRDataPoint]:
    """
    查找相似SNR值的数据点（便捷函数）
    
    Args:
        data: 数据列表
        target_snr: 目标SNR值
        tolerance: 容差范围
        max_results: 最大结果数
        
    Returns:
        相似SNR值的数据点列表
    """
    manager = get_search_manager()
    matches = manager.search_similar_snr(data, target_snr, tolerance, max_results)
    return [match.point for match in matches]