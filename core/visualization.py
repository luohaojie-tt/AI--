# -*- coding: utf-8 -*-
"""
SNR可视化工具可视化组件模块
提供现代化的图表组件和可视化功能
"""

import sys
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.config import ConfigManager
from core.data_manager import DataManager, SNRDataPoint, format_hex


class BaseChart:
    """图表基类"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.theme_config = config_manager.get_theme_config()
        self.chart_config = config_manager.get_chart_config()
    
    def _get_base_layout(self, title: str = "") -> Dict[str, Any]:
        """获取基础布局配置"""
        return {
            'title': {
                'text': title,
                'font': {
                    'size': self.chart_config.title_font_size,
                    'color': self.theme_config.text_color,
                    'family': self.chart_config.font_family
                },
                'x': 0.5,
                'xanchor': 'center'
            },
            'paper_bgcolor': self.theme_config.background_color,
            'plot_bgcolor': self.theme_config.surface_color,
            'font': {
                'family': self.chart_config.font_family,
                'size': self.chart_config.axis_font_size,
                'color': self.theme_config.text_color
            },
            'margin': dict(l=60, r=60, t=80, b=60),
            'showlegend': True,
            'legend': {
                'bgcolor': 'rgba(0,0,0,0)',
                'bordercolor': self.theme_config.border_color,
                'borderwidth': 1,
                'font': {'color': self.theme_config.text_color}
            },
            'hoverlabel': {
                'bgcolor': self.theme_config.surface_color,
                'bordercolor': self.theme_config.border_color,
                'font': {'color': self.theme_config.text_color}
            }
        }
    
    def _get_axis_config(self, title: str, is_log: bool = False) -> Dict[str, Any]:
        """获取坐标轴配置"""
        return {
            'title': {
                'text': title,
                'font': {
                    'size': self.chart_config.axis_font_size,
                    'color': self.theme_config.text_color
                }
            },
            'gridcolor': self.theme_config.grid_color,
            'gridwidth': 1,
            'linecolor': self.theme_config.border_color,
            'linewidth': 2,
            'tickfont': {
                'size': self.chart_config.tick_font_size,
                'color': self.theme_config.text_color
            },
            'type': 'log' if is_log else 'linear',
            'showgrid': self.chart_config.show_grid,
            'zeroline': False
        }


class LineChart(BaseChart):
    """折线图组件"""
    
    def create_parameter_trend_chart(self, data: Dict[str, Any], params: Dict[str, Any]) -> go.Figure:
        """创建增强版参数变化趋势图"""
        try:
            fig = go.Figure()
            
            # 获取数据
            grouped_data = data['data']
            group_by = data['group_by']
            
            # 使用更丰富的颜色方案
            colors = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
            ]
            
            # 为每个组创建增强的折线
            for i, (group_key, group_data) in enumerate(grouped_data.items()):
                color = colors[i % len(colors)]
                
                # 排序数据点
                sorted_indices = np.argsort(group_data['x'])
                x_sorted = [group_data['x'][idx] for idx in sorted_indices]
                y_sorted = [group_data['y'][idx] for idx in sorted_indices]
                
                # 创建详细的hover文本
                hover_text = []
                for j, idx in enumerate(sorted_indices):
                    x_val = group_data['x'][idx]
                    y_val = group_data['y'][idx]
                    
                    # 获取完整的参数信息
                    if 'full_data' in group_data and idx < len(group_data['full_data']):
                        point = group_data['full_data'][idx]
                        hover_text.append(
                            f"<b>参数组合</b><br>"
                            f"Pre: {format_hex(point.get('pre', 0))} ({point.get('pre', 0)})<br>"
                            f"Main: {format_hex(point.get('main', 0))} ({point.get('main', 0)})<br>"
                            f"Post: {format_hex(point.get('post', 0))} ({point.get('post', 0)})<br>"
                            f"<b>SNR: {y_val:.2f} dB</b><br>"
                            f"数据点: {j+1}/{len(x_sorted)}"
                        )
                    else:
                        hover_text.append(
                            f"{group_by.upper()}: {format_hex(group_key)} ({group_key})<br>"
                            f"X轴: {format_hex(x_val)} ({x_val})<br>"
                            f"<b>SNR: {y_val:.2f} dB</b><br>"
                            f"数据点: {j+1}/{len(x_sorted)}"
                        )
                
                # 添加主折线
                fig.add_trace(go.Scatter(
                    x=x_sorted,
                    y=y_sorted,
                    mode='lines+markers',
                    name=f"{group_by.upper()}: {format_hex(group_key)}",
                    line=dict(
                        color=color,
                        width=self.chart_config.line_width + 1,
                        shape='spline' if params.get('smooth_lines', True) else 'linear'
                    ),
                    marker=dict(
                        color=color,
                        size=self.chart_config.marker_size + 2,
                        line=dict(color='white', width=2),
                        symbol='circle'
                    ),
                    hovertext=hover_text,
                    hoverinfo='text',
                    connectgaps=False
                ))
                
                # 添加趋势线（如果数据点足够）
                if len(x_sorted) >= 3 and params.get('show_trend', True):
                    z = np.polyfit(x_sorted, y_sorted, min(2, len(x_sorted)-1))
                    p = np.poly1d(z)
                    x_trend = np.linspace(min(x_sorted), max(x_sorted), 100)
                    y_trend = p(x_trend)
                    
                    fig.add_trace(go.Scatter(
                        x=x_trend,
                        y=y_trend,
                        mode='lines',
                        name=f"趋势线 - {format_hex(group_key)}",
                        line=dict(
                            color=color,
                            width=1,
                            dash='dash'
                        ),
                        opacity=0.6,
                        showlegend=False,
                        hoverinfo='skip'
                    ))
            
            # 设置增强的布局
            x_axis_param = params.get('x_axis', 'main')
            layout = self._get_base_layout(f"SNR vs {x_axis_param.upper()} 参数变化轨迹")
            layout.update({
                'xaxis': self._get_axis_config(f"{x_axis_param.upper()} 参数值"),
                'yaxis': self._get_axis_config("SNR (dB)"),
                'hovermode': 'closest',
                'legend': {
                    'bgcolor': 'rgba(0,0,0,0.1)',
                    'bordercolor': self.theme_config.border_color,
                    'borderwidth': 1,
                    'font': {'color': self.theme_config.text_color, 'size': 12},
                    'orientation': 'v',
                    'x': 1.02,
                    'y': 1
                }
            })
            
            fig.update_layout(layout)
            
            # 添加增强的最优点标注
            if params.get('highlight_optimal', True):
                self._add_enhanced_optimal_points_annotation(fig, grouped_data)
            
            # 添加参数变化指示
            if params.get('show_parameter_indicators', True):
                self._add_parameter_change_indicators(fig, grouped_data, x_axis_param)
            
            return fig
            
        except Exception as e:
            logging.error(f"创建折线图失败: {e}")
            return self._create_error_figure(f"折线图创建失败: {str(e)}")
    
    def create_multi_parameter_comparison(self, data_manager: DataManager, params: Dict[str, Any]) -> go.Figure:
        """创建多参数对比图"""
        try:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Pre vs SNR', 'Main vs SNR', 'Post vs SNR', '参数相关性'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"type": "scatter"}]]
            )
            
            data_points = data_manager.data_points
            if not data_points:
                return self._create_error_figure("无数据可显示")
            
            # 提取数据
            pre_values = [point.pre for point in data_points]
            main_values = [point.main for point in data_points]
            post_values = [point.post for point in data_points]
            snr_values = [point.snr for point in data_points]
            
            # Pre vs SNR
            fig.add_trace(
                go.Scatter(x=pre_values, y=snr_values, mode='markers',
                          name='Pre', marker=dict(color=self.theme_config.primary_color)),
                row=1, col=1
            )
            
            # Main vs SNR
            fig.add_trace(
                go.Scatter(x=main_values, y=snr_values, mode='markers',
                          name='Main', marker=dict(color=self.theme_config.secondary_color)),
                row=1, col=2
            )
            
            # Post vs SNR
            fig.add_trace(
                go.Scatter(x=post_values, y=snr_values, mode='markers',
                          name='Post', marker=dict(color=self.theme_config.accent_color)),
                row=2, col=1
            )
            
            # 参数相关性热力图
            corr_data = np.corrcoef([pre_values, main_values, post_values, snr_values])
            fig.add_trace(
                go.Heatmap(
                    z=corr_data,
                    x=['Pre', 'Main', 'Post', 'SNR'],
                    y=['Pre', 'Main', 'Post', 'SNR'],
                    colorscale='RdBu',
                    zmid=0,
                    showscale=True
                ),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                title_text="多参数SNR分析对比",
                showlegend=False,
                **self._get_base_layout()
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"创建多参数对比图失败: {e}")
            return self._create_error_figure(f"多参数对比图创建失败: {str(e)}")
    
    def _add_optimal_points_annotation(self, fig: go.Figure, grouped_data: Dict[str, Any]) -> None:
        """添加最优点标注"""
        try:
            for group_key, group_data in grouped_data.items():
                if not group_data['y']:
                    continue
                
                # 找到最大SNR点
                max_snr_idx = np.argmax(group_data['y'])
                max_x = group_data['x'][max_snr_idx]
                max_y = group_data['y'][max_snr_idx]
                
                # 添加标注
                fig.add_annotation(
                    x=max_x,
                    y=max_y,
                    text=f"最优: {max_y:.2f}dB",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=self.theme_config.accent_color,
                    bgcolor=self.theme_config.surface_color,
                    bordercolor=self.theme_config.accent_color,
                    borderwidth=1,
                    font=dict(color=self.theme_config.text_color, size=10)
                )
        except Exception as e:
            logging.warning(f"添加最优点标注失败: {e}")
    
    def _add_enhanced_optimal_points_annotation(self, fig: go.Figure, grouped_data: Dict[str, Any]) -> None:
        """添加增强的最优点标注"""
        try:
            for group_key, group_data in grouped_data.items():
                if not group_data['y']:
                    continue
                
                # 找到最大SNR点
                max_snr_idx = np.argmax(group_data['y'])
                max_x = group_data['x'][max_snr_idx]
                max_y = group_data['y'][max_snr_idx]
                
                # 添加高亮标记
                fig.add_trace(go.Scatter(
                    x=[max_x],
                    y=[max_y],
                    mode='markers',
                    marker=dict(
                        color='gold',
                        size=15,
                        symbol='star',
                        line=dict(color='orange', width=2)
                    ),
                    name=f"最优点 - {format_hex(group_key)}",
                    showlegend=False,
                    hovertext=f"<b>最优配置</b><br>参数: {format_hex(max_x)}<br><b>SNR: {max_y:.2f} dB</b>",
                    hoverinfo='text'
                ))
                
                # 添加文字标注
                fig.add_annotation(
                    x=max_x,
                    y=max_y + (max(group_data['y']) - min(group_data['y'])) * 0.1,
                    text=f"★ {max_y:.2f}dB",
                    showarrow=False,
                    bgcolor='rgba(255, 215, 0, 0.8)',
                    bordercolor='orange',
                    borderwidth=1,
                    font=dict(color='black', size=11, family='Arial Black')
                )
        except Exception as e:
            logging.warning(f"添加增强最优点标注失败: {e}")
    
    def _add_parameter_change_indicators(self, fig: go.Figure, grouped_data: Dict[str, Any], x_axis_param: str) -> None:
        """添加参数变化指示"""
        try:
            # 为每个组添加参数变化方向指示
            for group_key, group_data in grouped_data.items():
                if len(group_data['x']) < 2:
                    continue
                
                # 计算参数变化趋势
                x_values = group_data['x']
                y_values = group_data['y']
                
                # 找到SNR变化最大的区间
                max_change = 0
                best_start_idx = 0
                for i in range(len(y_values) - 1):
                    change = abs(y_values[i+1] - y_values[i])
                    if change > max_change:
                        max_change = change
                        best_start_idx = i
                
                if max_change > 0.5:  # 只有变化足够大时才显示
                    start_x = x_values[best_start_idx]
                    end_x = x_values[best_start_idx + 1]
                    start_y = y_values[best_start_idx]
                    end_y = y_values[best_start_idx + 1]
                    
                    # 添加变化箭头
                    fig.add_annotation(
                        x=end_x,
                        y=end_y,
                        ax=start_x,
                        ay=start_y,
                        xref='x',
                        yref='y',
                        axref='x',
                        ayref='y',
                        showarrow=True,
                        arrowhead=3,
                        arrowsize=1.5,
                        arrowwidth=3,
                        arrowcolor='rgba(255, 255, 255, 0.7)',
                        opacity=0.8
                    )
        except Exception as e:
            logging.warning(f"添加参数变化指示失败: {e}")
    
    def _create_error_figure(self, error_message: str) -> go.Figure:
        """创建错误显示图表"""
        fig = go.Figure()
        fig.add_annotation(
            text=error_message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(self._get_base_layout("错误"))
        return fig


class HeatmapChart(BaseChart):
    """热力图组件"""
    
    def create_parameter_heatmap(self, data: Dict[str, Any], params: Dict[str, Any]) -> go.Figure:
        """创建参数热力图"""
        try:
            # 获取数据
            matrix = data['matrix']
            x_values = data['x_values']
            y_values = data['y_values']
            x_param = data['x_param']
            y_param = data['y_param']
            fixed_param = data['fixed_param']
            fixed_value = data['fixed_value']
            
            # 创建hover文本
            hover_text = []
            for i, y_val in enumerate(y_values):
                row_text = []
                for j, x_val in enumerate(x_values):
                    snr_val = matrix[i, j]
                    if np.isnan(snr_val):
                        text = f"{x_param.upper()}: {format_hex(x_val)}<br>"
                        text += f"{y_param.upper()}: {format_hex(y_val)}<br>"
                        text += f"{fixed_param.upper()}: {format_hex(fixed_value)}<br>"
                        text += "SNR: 无数据"
                    else:
                        text = f"{x_param.upper()}: {format_hex(x_val)} ({x_val})<br>"
                        text += f"{y_param.upper()}: {format_hex(y_val)} ({y_val})<br>"
                        text += f"{fixed_param.upper()}: {format_hex(fixed_value)} ({fixed_value})<br>"
                        text += f"SNR: {snr_val:.2f} dB"
                    row_text.append(text)
                hover_text.append(row_text)
            
            # 创建热力图
            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=[format_hex(x) for x in x_values],
                y=[format_hex(y) for y in y_values],
                colorscale=params.get('colorscale', 'Viridis'),
                hovertext=hover_text,
                hoverinfo='text',
                colorbar=dict(
                    title="SNR (dB)",
                    titlefont=dict(color=self.theme_config.text_color),
                    tickfont=dict(color=self.theme_config.text_color)
                ),
                showscale=True
            ))
            
            # 设置布局
            title = f"SNR热力图 ({fixed_param.upper()}={format_hex(fixed_value)})"
            layout = self._get_base_layout(title)
            layout.update({
                'xaxis': self._get_axis_config(f"{x_param.upper()} 参数"),
                'yaxis': self._get_axis_config(f"{y_param.upper()} 参数"),
                'hovermode': 'closest'
            })
            
            fig.update_layout(layout)
            
            # 添加最优点标记
            if params.get('highlight_optimal', True):
                self._add_optimal_point_marker(fig, matrix, x_values, y_values)
            
            return fig
            
        except Exception as e:
            logging.error(f"创建热力图失败: {e}")
            return self._create_error_figure(f"热力图创建失败: {str(e)}")
    
    def create_3d_heatmap(self, data_manager: DataManager, params: Dict[str, Any]) -> go.Figure:
        """创建3D热力图"""
        try:
            data_points = data_manager.data_points
            if not data_points:
                return self._create_error_figure("无数据可显示")
            
            # 提取数据
            pre_values = [point.pre for point in data_points]
            main_values = [point.main for point in data_points]
            post_values = [point.post for point in data_points]
            snr_values = [point.snr for point in data_points]
            
            # 创建hover文本
            hover_text = [
                f"Pre: {format_hex(pre)} ({pre})<br>"
                f"Main: {format_hex(main)} ({main})<br>"
                f"Post: {format_hex(post)} ({post})<br>"
                f"SNR: {snr:.2f} dB"
                for pre, main, post, snr in zip(pre_values, main_values, post_values, snr_values)
            ]
            
            # 创建3D散点图
            fig = go.Figure(data=go.Scatter3d(
                x=pre_values,
                y=main_values,
                z=post_values,
                mode='markers',
                marker=dict(
                    size=8,
                    color=snr_values,
                    colorscale=params.get('colorscale', 'Viridis'),
                    colorbar=dict(
                        title="SNR (dB)",
                        titlefont=dict(color=self.theme_config.text_color),
                        tickfont=dict(color=self.theme_config.text_color)
                    ),
                    showscale=True,
                    line=dict(color='white', width=0.5)
                ),
                text=hover_text,
                hoverinfo='text'
            ))
            
            # 设置布局
            layout = self._get_base_layout("3D参数空间SNR分布")
            layout.update({
                'scene': {
                    'xaxis_title': 'Pre 参数',
                    'yaxis_title': 'Main 参数',
                    'zaxis_title': 'Post 参数',
                    'bgcolor': self.theme_config.surface_color,
                    'xaxis': dict(gridcolor=self.theme_config.grid_color),
                    'yaxis': dict(gridcolor=self.theme_config.grid_color),
                    'zaxis': dict(gridcolor=self.theme_config.grid_color)
                }
            })
            
            fig.update_layout(layout)
            
            return fig
            
        except Exception as e:
            logging.error(f"创建3D热力图失败: {e}")
            return self._create_error_figure(f"3D热力图创建失败: {str(e)}")
    
    def create_layered_heatmap(self, data_manager: DataManager, params: Dict[str, Any]) -> go.Figure:
        """创建分层热力图，展示Main参数的影响"""
        try:
            data_points = data_manager.data_points
            if not data_points:
                return self._create_error_figure("无数据可显示")
            
            # 按Main参数分组
            main_groups = {}
            for point in data_points:
                main_val = point.main
                if main_val not in main_groups:
                    main_groups[main_val] = []
                main_groups[main_val].append(point)
            
            # 选择最有代表性的Main值（数据点最多的几个）
            sorted_groups = sorted(main_groups.items(), key=lambda x: len(x[1]), reverse=True)
            top_main_values = [group[0] for group in sorted_groups[:4]]  # 取前4个
            
            # 创建子图
            rows = 2
            cols = 2
            fig = make_subplots(
                rows=rows, cols=cols,
                subplot_titles=[f'Main = {format_hex(val)} ({val})' for val in top_main_values],
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )
            
            # 为每个Main值创建热力图
            for idx, main_val in enumerate(top_main_values):
                row = idx // cols + 1
                col = idx % cols + 1
                
                group_points = main_groups[main_val]
                
                # 提取Pre和Post值
                pre_values = [point.pre for point in group_points]
                post_values = [point.post for point in group_points]
                snr_values = [point.snr for point in group_points]
                
                # 创建网格
                unique_pre = sorted(set(pre_values))
                unique_post = sorted(set(post_values))
                
                if len(unique_pre) < 2 or len(unique_post) < 2:
                    continue
                
                # 创建矩阵
                matrix = np.full((len(unique_post), len(unique_pre)), np.nan)
                hover_matrix = []
                
                for i, post_val in enumerate(unique_post):
                    hover_row = []
                    for j, pre_val in enumerate(unique_pre):
                        # 查找对应的SNR值
                        matching_points = [
                            point for point in group_points 
                            if point.pre == pre_val and point.post == post_val
                        ]
                        if matching_points:
                            snr_val = matching_points[0].snr
                            matrix[i, j] = snr_val
                            hover_text = (
                                f"Pre: {format_hex(pre_val)} ({pre_val})<br>"
                                f"Main: {format_hex(main_val)} ({main_val})<br>"
                                f"Post: {format_hex(post_val)} ({post_val})<br>"
                                f"SNR: {snr_val:.2f} dB"
                            )
                        else:
                            hover_text = "无数据"
                        hover_row.append(hover_text)
                    hover_matrix.append(hover_row)
                
                # 添加热力图
                fig.add_trace(
                    go.Heatmap(
                        z=matrix,
                        x=[format_hex(x) for x in unique_pre],
                        y=[format_hex(y) for y in unique_post],
                        colorscale=params.get('colorscale', 'Viridis'),
                        hovertext=hover_matrix,
                        hoverinfo='text',
                        showscale=(idx == 0),  # 只在第一个子图显示颜色条
                        colorbar=dict(
                            title="SNR (dB)",
                            titlefont=dict(color=self.theme_config.text_color),
                            tickfont=dict(color=self.theme_config.text_color),
                            x=1.02
                        ) if idx == 0 else None
                    ),
                    row=row, col=col
                )
                
                # 添加最优点标记
                if params.get('highlight_optimal', True):
                    valid_mask = ~np.isnan(matrix)
                    if np.any(valid_mask):
                        max_idx = np.unravel_index(np.nanargmax(matrix), matrix.shape)
                        max_post_idx, max_pre_idx = max_idx
                        
                        fig.add_trace(
                            go.Scatter(
                                x=[format_hex(unique_pre[max_pre_idx])],
                                y=[format_hex(unique_post[max_post_idx])],
                                mode='markers',
                                marker=dict(
                                    symbol='star',
                                    size=15,
                                    color='gold',
                                    line=dict(color='black', width=2)
                                ),
                                name=f'最优点 (Main={format_hex(main_val)})',
                                showlegend=(idx == 0),
                                hovertext=f"最优SNR: {matrix[max_post_idx, max_pre_idx]:.2f} dB",
                                hoverinfo='text'
                            ),
                            row=row, col=col
                        )
            
            # 更新布局
            fig.update_layout(
                title={
                    'text': '分层热力图 - Main参数影响分析',
                    'font': {
                        'size': self.chart_config.title_font_size,
                        'color': self.theme_config.text_color,
                        'family': self.chart_config.font_family
                    },
                    'x': 0.5,
                    'xanchor': 'center'
                },
                paper_bgcolor=self.theme_config.background_color,
                plot_bgcolor=self.theme_config.surface_color,
                font=dict(
                    family=self.chart_config.font_family,
                    size=self.chart_config.axis_font_size,
                    color=self.theme_config.text_color
                ),
                height=600
            )
            
            # 更新轴标签
            for i in range(1, rows + 1):
                for j in range(1, cols + 1):
                    fig.update_xaxes(title_text="Pre 参数", row=i, col=j)
                    fig.update_yaxes(title_text="Post 参数", row=i, col=j)
            
            return fig
            
        except Exception as e:
            logging.error(f"创建3D热力图失败: {e}")
            return self._create_error_figure(f"3D热力图创建失败: {str(e)}")
    
    def _add_optimal_point_marker(self, fig: go.Figure, matrix: np.ndarray, 
                                 x_values: List[int], y_values: List[int]) -> None:
        """添加最优点标记"""
        try:
            # 找到最大SNR位置
            valid_mask = ~np.isnan(matrix)
            if not np.any(valid_mask):
                return
            
            max_idx = np.unravel_index(np.nanargmax(matrix), matrix.shape)
            max_y_idx, max_x_idx = max_idx
            
            # 添加最优点标记
            fig.add_trace(go.Scatter(
                x=[format_hex(x_values[max_x_idx])],
                y=[format_hex(y_values[max_y_idx])],
                mode='markers',
                marker=dict(
                    symbol='star',
                    size=20,
                    color='gold',
                    line=dict(color='black', width=2)
                ),
                name='最优配置',
                hovertext=f"最优SNR: {matrix[max_y_idx, max_x_idx]:.2f} dB",
                hoverinfo='text'
            ))
        except Exception as e:
            logging.warning(f"添加最优点标记失败: {e}")
    
    def _create_error_figure(self, error_message: str) -> go.Figure:
        """创建错误显示图表"""
        fig = go.Figure()
        fig.add_annotation(
            text=error_message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(self._get_base_layout("错误"))
        return fig


class GlobalConfigChart(BaseChart):
    """全局配置图组件"""
    
    def create_global_overview(self, data: Dict[str, Any], params: Dict[str, Any]) -> go.Figure:
        """创建全局配置概览图"""
        try:
            scatter_data = data['scatter_data']
            top_configs = data['top_configs']
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    '3D参数空间分布',
                    'SNR分布直方图',
                    '最优配置Top10',
                    '参数范围统计'
                ),
                specs=[
                    [{"type": "scatter3d"}, {"type": "histogram"}],
                    [{"type": "bar"}, {"type": "bar"}]
                ]
            )
            
            # 3D散点图
            hover_text_3d = [
                f"Pre: {format_hex(pre)} ({pre})<br>"
                f"Main: {format_hex(main)} ({main})<br>"
                f"Post: {format_hex(post)} ({post})<br>"
                f"SNR: {snr:.2f} dB"
                for pre, main, post, snr in zip(
                    scatter_data['pre'], scatter_data['main'],
                    scatter_data['post'], scatter_data['snr']
                )
            ]
            
            fig.add_trace(
                go.Scatter3d(
                    x=scatter_data['pre'],
                    y=scatter_data['main'],
                    z=scatter_data['post'],
                    mode='markers',
                    marker=dict(
                        size=5,
                        color=scatter_data['snr'],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(x=0.45, len=0.4)
                    ),
                    text=hover_text_3d,
                    hoverinfo='text',
                    name='数据点'
                ),
                row=1, col=1
            )
            
            # SNR分布直方图
            fig.add_trace(
                go.Histogram(
                    x=scatter_data['snr'],
                    nbinsx=30,
                    name='SNR分布',
                    marker_color=self.theme_config.primary_color
                ),
                row=1, col=2
            )
            
            # 最优配置柱状图
            if top_configs:
                top_snr_values = [config['snr'] for config in top_configs[:10]]
                top_labels = [f"#{i+1}" for i in range(len(top_snr_values))]
                
                fig.add_trace(
                    go.Bar(
                        x=top_labels,
                        y=top_snr_values,
                        name='Top配置',
                        marker_color=self.theme_config.accent_color,
                        text=[f"{snr:.2f}" for snr in top_snr_values],
                        textposition='auto'
                    ),
                    row=2, col=1
                )
            
            # 参数范围统计
            param_ranges = {
                'Pre': (min(scatter_data['pre']), max(scatter_data['pre'])),
                'Main': (min(scatter_data['main']), max(scatter_data['main'])),
                'Post': (min(scatter_data['post']), max(scatter_data['post']))
            }
            
            range_values = [max_val - min_val for min_val, max_val in param_ranges.values()]
            
            fig.add_trace(
                go.Bar(
                    x=list(param_ranges.keys()),
                    y=range_values,
                    name='参数范围',
                    marker_color=self.theme_config.secondary_color,
                    text=[f"{val}" for val in range_values],
                    textposition='auto'
                ),
                row=2, col=2
            )
            
            # 更新布局
            layout = self._get_base_layout("全局配置分析概览")
            layout.update({
                'showlegend': False,
                'scene': {
                    'xaxis_title': 'Pre',
                    'yaxis_title': 'Main',
                    'zaxis_title': 'Post'
                }
            })
            
            fig.update_layout(layout)
            
            return fig
            
        except Exception as e:
            logging.error(f"创建全局配置图失败: {e}")
            return self._create_error_figure(f"全局配置图创建失败: {str(e)}")
    
    def create_enhanced_global_overview(self, data: Dict[str, Any], params: Dict[str, Any]) -> go.Figure:
        """创建增强的全局配置概览图，清晰展示Pre/Main/Post三个参数与SNR的对应关系"""
        try:
            scatter_data = data['scatter_data']
            top_configs = data['top_configs']
            
            # 创建更合理的子图布局
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Pre参数与SNR关系',
                    'Main参数与SNR关系',
                    'Post参数与SNR关系',
                    '参数组合3D空间',
                    '最优配置Top10',
                    'SNR性能分布'
                ),
                specs=[
                    [{"type": "scatter"}, {"type": "scatter"}],
                    [{"type": "scatter"}, {"type": "scatter3d"}],
                    [{"type": "bar"}, {"type": "histogram"}]
                ],
                vertical_spacing=0.08,
                horizontal_spacing=0.1
            )
            
            # 1. Pre参数与SNR关系散点图
            fig.add_trace(
                go.Scatter(
                    x=scatter_data['pre'],
                    y=scatter_data['snr'],
                    mode='markers',
                    marker=dict(
                        size=6,
                        color=scatter_data['main'],
                        colorscale='Viridis',
                        showscale=False,
                        opacity=0.7
                    ),
                    text=[
                        f"Pre: {format_hex(pre)} ({pre})<br>"
                        f"Main: {format_hex(main)} ({main})<br>"
                        f"Post: {format_hex(post)} ({post})<br>"
                        f"SNR: {snr:.2f} dB"
                        for pre, main, post, snr in zip(
                            scatter_data['pre'], scatter_data['main'],
                            scatter_data['post'], scatter_data['snr']
                        )
                    ],
                    hoverinfo='text',
                    name='Pre-SNR'
                ),
                row=1, col=1
            )
            
            # 2. Main参数与SNR关系散点图
            fig.add_trace(
                go.Scatter(
                    x=scatter_data['main'],
                    y=scatter_data['snr'],
                    mode='markers',
                    marker=dict(
                        size=6,
                        color=scatter_data['post'],
                        colorscale='Plasma',
                        showscale=False,
                        opacity=0.7
                    ),
                    text=[
                        f"Pre: {format_hex(pre)} ({pre})<br>"
                        f"Main: {format_hex(main)} ({main})<br>"
                        f"Post: {format_hex(post)} ({post})<br>"
                        f"SNR: {snr:.2f} dB"
                        for pre, main, post, snr in zip(
                            scatter_data['pre'], scatter_data['main'],
                            scatter_data['post'], scatter_data['snr']
                        )
                    ],
                    hoverinfo='text',
                    name='Main-SNR'
                ),
                row=1, col=2
            )
            
            # 3. Post参数与SNR关系散点图
            fig.add_trace(
                go.Scatter(
                    x=scatter_data['post'],
                    y=scatter_data['snr'],
                    mode='markers',
                    marker=dict(
                        size=6,
                        color=scatter_data['pre'],
                        colorscale='Cividis',
                        showscale=False,
                        opacity=0.7
                    ),
                    text=[
                        f"Pre: {format_hex(pre)} ({pre})<br>"
                        f"Main: {format_hex(main)} ({main})<br>"
                        f"Post: {format_hex(post)} ({post})<br>"
                        f"SNR: {snr:.2f} dB"
                        for pre, main, post, snr in zip(
                            scatter_data['pre'], scatter_data['main'],
                            scatter_data['post'], scatter_data['snr']
                        )
                    ],
                    hoverinfo='text',
                    name='Post-SNR'
                ),
                row=2, col=1
            )
            
            # 4. 3D参数空间分布
            hover_text_3d = [
                f"Pre: {format_hex(pre)} ({pre})<br>"
                f"Main: {format_hex(main)} ({main})<br>"
                f"Post: {format_hex(post)} ({post})<br>"
                f"SNR: {snr:.2f} dB"
                for pre, main, post, snr in zip(
                    scatter_data['pre'], scatter_data['main'],
                    scatter_data['post'], scatter_data['snr']
                )
            ]
            
            fig.add_trace(
                go.Scatter3d(
                    x=scatter_data['pre'],
                    y=scatter_data['main'],
                    z=scatter_data['post'],
                    mode='markers',
                    marker=dict(
                        size=4,
                        color=scatter_data['snr'],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(
                            title="SNR (dB)",
                            titlefont=dict(color=self.theme_config.text_color),
                            tickfont=dict(color=self.theme_config.text_color),
                            x=0.85,
                            len=0.3
                        )
                    ),
                    text=hover_text_3d,
                    hoverinfo='text',
                    name='3D分布'
                ),
                row=2, col=2
            )
            
            # 5. 最优配置Top10
            if top_configs:
                top_snr_values = [config['snr'] for config in top_configs[:10]]
                top_labels = [
                    f"#{i+1}<br>P:{format_hex(config['pre'])}<br>M:{format_hex(config['main'])}<br>Po:{format_hex(config['post'])}"
                    for i, config in enumerate(top_configs[:10])
                ]
                
                fig.add_trace(
                    go.Bar(
                        x=list(range(1, len(top_snr_values) + 1)),
                        y=top_snr_values,
                        name='Top配置',
                        marker=dict(
                            color=top_snr_values,
                            colorscale='RdYlGn',
                            showscale=False
                        ),
                        text=[f"{snr:.2f}dB" for snr in top_snr_values],
                        textposition='auto',
                        hovertext=top_labels,
                        hoverinfo='text'
                    ),
                    row=3, col=1
                )
            
            # 6. SNR性能分布直方图
            fig.add_trace(
                go.Histogram(
                    x=scatter_data['snr'],
                    nbinsx=25,
                    name='SNR分布',
                    marker=dict(
                        color=self.theme_config.primary_color,
                        opacity=0.7
                    ),
                    showlegend=False
                ),
                row=3, col=2
            )
            
            # 更新布局
            layout = self._get_base_layout("增强全局配置分析 - Pre/Main/Post参数与SNR关系")
            layout.update({
                'showlegend': False,
                'height': 900,
                'scene': {
                    'xaxis_title': 'Pre参数',
                    'yaxis_title': 'Main参数',
                    'zaxis_title': 'Post参数',
                    'bgcolor': self.theme_config.surface_color,
                    'xaxis': dict(gridcolor=self.theme_config.grid_color),
                    'yaxis': dict(gridcolor=self.theme_config.grid_color),
                    'zaxis': dict(gridcolor=self.theme_config.grid_color)
                }
            })
            
            # 更新各个子图的轴标签
            fig.update_xaxes(title_text="Pre参数值", row=1, col=1)
            fig.update_yaxes(title_text="SNR (dB)", row=1, col=1)
            
            fig.update_xaxes(title_text="Main参数值", row=1, col=2)
            fig.update_yaxes(title_text="SNR (dB)", row=1, col=2)
            
            fig.update_xaxes(title_text="Post参数值", row=2, col=1)
            fig.update_yaxes(title_text="SNR (dB)", row=2, col=1)
            
            fig.update_xaxes(title_text="配置排名", row=3, col=1)
            fig.update_yaxes(title_text="SNR (dB)", row=3, col=1)
            
            fig.update_xaxes(title_text="SNR (dB)", row=3, col=2)
            fig.update_yaxes(title_text="频次", row=3, col=2)
            
            fig.update_layout(layout)
            
            return fig
            
        except Exception as e:
            logging.error(f"创建增强全局配置图失败: {e}")
            return self._create_error_figure(f"增强全局配置图创建失败: {str(e)}")
    
    def create_parameter_correlation_matrix(self, data_manager: DataManager) -> go.Figure:
        """创建参数相关性矩阵"""
        try:
            data_points = data_manager.data_points
            if not data_points:
                return self._create_error_figure("无数据可显示")
            
            # 创建数据矩阵
            data_matrix = np.array([
                [point.pre for point in data_points],
                [point.main for point in data_points],
                [point.post for point in data_points],
                [point.snr for point in data_points]
            ])
            
            # 计算相关性矩阵
            corr_matrix = np.corrcoef(data_matrix)
            
            # 创建标签
            labels = ['Pre', 'Main', 'Post', 'SNR']
            
            # 创建hover文本
            hover_text = []
            for i in range(len(labels)):
                row_text = []
                for j in range(len(labels)):
                    text = f"{labels[i]} vs {labels[j]}<br>相关系数: {corr_matrix[i, j]:.3f}"
                    row_text.append(text)
                hover_text.append(row_text)
            
            # 创建热力图
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=labels,
                y=labels,
                colorscale='RdBu',
                zmid=0,
                zmin=-1,
                zmax=1,
                hovertext=hover_text,
                hoverinfo='text',
                colorbar=dict(
                    title="相关系数",
                    titlefont=dict(color=self.theme_config.text_color),
                    tickfont=dict(color=self.theme_config.text_color)
                )
            ))
            
            # 添加数值标注
            for i in range(len(labels)):
                for j in range(len(labels)):
                    fig.add_annotation(
                        x=j, y=i,
                        text=f"{corr_matrix[i, j]:.2f}",
                        showarrow=False,
                        font=dict(
                            color='white' if abs(corr_matrix[i, j]) > 0.5 else 'black',
                            size=12
                        )
                    )
            
            # 设置布局
            layout = self._get_base_layout("参数相关性分析矩阵")
            layout.update({
                'xaxis': self._get_axis_config("参数"),
                'yaxis': self._get_axis_config("参数")
            })
            
            fig.update_layout(layout)
            
            return fig
            
        except Exception as e:
            logging.error(f"创建相关性矩阵失败: {e}")
            return self._create_error_figure(f"相关性矩阵创建失败: {str(e)}")
    
    def _create_error_figure(self, error_message: str) -> go.Figure:
        """创建错误显示图表"""
        fig = go.Figure()
        fig.add_annotation(
            text=error_message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(self._get_base_layout("错误"))
        return fig


class VisualizationManager:
    """可视化管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.line_chart = LineChart(config_manager)
        self.heatmap_chart = HeatmapChart(config_manager)
        self.global_config_chart = GlobalConfigChart(config_manager)
    
    def create_chart(self, chart_type: str, data: Any, params: Dict[str, Any]) -> go.Figure:
        """创建指定类型的图表"""
        try:
            if chart_type == 'line':
                return self.line_chart.create_parameter_trend_chart(data, params)
            elif chart_type == 'line_multi':
                return self.line_chart.create_multi_parameter_comparison(data, params)
            elif chart_type == 'heatmap':
                return self.heatmap_chart.create_parameter_heatmap(data, params)
            elif chart_type == 'heatmap_3d':
                return self.heatmap_chart.create_3d_heatmap(data, params)
            elif chart_type == 'heatmap_layered':
                return self.heatmap_chart.create_layered_heatmap(data, params)
            elif chart_type == 'global':
                return self.global_config_chart.create_global_overview(data, params)
            elif chart_type == 'global_enhanced':
                return self.global_config_chart.create_enhanced_global_overview(data, params)
            elif chart_type == 'correlation':
                return self.global_config_chart.create_parameter_correlation_matrix(data)
            else:
                raise ValueError(f"不支持的图表类型: {chart_type}")
        except Exception as e:
            logging.error(f"创建图表失败: {e}")
            return self._create_error_figure(f"图表创建失败: {str(e)}")
    
    def _create_error_figure(self, error_message: str) -> go.Figure:
        """创建错误显示图表"""
        fig = go.Figure()
        fig.add_annotation(
            text=error_message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        
        theme_config = self.config_manager.get_theme_config()
        fig.update_layout(
            paper_bgcolor=theme_config.background_color,
            plot_bgcolor=theme_config.surface_color,
            font=dict(color=theme_config.text_color)
        )
        
        return fig