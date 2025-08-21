# -*- coding: utf-8 -*-
"""
SNR可视化工具数据管理模块
提供数据加载、解析、验证、计算等功能
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
import logging
from pathlib import Path


@dataclass
class SNRDataPoint:
    """SNR数据点类"""
    pre: int
    main: int
    post: int
    snr: float
    
    def to_dict(self) -> Dict[str, Union[int, float]]:
        """转换为字典"""
        return {
            'pre': self.pre,
            'main': self.main,
            'post': self.post,
            'snr': self.snr
        }


@dataclass
class DataStatistics:
    """数据统计信息类"""
    total_points: int
    pre_range: Tuple[int, int]
    main_range: Tuple[int, int]
    post_range: Tuple[int, int]
    snr_range: Tuple[float, float]
    unique_pre_count: int
    unique_main_count: int
    unique_post_count: int
    max_snr_point: SNRDataPoint
    min_snr_point: SNRDataPoint


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """验证文件路径"""
        if not file_path:
            return False
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")
        
        # 检查文件扩展名
        allowed_extensions = {'.csv', '.txt'}
        if path.suffix.lower() not in allowed_extensions:
            logging.warning(f"文件扩展名不在推荐列表中: {path.suffix}")
        
        return True
    
    @staticmethod
    def validate_data_point(pre: Any, main: Any, post: Any, snr: Any, line_num: int) -> Optional[SNRDataPoint]:
        """验证单个数据点"""
        try:
            # 解析Pre值
            if isinstance(pre, str):
                pre_val = int(pre, 0) if '0x' in pre.lower() else int(pre)
            else:
                pre_val = int(pre)
            
            # 解析Main值
            if isinstance(main, str):
                main_val = int(main, 0) if '0x' in main.lower() else int(main)
            else:
                main_val = int(main)
            
            # 解析Post值
            if isinstance(post, str):
                post_val = int(post, 0) if '0x' in post.lower() else int(post)
            else:
                post_val = int(post)
            
            # 解析SNR值
            snr_val = float(snr)
            
            # 基本范围检查
            if pre_val < 0 or main_val < 0 or post_val < 0:
                logging.warning(f"第{line_num}行: 参数值不能为负数")
                return None
            
            if not np.isfinite(snr_val):
                logging.warning(f"第{line_num}行: SNR值无效 ({snr_val})")
                return None
            
            return SNRDataPoint(pre_val, main_val, post_val, snr_val)
            
        except (ValueError, TypeError) as e:
            logging.warning(f"第{line_num}行数据解析失败: {e}")
            return None
    
    @staticmethod
    def validate_dataset(data_points: List[SNRDataPoint]) -> bool:
        """验证整个数据集"""
        if not data_points:
            raise ValueError("数据集为空")
        
        if len(data_points) < 2:
            logging.warning("数据点数量过少，可能影响可视化效果")
        
        # 检查数据分布
        pre_values = set(point.pre for point in data_points)
        main_values = set(point.main for point in data_points)
        post_values = set(point.post for point in data_points)
        
        if len(pre_values) == 1 and len(main_values) == 1 and len(post_values) == 1:
            logging.warning("所有参数值都相同，无法进行有效的可视化分析")
        
        return True


class DataParser:
    """数据解析器"""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def parse_csv_file(self, file_path: str) -> List[SNRDataPoint]:
        """解析CSV文件"""
        self.validator.validate_file_path(file_path)
        
        try:
            # 尝试使用pandas读取
            df = pd.read_csv(file_path)
            return self._parse_dataframe(df)
        except Exception as e:
            logging.warning(f"pandas读取失败，尝试手动解析: {e}")
            return self._parse_text_file(file_path)
    
    def parse_text_file(self, file_path: str) -> List[SNRDataPoint]:
        """解析文本文件"""
        self.validator.validate_file_path(file_path)
        return self._parse_text_file(file_path)
    
    def _parse_dataframe(self, df: pd.DataFrame) -> List[SNRDataPoint]:
        """解析DataFrame"""
        data_points = []
        
        # 检查列名
        expected_columns = ['pre', 'main', 'post', 'snr']
        if not all(col in df.columns for col in expected_columns):
            raise ValueError(f"CSV文件缺少必要列: {expected_columns}")
        
        for idx, row in df.iterrows():
            point = self.validator.validate_data_point(
                row['pre'], row['main'], row['post'], row['snr'], idx + 2
            )
            if point:
                data_points.append(point)
        
        return data_points
    
    def _parse_text_file(self, file_path: str) -> List[SNRDataPoint]:
        """手动解析文本文件"""
        data_points = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 检测并跳过表头
        start_line = 0
        if lines and self._is_header_line(lines[0]):
            start_line = 1
        
        for i, line in enumerate(lines[start_line:], start_line):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) != 4:
                logging.warning(f"第{i+1}行格式错误，期望4列，实际{len(parts)}列")
                continue
            
            point = self.validator.validate_data_point(
                parts[0], parts[1], parts[2], parts[3], i + 1
            )
            if point:
                data_points.append(point)
        
        return data_points
    
    def _is_header_line(self, line: str) -> bool:
        """检测是否为表头行"""
        line_lower = line.lower()
        header_keywords = ['pre', 'main', 'post', 'snr']
        return all(keyword in line_lower for keyword in header_keywords)


class SNRCalculator:
    """SNR计算器"""
    
    @staticmethod
    def calculate_statistics(data_points: List[SNRDataPoint]) -> DataStatistics:
        """计算数据统计信息"""
        if not data_points:
            raise ValueError("数据点列表为空")
        
        pre_values = [point.pre for point in data_points]
        main_values = [point.main for point in data_points]
        post_values = [point.post for point in data_points]
        snr_values = [point.snr for point in data_points]
        
        # 找到最大和最小SNR点
        max_snr_idx = np.argmax(snr_values)
        min_snr_idx = np.argmin(snr_values)
        
        return DataStatistics(
            total_points=len(data_points),
            pre_range=(min(pre_values), max(pre_values)),
            main_range=(min(main_values), max(main_values)),
            post_range=(min(post_values), max(post_values)),
            snr_range=(min(snr_values), max(snr_values)),
            unique_pre_count=len(set(pre_values)),
            unique_main_count=len(set(main_values)),
            unique_post_count=len(set(post_values)),
            max_snr_point=data_points[max_snr_idx],
            min_snr_point=data_points[min_snr_idx]
        )
    
    @staticmethod
    def find_optimal_configs(data_points: List[SNRDataPoint], top_n: int = 10) -> List[SNRDataPoint]:
        """找到最优配置"""
        sorted_points = sorted(data_points, key=lambda x: x.snr, reverse=True)
        return sorted_points[:top_n]
    
    @staticmethod
    def filter_by_snr_range(data_points: List[SNRDataPoint], min_snr: float, max_snr: float) -> List[SNRDataPoint]:
        """按SNR范围过滤数据"""
        return [point for point in data_points if min_snr <= point.snr <= max_snr]
    
    @staticmethod
    def filter_by_parameters(data_points: List[SNRDataPoint], 
                           pre: Optional[int] = None,
                           main: Optional[int] = None,
                           post: Optional[int] = None) -> List[SNRDataPoint]:
        """按参数值过滤数据"""
        filtered = data_points
        
        if pre is not None:
            filtered = [point for point in filtered if point.pre == pre]
        if main is not None:
            filtered = [point for point in filtered if point.main == main]
        if post is not None:
            filtered = [point for point in filtered if point.post == post]
        
        return filtered


class DataManager:
    """数据管理器主类"""
    
    def __init__(self):
        self.parser = DataParser()
        self.calculator = SNRCalculator()
        self.validator = DataValidator()
        
        # 数据存储
        self.data_points: List[SNRDataPoint] = []
        self.statistics: Optional[DataStatistics] = None
        self.dataframe: Optional[pd.DataFrame] = None
        
        # 缓存
        self._cache = {}
    
    def load_data(self, file_path: str) -> Dict[str, Any]:
        """加载数据文件"""
        try:
            # 根据文件扩展名选择解析方法
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                self.data_points = self.parser.parse_csv_file(file_path)
            else:
                self.data_points = self.parser.parse_text_file(file_path)
            
            # 验证数据集
            self.validator.validate_dataset(self.data_points)
            
            # 计算统计信息
            self.statistics = self.calculator.calculate_statistics(self.data_points)
            
            # 创建DataFrame
            self._create_dataframe()
            
            # 清空缓存
            self._cache.clear()
            
            logging.info(f"成功加载 {len(self.data_points)} 条数据")
            
            return {
                'success': True,
                'data_count': len(self.data_points),
                'statistics': self.statistics,
                'file_path': file_path
            }
            
        except FileNotFoundError:
            error_msg = f"文件不存在: {file_path}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
        except PermissionError:
            error_msg = f"文件访问权限不足: {file_path}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
        except pd.errors.EmptyDataError:
            error_msg = "文件为空或没有有效数据"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
        except pd.errors.ParserError as e:
            error_msg = f"文件格式解析错误: {e}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
        except UnicodeDecodeError as e:
            error_msg = f"文件编码错误，无法读取: {e.reason}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
        except ValueError as e:
            error_msg = f"数据验证失败: {e}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
        except Exception as e:
            error_msg = f"数据加载失败: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
    
    def _create_dataframe(self) -> None:
        """创建pandas DataFrame"""
        if not self.data_points:
            self.dataframe = None
            return
        
        data_dict = {
            'pre': [point.pre for point in self.data_points],
            'main': [point.main for point in self.data_points],
            'post': [point.post for point in self.data_points],
            'snr': [point.snr for point in self.data_points]
        }
        
        self.dataframe = pd.DataFrame(data_dict)
    
    def get_line_chart_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取折线图数据"""
        cache_key = f"line_chart_{hash(str(sorted(params.items())))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 根据参数过滤数据
            filtered_points = self.calculator.filter_by_parameters(
                self.data_points,
                pre=params.get('pre'),
                main=params.get('main'),
                post=params.get('post')
            )
            
            if not filtered_points:
                return {'success': False, 'error': '没有匹配的数据点'}
            
            # 按指定参数分组
            group_by = params.get('group_by', 'main')  # 默认按main分组
            
            grouped_data = {}
            for point in filtered_points:
                group_key = getattr(point, group_by)
                if group_key not in grouped_data:
                    grouped_data[group_key] = {'x': [], 'y': []}
                
                # x轴数据（根据group_by确定）
                if group_by == 'pre':
                    x_val = point.main if params.get('x_axis') == 'main' else point.post
                elif group_by == 'main':
                    x_val = point.pre if params.get('x_axis') == 'pre' else point.post
                else:  # group_by == 'post'
                    x_val = point.pre if params.get('x_axis') == 'pre' else point.main
                
                grouped_data[group_key]['x'].append(x_val)
                grouped_data[group_key]['y'].append(point.snr)
            
            result = {
                'success': True,
                'data': grouped_data,
                'group_by': group_by,
                'total_points': len(filtered_points)
            }
            
            self._cache[cache_key] = result
            return result
            
        except KeyError as e:
            error_msg = f"参数错误，缺少必要的字段: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except AttributeError as e:
            error_msg = f"数据结构错误: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except ValueError as e:
            error_msg = f"数据值错误: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"获取折线图数据失败: {str(e)}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_heatmap_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取热力图数据"""
        cache_key = f"heatmap_{hash(str(sorted(params.items())))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 固定参数值
            fixed_param = params.get('fixed_param', 'main')
            fixed_value = params.get('fixed_value')
            
            # 过滤数据
            filter_kwargs = {fixed_param: fixed_value} if fixed_value is not None else {}
            filtered_points = self.calculator.filter_by_parameters(self.data_points, **filter_kwargs)
            
            if not filtered_points:
                return {'success': False, 'error': '没有匹配的数据点'}
            
            # 确定x和y轴参数
            if fixed_param == 'main':
                x_param, y_param = 'pre', 'post'
            elif fixed_param == 'pre':
                x_param, y_param = 'main', 'post'
            else:  # fixed_param == 'post'
                x_param, y_param = 'pre', 'main'
            
            # 获取唯一值并排序
            x_values = sorted(set(getattr(point, x_param) for point in filtered_points))
            y_values = sorted(set(getattr(point, y_param) for point in filtered_points))
            
            # 创建热力图矩阵
            heatmap_matrix = np.full((len(y_values), len(x_values)), np.nan)
            
            for point in filtered_points:
                x_idx = x_values.index(getattr(point, x_param))
                y_idx = y_values.index(getattr(point, y_param))
                heatmap_matrix[y_idx, x_idx] = point.snr
            
            result = {
                'success': True,
                'matrix': heatmap_matrix,
                'x_values': x_values,
                'y_values': y_values,
                'x_param': x_param,
                'y_param': y_param,
                'fixed_param': fixed_param,
                'fixed_value': fixed_value,
                'total_points': len(filtered_points)
            }
            
            self._cache[cache_key] = result
            return result
            
        except KeyError as e:
            error_msg = f"参数错误，缺少必要的字段: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except AttributeError as e:
            error_msg = f"数据结构错误: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except ValueError as e:
            error_msg = f"数据值错误或索引错误: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"获取热力图数据失败: {str(e)}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_global_config_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取全局配置图数据"""
        cache_key = f"global_config_{hash(str(sorted(params.items())))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # SNR范围过滤
            min_snr = params.get('min_snr', float('-inf'))
            max_snr = params.get('max_snr', float('inf'))
            
            filtered_points = self.calculator.filter_by_snr_range(self.data_points, min_snr, max_snr)
            
            if not filtered_points:
                return {'success': False, 'error': '没有匹配的数据点'}
            
            # 准备3D散点图数据
            scatter_data = {
                'pre': [point.pre for point in filtered_points],
                'main': [point.main for point in filtered_points],
                'post': [point.post for point in filtered_points],
                'snr': [point.snr for point in filtered_points]
            }
            
            # 找到最优配置
            top_configs = self.calculator.find_optimal_configs(filtered_points, params.get('top_n', 10))
            
            result = {
                'success': True,
                'scatter_data': scatter_data,
                'top_configs': [point.to_dict() for point in top_configs],
                'total_points': len(filtered_points),
                'snr_range': (min([p.snr for p in filtered_points]), max([p.snr for p in filtered_points]))
            }
            
            self._cache[cache_key] = result
            return result
            
        except KeyError as e:
            error_msg = f"参数错误，缺少必要的字段: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except ValueError as e:
            error_msg = f"数据值错误或范围错误: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except AttributeError as e:
            error_msg = f"数据结构错误: {e}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"获取全局配置图数据失败: {str(e)}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_unique_values(self, param: str) -> List[int]:
        """获取指定参数的唯一值列表"""
        if not self.data_points:
            return []
        
        if param not in ['pre', 'main', 'post']:
            raise ValueError(f"无效的参数名: {param}")
        
        values = set(getattr(point, param) for point in self.data_points)
        return sorted(list(values))
    
    def get_statistics(self) -> Optional[DataStatistics]:
        """获取数据统计信息"""
        return self.statistics
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """获取pandas DataFrame"""
        return self.dataframe
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def export_data(self, file_path: str, format: str = 'csv') -> bool:
        """导出数据"""
        try:
            if format.lower() == 'csv' and self.dataframe is not None:
                self.dataframe.to_csv(file_path, index=False)
                return True
            else:
                raise ValueError(f"不支持的导出格式: {format}")
        except Exception as e:
            logging.error(f"数据导出失败: {e}")
            return False


# 便捷函数
def format_hex(value: int) -> str:
    """格式化十六进制显示"""
    return f"0x{value:02X}" if value < 256 else f"0x{value:04X}"


def format_parameter_display(param_name: str, value: int) -> str:
    """格式化参数显示"""
    return f"{param_name.upper()}: {format_hex(value)} ({value})"