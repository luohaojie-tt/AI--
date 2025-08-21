# -*- coding: utf-8 -*-
"""
V2.1 数据筛选和搜索功能 - 筛选面板UI组件
提供用户友好的数据筛选和搜索界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, List, Tuple
import threading
import sys
import os
from dataclasses import dataclass
import logging

# 添加项目根目录和子目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'filters'))
sys.path.insert(0, os.path.join(project_root, 'core'))

from filters.filter_models import FilterCriteria, SearchParams, FilterStats
from filters.filter_manager import FilterManager, get_filter_manager
from filters.search_manager import SearchManager, get_search_manager, SearchMatch
from core.data_manager import SNRDataPoint


@dataclass
class FilterPanelConfig:
    """
    筛选面板配置
    """
    # 界面配置
    width: int = 350
    height: int = 600
    padding: int = 10
    
    # 输入验证配置
    validate_input: bool = True
    auto_filter: bool = False  # 是否自动筛选
    debounce_delay: int = 500  # 防抖延迟（毫秒）
    
    # 性能配置
    max_results_display: int = 1000
    enable_async: bool = True
    
    # 样式配置
    primary_color: str = '#3498db'
    success_color: str = '#27ae60'
    warning_color: str = '#f39c12'
    error_color: str = '#e74c3c'


class FilterPanel:
    """
    筛选面板UI组件
    提供数据筛选和搜索的用户界面
    """
    
    def __init__(self, parent: tk.Widget, config: Optional[FilterPanelConfig] = None):
        self.parent = parent
        self.config = config or FilterPanelConfig()
        
        # 管理器实例
        self.filter_manager = get_filter_manager()
        self.search_manager = get_search_manager()
        
        # 数据引用
        self.data: List[SNRDataPoint] = []
        self.filtered_data: List[SNRDataPoint] = []
        self.search_results: List[SearchMatch] = []
        
        # 回调函数
        self.on_filter_changed: Optional[Callable[[List[SNRDataPoint]], None]] = None
        self.on_search_completed: Optional[Callable[[List[SearchMatch]], None]] = None
        self.on_stats_updated: Optional[Callable[[FilterStats], None]] = None
        
        # UI组件
        self.main_frame: Optional[ttk.Frame] = None
        self.filter_frame: Optional[ttk.LabelFrame] = None
        self.search_frame: Optional[ttk.LabelFrame] = None
        self.results_frame: Optional[ttk.LabelFrame] = None
        
        # 筛选控件
        self.pre_min_var = tk.StringVar()
        self.pre_max_var = tk.StringVar()
        self.main_min_var = tk.StringVar()
        self.main_max_var = tk.StringVar()
        self.post_min_var = tk.StringVar()
        self.post_max_var = tk.StringVar()
        self.snr_min_var = tk.StringVar()
        self.snr_max_var = tk.StringVar()
        
        # 搜索控件
        self.search_pre_var = tk.StringVar()
        self.search_main_var = tk.StringVar()
        self.search_post_var = tk.StringVar()
        self.search_snr_var = tk.StringVar()
        self.search_tolerance_var = tk.StringVar(value="0.1")
        self.search_type_var = tk.StringVar(value="exact")
        
        # 状态变量
        self.filter_enabled_var = tk.BooleanVar(value=True)
        self.auto_filter_var = tk.BooleanVar(value=self.config.auto_filter)
        
        # 统计信息
        self.stats_var = tk.StringVar()
        self.performance_var = tk.StringVar()
        
        # 线程控制
        self._filter_thread: Optional[threading.Thread] = None
        self._search_thread: Optional[threading.Thread] = None
        self._debounce_timer: Optional[str] = None
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 创建UI
        self.create_widgets()
        self.setup_bindings()
        
        # 初始化状态
        self.update_stats()
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.parent, padding=self.config.padding)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建筛选区域
        self.create_filter_section()
        
        # 创建搜索区域
        self.create_search_section()
        
        # 创建结果统计区域
        self.create_results_section()
        
        # 创建控制按钮区域
        self.create_control_section()
    
    def create_filter_section(self):
        """创建筛选区域"""
        self.filter_frame = ttk.LabelFrame(
            self.main_frame, 
            text="🔍 数据筛选", 
            padding=self.config.padding
        )
        self.filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 筛选开关
        control_frame = ttk.Frame(self.filter_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.filter_enabled_check = ttk.Checkbutton(
            control_frame,
            text="启用筛选",
            variable=self.filter_enabled_var,
            command=self.on_filter_enabled_changed
        )
        self.filter_enabled_check.pack(side=tk.LEFT)
        
        self.auto_filter_check = ttk.Checkbutton(
            control_frame,
            text="自动筛选",
            variable=self.auto_filter_var,
            command=self.on_auto_filter_changed
        )
        self.auto_filter_check.pack(side=tk.LEFT, padx=(20, 0))
        
        # 参数范围筛选
        params_frame = ttk.LabelFrame(self.filter_frame, text="参数范围", padding=5)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # PRE参数
        self.create_range_input(params_frame, "PRE", self.pre_min_var, self.pre_max_var, 0)
        
        # MAIN参数
        self.create_range_input(params_frame, "MAIN", self.main_min_var, self.main_max_var, 1)
        
        # POST参数
        self.create_range_input(params_frame, "POST", self.post_min_var, self.post_max_var, 2)
        
        # SNR值筛选
        snr_frame = ttk.LabelFrame(self.filter_frame, text="SNR值范围", padding=5)
        snr_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.create_range_input(snr_frame, "SNR", self.snr_min_var, self.snr_max_var, 0, is_float=True)
    
    def create_range_input(self, parent: tk.Widget, label: str, 
                          min_var: tk.StringVar, max_var: tk.StringVar, 
                          row: int, is_float: bool = False):
        """创建范围输入组件"""
        # 标签
        ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10))
        
        # 最小值输入
        ttk.Label(parent, text="最小:").grid(row=row, column=1, sticky=tk.W, padx=(0, 5))
        min_entry = ttk.Entry(parent, textvariable=min_var, width=10)
        min_entry.grid(row=row, column=2, padx=(0, 10))
        
        # 最大值输入
        ttk.Label(parent, text="最大:").grid(row=row, column=3, sticky=tk.W, padx=(0, 5))
        max_entry = ttk.Entry(parent, textvariable=max_var, width=10)
        max_entry.grid(row=row, column=4, padx=(0, 10))
        
        # 清除按钮
        clear_btn = ttk.Button(
            parent, 
            text="清除", 
            command=lambda: self.clear_range(min_var, max_var),
            width=6
        )
        clear_btn.grid(row=row, column=5)
        
        # 输入验证
        if self.config.validate_input:
            if is_float:
                min_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_float), '%P'))
                max_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_float), '%P'))
            else:
                min_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_int), '%P'))
                max_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_int), '%P'))
    
    def create_search_section(self):
        """创建搜索区域"""
        self.search_frame = ttk.LabelFrame(
            self.main_frame, 
            text="🔎 精确搜索", 
            padding=self.config.padding
        )
        self.search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 搜索类型选择
        type_frame = ttk.Frame(self.search_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="搜索类型:").pack(side=tk.LEFT)
        
        exact_radio = ttk.Radiobutton(
            type_frame, 
            text="精确匹配", 
            variable=self.search_type_var, 
            value="exact"
        )
        exact_radio.pack(side=tk.LEFT, padx=(10, 0))
        
        fuzzy_radio = ttk.Radiobutton(
            type_frame, 
            text="模糊匹配", 
            variable=self.search_type_var, 
            value="fuzzy"
        )
        fuzzy_radio.pack(side=tk.LEFT, padx=(10, 0))
        
        # 搜索参数输入
        search_params_frame = ttk.LabelFrame(self.search_frame, text="搜索参数", padding=5)
        search_params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 参数输入网格
        params_grid = ttk.Frame(search_params_frame)
        params_grid.pack(fill=tk.X)
        
        # PRE参数搜索
        ttk.Label(params_grid, text="PRE:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        pre_entry = ttk.Entry(params_grid, textvariable=self.search_pre_var, width=12)
        pre_entry.grid(row=0, column=1, padx=(0, 15))
        
        # MAIN参数搜索
        ttk.Label(params_grid, text="MAIN:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        main_entry = ttk.Entry(params_grid, textvariable=self.search_main_var, width=12)
        main_entry.grid(row=0, column=3, padx=(0, 15))
        
        # POST参数搜索
        ttk.Label(params_grid, text="POST:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        post_entry = ttk.Entry(params_grid, textvariable=self.search_post_var, width=12)
        post_entry.grid(row=1, column=1, padx=(0, 15))
        
        # SNR值搜索
        ttk.Label(params_grid, text="SNR:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        snr_entry = ttk.Entry(params_grid, textvariable=self.search_snr_var, width=12)
        snr_entry.grid(row=1, column=3, padx=(0, 15))
        
        # SNR容差（仅模糊搜索）
        tolerance_frame = ttk.Frame(self.search_frame)
        tolerance_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(tolerance_frame, text="SNR容差:").pack(side=tk.LEFT)
        tolerance_entry = ttk.Entry(
            tolerance_frame, 
            textvariable=self.search_tolerance_var, 
            width=10
        )
        tolerance_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(tolerance_frame, text="(仅模糊搜索)").pack(side=tk.LEFT, padx=(10, 0))
        
        # 搜索按钮
        search_btn_frame = ttk.Frame(self.search_frame)
        search_btn_frame.pack(fill=tk.X)
        
        self.search_btn = ttk.Button(
            search_btn_frame,
            text="🔍 开始搜索",
            command=self.perform_search
        )
        self.search_btn.pack(side=tk.LEFT)
        
        self.clear_search_btn = ttk.Button(
            search_btn_frame,
            text="清除搜索",
            command=self.clear_search
        )
        self.clear_search_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 输入验证
        if self.config.validate_input:
            pre_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_int), '%P'))
            main_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_int), '%P'))
            post_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_int), '%P'))
            snr_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_float), '%P'))
            tolerance_entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_float), '%P'))
    
    def create_results_section(self):
        """创建结果统计区域"""
        self.results_frame = ttk.LabelFrame(
            self.main_frame, 
            text="📊 筛选结果", 
            padding=self.config.padding
        )
        self.results_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 统计信息显示
        stats_frame = ttk.Frame(self.results_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = ttk.Label(
            stats_frame,
            textvariable=self.stats_var,
            font=('Arial', 9),
            foreground=self.config.primary_color
        )
        self.stats_label.pack()
        
        # 性能信息显示
        performance_frame = ttk.Frame(self.results_frame)
        performance_frame.pack(fill=tk.X)
        
        self.performance_label = ttk.Label(
            performance_frame,
            textvariable=self.performance_var,
            font=('Arial', 8),
            foreground='gray'
        )
        self.performance_label.pack()
    
    def create_control_section(self):
        """创建控制按钮区域"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 筛选控制按钮
        self.apply_filter_btn = ttk.Button(
            control_frame,
            text="✅ 应用筛选",
            command=self.apply_filter
        )
        self.apply_filter_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_filter_btn = ttk.Button(
            control_frame,
            text="🔄 重置筛选",
            command=self.reset_filter
        )
        self.reset_filter_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 导出按钮
        self.export_btn = ttk.Button(
            control_frame,
            text="📤 导出结果",
            command=self.export_results
        )
        self.export_btn.pack(side=tk.RIGHT)
    
    def setup_bindings(self):
        """设置事件绑定"""
        # 自动筛选绑定
        if self.config.auto_filter:
            for var in [self.pre_min_var, self.pre_max_var, self.main_min_var, 
                       self.main_max_var, self.post_min_var, self.post_max_var,
                       self.snr_min_var, self.snr_max_var]:
                var.trace('w', self.on_filter_input_changed)
    
    def validate_int(self, value: str) -> bool:
        """验证整数输入"""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def validate_float(self, value: str) -> bool:
        """验证浮点数输入"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def clear_range(self, min_var: tk.StringVar, max_var: tk.StringVar):
        """清除范围输入"""
        min_var.set("")
        max_var.set("")
        
        if self.auto_filter_var.get():
            self.schedule_auto_filter()
    
    def on_filter_enabled_changed(self):
        """筛选开关状态改变"""
        enabled = self.filter_enabled_var.get()
        
        # 更新UI状态
        state = tk.NORMAL if enabled else tk.DISABLED
        
        for widget in self.filter_frame.winfo_children():
            self.set_widget_state_recursive(widget, state)
        
        # 保持开关本身可用
        self.filter_enabled_check.configure(state=tk.NORMAL)
        
        if enabled and self.auto_filter_var.get():
            self.schedule_auto_filter()
        elif not enabled:
            # 禁用筛选时显示所有数据
            self.filtered_data = self.data.copy()
            self.notify_filter_changed()
    
    def set_widget_state_recursive(self, widget: tk.Widget, state: str):
        """递归设置组件状态"""
        try:
            widget.configure(state=state)
        except tk.TclError:
            pass  # 某些组件不支持state属性
        
        for child in widget.winfo_children():
            self.set_widget_state_recursive(child, state)
    
    def on_auto_filter_changed(self):
        """自动筛选开关状态改变"""
        if self.auto_filter_var.get():
            self.setup_bindings()
            self.schedule_auto_filter()
    
    def on_filter_input_changed(self, *args):
        """筛选输入改变"""
        if self.auto_filter_var.get() and self.filter_enabled_var.get():
            self.schedule_auto_filter()
    
    def schedule_auto_filter(self):
        """调度自动筛选（防抖）"""
        # 取消之前的定时器
        if self._debounce_timer:
            self.parent.after_cancel(self._debounce_timer)
        
        # 设置新的定时器
        self._debounce_timer = self.parent.after(
            self.config.debounce_delay, 
            self.apply_filter
        )
    
    def apply_filter(self):
        """应用筛选"""
        if not self.filter_enabled_var.get():
            return
        
        try:
            # 构建筛选条件
            criteria = self.build_filter_criteria()
            
            if criteria.is_empty():
                # 没有筛选条件，显示所有数据
                self.filtered_data = self.data.copy()
            else:
                # 执行筛选
                if self.config.enable_async and len(self.data) > 1000:
                    self.apply_filter_async(criteria)
                    return
                else:
                    self.filtered_data = self.filter_manager.filter_data(self.data, criteria)
            
            # 更新统计信息
            self.update_stats()
            
            # 通知筛选结果改变
            self.notify_filter_changed()
            
        except Exception as e:
            self.logger.error(f"筛选过程中发生错误: {e}")
            messagebox.showerror("筛选错误", f"筛选过程中发生错误:\n{e}")
    
    def apply_filter_async(self, criteria: FilterCriteria):
        """异步应用筛选"""
        def filter_worker():
            try:
                filtered_data = self.filter_manager.filter_data(self.data, criteria)
                
                # 在主线程中更新UI
                self.parent.after(0, lambda: self.on_filter_completed(filtered_data))
                
            except Exception as e:
                self.logger.error(f"异步筛选错误: {e}")
                self.parent.after(0, lambda: messagebox.showerror("筛选错误", f"筛选过程中发生错误:\n{e}"))
        
        # 启动筛选线程
        if self._filter_thread and self._filter_thread.is_alive():
            return  # 已有筛选任务在进行
        
        self._filter_thread = threading.Thread(target=filter_worker, daemon=True)
        self._filter_thread.start()
        
        # 更新UI状态
        self.apply_filter_btn.configure(text="筛选中...", state=tk.DISABLED)
    
    def on_filter_completed(self, filtered_data: List[SNRDataPoint]):
        """筛选完成回调"""
        self.filtered_data = filtered_data
        self.update_stats()
        self.notify_filter_changed()
        
        # 恢复UI状态
        self.apply_filter_btn.configure(text="✅ 应用筛选", state=tk.NORMAL)
    
    def build_filter_criteria(self) -> FilterCriteria:
        """构建筛选条件"""
        criteria = FilterCriteria()
        
        # PRE参数范围
        if self.pre_min_var.get().strip():
            criteria.pre_min = int(self.pre_min_var.get())
        if self.pre_max_var.get().strip():
            criteria.pre_max = int(self.pre_max_var.get())
        
        # MAIN参数范围
        if self.main_min_var.get().strip():
            criteria.main_min = int(self.main_min_var.get())
        if self.main_max_var.get().strip():
            criteria.main_max = int(self.main_max_var.get())
        
        # POST参数范围
        if self.post_min_var.get().strip():
            criteria.post_min = int(self.post_min_var.get())
        if self.post_max_var.get().strip():
            criteria.post_max = int(self.post_max_var.get())
        
        # SNR值范围
        if self.snr_min_var.get().strip():
            criteria.snr_min = float(self.snr_min_var.get())
        if self.snr_max_var.get().strip():
            criteria.snr_max = float(self.snr_max_var.get())
        
        return criteria
    
    def reset_filter(self):
        """重置筛选"""
        # 清除所有输入
        for var in [self.pre_min_var, self.pre_max_var, self.main_min_var, 
                   self.main_max_var, self.post_min_var, self.post_max_var,
                   self.snr_min_var, self.snr_max_var]:
            var.set("")
        
        # 重置数据
        self.filtered_data = self.data.copy()
        
        # 更新统计信息
        self.update_stats()
        
        # 通知筛选结果改变
        self.notify_filter_changed()
    
    def perform_search(self):
        """执行搜索"""
        try:
            # 构建搜索参数
            params = self.build_search_params()
            
            if params.is_empty():
                messagebox.showwarning("搜索提示", "请输入至少一个搜索条件")
                return
            
            # 执行搜索
            if self.config.enable_async and len(self.data) > 1000:
                self.perform_search_async(params)
            else:
                self.search_results = self.search_manager.search_data(self.data, params)
                self.on_search_completed_internal()
            
        except Exception as e:
            self.logger.error(f"搜索过程中发生错误: {e}")
            messagebox.showerror("搜索错误", f"搜索过程中发生错误:\n{e}")
    
    def perform_search_async(self, params: SearchParams):
        """异步执行搜索"""
        def search_worker():
            try:
                search_results = self.search_manager.search_data(self.data, params)
                
                # 在主线程中更新UI
                self.parent.after(0, lambda: self.on_search_completed_async(search_results))
                
            except Exception as e:
                self.logger.error(f"异步搜索错误: {e}")
                self.parent.after(0, lambda: messagebox.showerror("搜索错误", f"搜索过程中发生错误:\n{e}"))
        
        # 启动搜索线程
        if self._search_thread and self._search_thread.is_alive():
            return  # 已有搜索任务在进行
        
        self._search_thread = threading.Thread(target=search_worker, daemon=True)
        self._search_thread.start()
        
        # 更新UI状态
        self.search_btn.configure(text="搜索中...", state=tk.DISABLED)
    
    def on_search_completed_async(self, search_results: List[SearchMatch]):
        """异步搜索完成回调"""
        self.search_results = search_results
        self.on_search_completed_internal()
        
        # 恢复UI状态
        self.search_btn.configure(text="🔍 开始搜索", state=tk.NORMAL)
    
    def on_search_completed_internal(self):
        """搜索完成内部处理"""
        # 更新统计信息
        self.update_search_stats()
        
        # 通知搜索完成
        if self.on_search_completed:
            self.on_search_completed(self.search_results)
        
        # 显示搜索结果摘要
        if self.search_results:
            result_count = len(self.search_results)
            avg_score = sum(m.score for m in self.search_results) / result_count
            messagebox.showinfo(
                "搜索完成", 
                f"找到 {result_count} 个匹配结果\n平均相似度: {avg_score:.3f}"
            )
        else:
            messagebox.showinfo("搜索完成", "未找到匹配的结果")
    
    def build_search_params(self) -> SearchParams:
        """构建搜索参数"""
        params = SearchParams(search_type=self.search_type_var.get())
        
        # 精确参数
        if self.search_pre_var.get().strip():
            params.exact_pre = int(self.search_pre_var.get())
        if self.search_main_var.get().strip():
            params.exact_main = int(self.search_main_var.get())
        if self.search_post_var.get().strip():
            params.exact_post = int(self.search_post_var.get())
        
        # SNR值和容差
        if self.search_snr_var.get().strip():
            params.target_snr = float(self.search_snr_var.get())
            
            if self.search_tolerance_var.get().strip():
                params.snr_tolerance = float(self.search_tolerance_var.get())
        
        return params
    
    def clear_search(self):
        """清除搜索"""
        # 清除搜索输入
        for var in [self.search_pre_var, self.search_main_var, 
                   self.search_post_var, self.search_snr_var]:
            var.set("")
        
        # 重置搜索类型和容差
        self.search_type_var.set("exact")
        self.search_tolerance_var.set("0.1")
        
        # 清除搜索结果
        self.search_results = []
        
        # 更新统计信息
        self.update_search_stats()
    
    def export_results(self):
        """导出筛选结果"""
        if not self.filtered_data:
            messagebox.showwarning("导出提示", "没有可导出的筛选结果")
            return
        
        try:
            from tkinter import filedialog
            import csv
            
            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                title="导出筛选结果",
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
            )
            
            if filename:
                # 导出数据
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # 写入表头
                    writer.writerow(['PRE', 'MAIN', 'POST', 'SNR'])
                    
                    # 写入数据
                    for point in self.filtered_data:
                        writer.writerow([point.pre, point.main, point.post, point.snr])
                
                messagebox.showinfo("导出成功", f"筛选结果已导出到:\n{filename}")
                
        except Exception as e:
            self.logger.error(f"导出错误: {e}")
            messagebox.showerror("导出错误", f"导出过程中发生错误:\n{e}")
    
    def update_stats(self):
        """更新统计信息"""
        if not self.data:
            self.stats_var.set("无数据")
            self.performance_var.set("")
            return
        
        total_count = len(self.data)
        filtered_count = len(self.filtered_data)
        filter_ratio = (filtered_count / total_count * 100) if total_count > 0 else 0
        
        # 基本统计
        stats_text = f"总数据: {total_count} | 筛选结果: {filtered_count} | 筛选率: {filter_ratio:.1f}%"
        
        if self.filtered_data:
            # SNR统计
            snr_values = [p.snr for p in self.filtered_data]
            min_snr = min(snr_values)
            max_snr = max(snr_values)
            avg_snr = sum(snr_values) / len(snr_values)
            
            stats_text += f"\nSNR范围: {min_snr:.3f} ~ {max_snr:.3f} | 平均: {avg_snr:.3f}"
        
        self.stats_var.set(stats_text)
        
        # 性能统计
        filter_stats = self.filter_manager.get_performance_stats()
        search_stats = self.search_manager.get_performance_stats()
        
        perf_text = f"筛选: {filter_stats['total_filters']}次 | 搜索: {search_stats['total_searches']}次"
        if filter_stats['total_filters'] > 0:
            perf_text += f" | 平均筛选时间: {filter_stats['avg_filter_time_ms']:.1f}ms"
        
        self.performance_var.set(perf_text)
        
        # 通知统计信息更新
        if self.on_stats_updated and self.filtered_data:
            filter_stats_obj = FilterStats(
                total_count=total_count,
                filtered_count=filtered_count,
                filter_ratio=filter_ratio / 100,
                min_snr=min(snr_values) if self.filtered_data else 0,
                max_snr=max(snr_values) if self.filtered_data else 0,
                avg_snr=avg_snr if self.filtered_data else 0
            )
            self.on_stats_updated(filter_stats_obj)
    
    def update_search_stats(self):
        """更新搜索统计信息"""
        if self.search_results:
            result_count = len(self.search_results)
            avg_score = sum(m.score for m in self.search_results) / result_count
            
            search_text = f"搜索结果: {result_count}个 | 平均相似度: {avg_score:.3f}"
            
            # 按匹配类型分组统计
            exact_count = sum(1 for m in self.search_results if m.match_type == "exact")
            fuzzy_count = result_count - exact_count
            
            if exact_count > 0 and fuzzy_count > 0:
                search_text += f" | 精确: {exact_count}个, 模糊: {fuzzy_count}个"
            
            # 更新显示（可以添加到现有统计信息中）
            current_stats = self.stats_var.get()
            if "搜索结果:" not in current_stats:
                self.stats_var.set(current_stats + "\n" + search_text)
    
    def notify_filter_changed(self):
        """通知筛选结果改变"""
        if self.on_filter_changed:
            self.on_filter_changed(self.filtered_data)
    
    def set_data(self, data: List[SNRDataPoint]):
        """设置数据"""
        self.data = data.copy()
        self.filtered_data = data.copy()
        self.search_results = []
        
        # 更新统计信息
        self.update_stats()
        
        # 通知数据改变
        self.notify_filter_changed()
    
    def get_filtered_data(self) -> List[SNRDataPoint]:
        """获取筛选后的数据"""
        return self.filtered_data.copy()
    
    def get_search_results(self) -> List[SearchMatch]:
        """获取搜索结果"""
        return self.search_results.copy()
    
    def set_filter_changed_callback(self, callback: Callable[[List[SNRDataPoint]], None]):
        """设置筛选结果改变回调"""
        self.on_filter_changed = callback
    
    def set_search_completed_callback(self, callback: Callable[[List[SearchMatch]], None]):
        """设置搜索完成回调"""
        self.on_search_completed = callback
    
    def set_stats_updated_callback(self, callback: Callable[[FilterStats], None]):
        """设置统计信息更新回调"""
        self.on_stats_updated = callback
    
    def get_widget(self) -> ttk.Frame:
        """获取主组件"""
        return self.main_frame
    
    def destroy(self):
        """销毁组件"""
        # 取消定时器
        if self._debounce_timer:
            self.parent.after_cancel(self._debounce_timer)
        
        # 等待线程结束
        if self._filter_thread and self._filter_thread.is_alive():
            self._filter_thread.join(timeout=1.0)
        
        if self._search_thread and self._search_thread.is_alive():
            self._search_thread.join(timeout=1.0)
        
        # 销毁UI组件
        if self.main_frame:
            self.main_frame.destroy()


# 便捷函数
def create_filter_panel(parent: tk.Widget, 
                       config: Optional[FilterPanelConfig] = None) -> FilterPanel:
    """
    创建筛选面板
    
    Args:
        parent: 父组件
        config: 配置对象
        
    Returns:
        FilterPanel实例
    """
    return FilterPanel(parent, config)


def create_filter_window(title: str = "数据筛选", 
                        config: Optional[FilterPanelConfig] = None) -> Tuple[tk.Toplevel, FilterPanel]:
    """
    创建独立的筛选窗口
    
    Args:
        title: 窗口标题
        config: 配置对象
        
    Returns:
        (窗口对象, 筛选面板对象)
    """
    if config is None:
        config = FilterPanelConfig()
    
    # 创建窗口
    window = tk.Toplevel()
    window.title(title)
    window.geometry(f"{config.width}x{config.height}")
    window.resizable(True, True)
    
    # 创建筛选面板
    panel = FilterPanel(window, config)
    
    return window, panel