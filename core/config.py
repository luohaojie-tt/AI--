# -*- coding: utf-8 -*-
"""
SNR可视化工具配置管理模块
提供主题配置、图表样式配置、应用设置等功能
"""

import os
from typing import Dict, Any, Optional
import json
from dataclasses import dataclass, asdict


@dataclass
class ThemeConfig:
    """主题配置类"""
    # 深色主题配色
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    background_color: str = "#2b2b2b"
    surface_color: str = "#3c3c3c"
    text_color: str = "#ffffff"
    text_secondary: str = "#cccccc"
    border_color: str = "#555555"
    success_color: str = "#28a745"
    warning_color: str = "#ffc107"
    error_color: str = "#dc3545"
    
    # 图表配色方案
    chart_colors: list = None
    
    def __post_init__(self):
        if self.chart_colors is None:
            self.chart_colors = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
                "#bcbd22", "#17becf"
            ]


@dataclass
class ChartConfig:
    """图表配置类"""
    # 折线图配置
    line_width: int = 3
    marker_size: int = 8
    grid_alpha: float = 0.3
    
    # 热力图配置
    colorscale: str = "Viridis"
    show_colorbar: bool = True
    
    # 全局配置图配置
    scatter_size: int = 10
    scatter_opacity: float = 0.7
    
    # 图表尺寸
    default_height: int = 500
    default_width: int = 800
    
    # 动画配置
    animation_duration: int = 500
    

@dataclass
class UIConfig:
    """UI配置类"""
    # 布局配置
    sidebar_width: str = "300px"
    header_height: str = "60px"
    
    # 组件间距
    component_margin: str = "10px"
    section_padding: str = "20px"
    
    # 字体配置
    font_family: str = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    font_size_base: str = "14px"
    font_size_small: str = "12px"
    font_size_large: str = "16px"
    
    # 响应式断点
    breakpoint_sm: str = "576px"
    breakpoint_md: str = "768px"
    breakpoint_lg: str = "992px"
    breakpoint_xl: str = "1200px"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "app_config.json"):
        self.config_file = config_file
        self.theme = ThemeConfig()
        self.chart = ChartConfig()
        self.ui = UIConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新主题配置
                if 'theme' in config_data:
                    for key, value in config_data['theme'].items():
                        if hasattr(self.theme, key):
                            setattr(self.theme, key, value)
                
                # 更新图表配置
                if 'chart' in config_data:
                    for key, value in config_data['chart'].items():
                        if hasattr(self.chart, key):
                            setattr(self.chart, key, value)
                
                # 更新UI配置
                if 'ui' in config_data:
                    for key, value in config_data['ui'].items():
                        if hasattr(self.ui, key):
                            setattr(self.ui, key, value)
                            
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            config_data = {
                'theme': asdict(self.theme),
                'chart': asdict(self.chart),
                'ui': asdict(self.ui)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_plotly_theme(self) -> Dict[str, Any]:
        """获取Plotly图表主题配置"""
        return {
            'layout': {
                'paper_bgcolor': self.theme.background_color,
                'plot_bgcolor': self.theme.surface_color,
                'font': {
                    'color': self.theme.text_color,
                    'family': self.ui.font_family,
                    'size': 12
                },
                'colorway': self.theme.chart_colors,
                'grid': {
                    'color': self.theme.border_color
                },
                'xaxis': {
                    'gridcolor': self.theme.border_color,
                    'linecolor': self.theme.border_color,
                    'tickcolor': self.theme.text_secondary,
                    'tickfont': {'color': self.theme.text_secondary}
                },
                'yaxis': {
                    'gridcolor': self.theme.border_color,
                    'linecolor': self.theme.border_color,
                    'tickcolor': self.theme.text_secondary,
                    'tickfont': {'color': self.theme.text_secondary}
                }
            }
        }
    
    def get_dash_theme(self) -> str:
        """获取Dash Bootstrap主题"""
        # 返回深色主题
        return "CYBORG"  # Bootstrap深色主题
    
    def update_theme_color(self, color_name: str, color_value: str) -> None:
        """更新主题颜色"""
        if hasattr(self.theme, color_name):
            setattr(self.theme, color_name, color_value)
            self.save_config()
    
    def update_chart_config(self, config_dict: Dict[str, Any]) -> None:
        """更新图表配置"""
        for config_name, config_value in config_dict.items():
            if hasattr(self.chart, config_name):
                setattr(self.chart, config_name, config_value)
        self.save_config()
    
    def get_theme_config(self) -> ThemeConfig:
        """获取主题配置"""
        return self.theme
    
    def get_ui_config(self) -> UIConfig:
        """获取UI配置"""
        return self.ui
    
    def get_chart_config(self) -> ChartConfig:
        """获取图表配置"""
        return self.chart
    
    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.theme = ThemeConfig()
        self.chart = ChartConfig()
        self.ui = UIConfig()
        self.save_config()


# 全局配置实例
config_manager = ConfigManager()


# 便捷访问函数
def get_theme() -> ThemeConfig:
    """获取主题配置"""
    return config_manager.theme


def get_chart_config() -> ChartConfig:
    """获取图表配置"""
    return config_manager.chart


def get_ui_config() -> UIConfig:
    """获取UI配置"""
    return config_manager.ui


def get_plotly_theme() -> Dict[str, Any]:
    """获取Plotly主题"""
    return config_manager.get_plotly_theme()


def get_dash_theme() -> str:
    """获取Dash主题"""
    return config_manager.get_dash_theme()