# -*- coding: utf-8 -*-
"""
V2.1 数据筛选和搜索功能 - 数据结构定义
提供筛选条件、搜索参数、筛选统计等数据结构
"""

import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

from core.data_manager import SNRDataPoint


@dataclass
class FilterCriteria:
    """
    筛选条件数据结构
    支持四种参数的范围筛选和SNR值筛选
    """
    # 参数范围筛选
    pre_min: Optional[int] = None
    pre_max: Optional[int] = None
    main_min: Optional[int] = None
    main_max: Optional[int] = None
    post_min: Optional[int] = None
    post_max: Optional[int] = None
    
    # SNR值筛选
    snr_min: Optional[float] = None
    snr_max: Optional[float] = None
    
    # 筛选元数据
    created_at: datetime = field(default_factory=datetime.now)
    name: str = "未命名筛选"
    description: str = ""
    
    def __post_init__(self):
        """初始化后验证"""
        self._validate_ranges()
    
    def _validate_ranges(self) -> None:
        """验证范围参数的有效性"""
        # 验证pre范围
        if self.pre_min is not None and self.pre_max is not None:
            if self.pre_min > self.pre_max:
                raise ValueError(f"pre_min ({self.pre_min}) 不能大于 pre_max ({self.pre_max})")
        
        # 验证main范围
        if self.main_min is not None and self.main_max is not None:
            if self.main_min > self.main_max:
                raise ValueError(f"main_min ({self.main_min}) 不能大于 main_max ({self.main_max})")
        
        # 验证post范围
        if self.post_min is not None and self.post_max is not None:
            if self.post_min > self.post_max:
                raise ValueError(f"post_min ({self.post_min}) 不能大于 post_max ({self.post_max})")
        
        # 验证SNR范围
        if self.snr_min is not None and self.snr_max is not None:
            if self.snr_min > self.snr_max:
                raise ValueError(f"snr_min ({self.snr_min}) 不能大于 snr_max ({self.snr_max})")
    
    def is_empty(self) -> bool:
        """检查是否为空筛选条件"""
        return all([
            self.pre_min is None, self.pre_max is None,
            self.main_min is None, self.main_max is None,
            self.post_min is None, self.post_max is None,
            self.snr_min is None, self.snr_max is None
        ])
    
    def has_parameter_filter(self) -> bool:
        """检查是否有参数筛选条件"""
        return any([
            self.pre_min is not None, self.pre_max is not None,
            self.main_min is not None, self.main_max is not None,
            self.post_min is not None, self.post_max is not None
        ])
    
    def has_snr_filter(self) -> bool:
        """检查是否有SNR筛选条件"""
        return self.snr_min is not None or self.snr_max is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，支持序列化"""
        return {
            'pre_min': self.pre_min,
            'pre_max': self.pre_max,
            'main_min': self.main_min,
            'main_max': self.main_max,
            'post_min': self.post_min,
            'post_max': self.post_max,
            'snr_min': self.snr_min,
            'snr_max': self.snr_max,
            'created_at': self.created_at.isoformat(),
            'name': self.name,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterCriteria':
        """从字典创建实例，支持反序列化"""
        # 处理datetime字段
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FilterCriteria':
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __hash__(self) -> int:
        """支持哈希，用于缓存"""
        return hash((
            self.pre_min, self.pre_max,
            self.main_min, self.main_max,
            self.post_min, self.post_max,
            self.snr_min, self.snr_max
        ))
    
    def __eq__(self, other) -> bool:
        """支持相等比较"""
        if not isinstance(other, FilterCriteria):
            return False
        
        return (
            self.pre_min == other.pre_min and self.pre_max == other.pre_max and
            self.main_min == other.main_min and self.main_max == other.main_max and
            self.post_min == other.post_min and self.post_max == other.post_max and
            self.snr_min == other.snr_min and self.snr_max == other.snr_max
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        conditions = []
        
        if self.pre_min is not None or self.pre_max is not None:
            pre_range = f"[{self.pre_min or '∞'}, {self.pre_max or '∞'}]"
            conditions.append(f"PRE: {pre_range}")
        
        if self.main_min is not None or self.main_max is not None:
            main_range = f"[{self.main_min or '∞'}, {self.main_max or '∞'}]"
            conditions.append(f"MAIN: {main_range}")
        
        if self.post_min is not None or self.post_max is not None:
            post_range = f"[{self.post_min or '∞'}, {self.post_max or '∞'}]"
            conditions.append(f"POST: {post_range}")
        
        if self.snr_min is not None or self.snr_max is not None:
            snr_range = f"[{self.snr_min or '∞'}, {self.snr_max or '∞'}]"
            conditions.append(f"SNR: {snr_range}")
        
        if not conditions:
            return "无筛选条件"
        
        return " & ".join(conditions)


@dataclass
class SearchParams:
    """
    搜索参数数据结构
    支持精确搜索和模糊搜索
    """
    # 精确搜索参数
    exact_pre: Optional[int] = None
    exact_main: Optional[int] = None
    exact_post: Optional[int] = None
    
    # SNR值容差搜索
    target_snr: Optional[float] = None
    snr_tolerance: float = 0.1  # 默认容差
    
    # 搜索元数据
    created_at: datetime = field(default_factory=datetime.now)
    search_type: str = "exact"  # "exact" 或 "fuzzy"
    
    def __post_init__(self):
        """初始化后验证"""
        self._validate_params()
    
    def _validate_params(self) -> None:
        """验证搜索参数"""
        if self.search_type not in ["exact", "fuzzy"]:
            raise ValueError(f"不支持的搜索类型: {self.search_type}")
        
        if self.snr_tolerance < 0:
            raise ValueError(f"SNR容差不能为负数: {self.snr_tolerance}")
        
        # 检查是否有有效的搜索条件
        if self.is_empty():
            raise ValueError("搜索参数不能为空")
    
    def is_empty(self) -> bool:
        """检查是否为空搜索参数"""
        return all([
            self.exact_pre is None,
            self.exact_main is None,
            self.exact_post is None,
            self.target_snr is None
        ])
    
    def has_parameter_search(self) -> bool:
        """检查是否有参数搜索条件"""
        return any([
            self.exact_pre is not None,
            self.exact_main is not None,
            self.exact_post is not None
        ])
    
    def has_snr_search(self) -> bool:
        """检查是否有SNR搜索条件"""
        return self.target_snr is not None
    
    def get_snr_range(self) -> Optional[Tuple[float, float]]:
        """获取SNR搜索范围"""
        if self.target_snr is None:
            return None
        
        return (
            self.target_snr - self.snr_tolerance,
            self.target_snr + self.snr_tolerance
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，支持序列化"""
        return {
            'exact_pre': self.exact_pre,
            'exact_main': self.exact_main,
            'exact_post': self.exact_post,
            'target_snr': self.target_snr,
            'snr_tolerance': self.snr_tolerance,
            'created_at': self.created_at.isoformat(),
            'search_type': self.search_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchParams':
        """从字典创建实例，支持反序列化"""
        # 处理datetime字段
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SearchParams':
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __hash__(self) -> int:
        """支持哈希，用于缓存"""
        return hash((
            self.exact_pre, self.exact_main, self.exact_post,
            self.target_snr, self.snr_tolerance, self.search_type
        ))
    
    def __eq__(self, other) -> bool:
        """支持相等比较"""
        if not isinstance(other, SearchParams):
            return False
        
        return (
            self.exact_pre == other.exact_pre and
            self.exact_main == other.exact_main and
            self.exact_post == other.exact_post and
            self.target_snr == other.target_snr and
            self.snr_tolerance == other.snr_tolerance and
            self.search_type == other.search_type
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        conditions = []
        
        if self.exact_pre is not None:
            conditions.append(f"PRE={self.exact_pre}")
        
        if self.exact_main is not None:
            conditions.append(f"MAIN={self.exact_main}")
        
        if self.exact_post is not None:
            conditions.append(f"POST={self.exact_post}")
        
        if self.target_snr is not None:
            if self.search_type == "fuzzy":
                snr_range = self.get_snr_range()
                conditions.append(f"SNR≈{self.target_snr}±{self.snr_tolerance} [{snr_range[0]:.2f}, {snr_range[1]:.2f}]")
            else:
                conditions.append(f"SNR={self.target_snr}")
        
        if not conditions:
            return "无搜索条件"
        
        return " & ".join(conditions)


@dataclass
class FilterStats:
    """
    筛选统计信息数据结构
    提供筛选结果的完整统计信息
    """
    # 基本统计
    total_matched: int = 0
    total_original: int = 0
    match_percentage: float = 0.0
    
    # 参数统计
    pre_range: Optional[Tuple[int, int]] = None
    main_range: Optional[Tuple[int, int]] = None
    post_range: Optional[Tuple[int, int]] = None
    snr_range: Optional[Tuple[float, float]] = None
    
    # 唯一值统计
    unique_pre_count: int = 0
    unique_main_count: int = 0
    unique_post_count: int = 0
    
    # 最优值
    max_snr_point: Optional[SNRDataPoint] = None
    min_snr_point: Optional[SNRDataPoint] = None
    avg_snr: float = 0.0
    
    # 筛选元数据
    filter_criteria: Optional[FilterCriteria] = None
    created_at: datetime = field(default_factory=datetime.now)
    execution_time_ms: float = 0.0
    
    def __post_init__(self):
        """初始化后计算"""
        self._calculate_percentage()
    
    def _calculate_percentage(self) -> None:
        """计算匹配百分比"""
        if self.total_original > 0:
            self.match_percentage = (self.total_matched / self.total_original) * 100
        else:
            self.match_percentage = 0.0
    
    def is_empty_result(self) -> bool:
        """检查是否为空结果"""
        return self.total_matched == 0
    
    def get_efficiency_level(self) -> str:
        """获取筛选效率等级"""
        if self.match_percentage >= 80:
            return "低效筛选"
        elif self.match_percentage >= 50:
            return "中等筛选"
        elif self.match_percentage >= 20:
            return "有效筛选"
        elif self.match_percentage >= 5:
            return "高效筛选"
        else:
            return "极高效筛选"
    
    def get_performance_level(self) -> str:
        """获取性能等级"""
        if self.execution_time_ms <= 50:
            return "极快"
        elif self.execution_time_ms <= 100:
            return "快速"
        elif self.execution_time_ms <= 500:
            return "正常"
        elif self.execution_time_ms <= 1000:
            return "较慢"
        else:
            return "慢"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，支持序列化"""
        return {
            'total_matched': self.total_matched,
            'total_original': self.total_original,
            'match_percentage': self.match_percentage,
            'pre_range': self.pre_range,
            'main_range': self.main_range,
            'post_range': self.post_range,
            'snr_range': self.snr_range,
            'unique_pre_count': self.unique_pre_count,
            'unique_main_count': self.unique_main_count,
            'unique_post_count': self.unique_post_count,
            'max_snr_point': self.max_snr_point.to_dict() if self.max_snr_point else None,
            'min_snr_point': self.min_snr_point.to_dict() if self.min_snr_point else None,
            'avg_snr': self.avg_snr,
            'filter_criteria': self.filter_criteria.to_dict() if self.filter_criteria else None,
            'created_at': self.created_at.isoformat(),
            'execution_time_ms': self.execution_time_ms,
            'efficiency_level': self.get_efficiency_level(),
            'performance_level': self.get_performance_level()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterStats':
        """从字典创建实例，支持反序列化"""
        # 处理datetime字段
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # 处理SNRDataPoint字段
        if 'max_snr_point' in data and data['max_snr_point']:
            data['max_snr_point'] = SNRDataPoint(**data['max_snr_point'])
        
        if 'min_snr_point' in data and data['min_snr_point']:
            data['min_snr_point'] = SNRDataPoint(**data['min_snr_point'])
        
        # 处理FilterCriteria字段
        if 'filter_criteria' in data and data['filter_criteria']:
            data['filter_criteria'] = FilterCriteria.from_dict(data['filter_criteria'])
        
        # 移除计算字段
        data.pop('efficiency_level', None)
        data.pop('performance_level', None)
        
        return cls(**data)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FilterStats':
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"筛选结果: {self.total_matched}/{self.total_original} "
            f"({self.match_percentage:.1f}%) - "
            f"{self.get_efficiency_level()} - "
            f"耗时: {self.execution_time_ms:.1f}ms ({self.get_performance_level()})"
        )


# 类型别名
FilterResult = Tuple[List[SNRDataPoint], FilterStats]
SearchResult = List[SNRDataPoint]


# 工具函数
def create_empty_filter() -> FilterCriteria:
    """创建空筛选条件"""
    return FilterCriteria(name="空筛选")


def create_snr_filter(min_snr: float, max_snr: float, name: str = "SNR筛选") -> FilterCriteria:
    """创建SNR范围筛选条件"""
    return FilterCriteria(
        snr_min=min_snr,
        snr_max=max_snr,
        name=name,
        description=f"SNR范围: [{min_snr}, {max_snr}]"
    )


def create_parameter_filter(pre: Optional[Tuple[int, int]] = None,
                          main: Optional[Tuple[int, int]] = None,
                          post: Optional[Tuple[int, int]] = None,
                          name: str = "参数筛选") -> FilterCriteria:
    """创建参数范围筛选条件"""
    return FilterCriteria(
        pre_min=pre[0] if pre else None,
        pre_max=pre[1] if pre else None,
        main_min=main[0] if main else None,
        main_max=main[1] if main else None,
        post_min=post[0] if post else None,
        post_max=post[1] if post else None,
        name=name
    )


def create_exact_search(pre: Optional[int] = None,
                       main: Optional[int] = None,
                       post: Optional[int] = None) -> SearchParams:
    """创建精确搜索参数"""
    return SearchParams(
        exact_pre=pre,
        exact_main=main,
        exact_post=post,
        search_type="exact"
    )


def create_fuzzy_snr_search(target_snr: float, tolerance: float = 0.1) -> SearchParams:
    """创建模糊SNR搜索参数"""
    return SearchParams(
        target_snr=target_snr,
        snr_tolerance=tolerance,
        search_type="fuzzy"
    )