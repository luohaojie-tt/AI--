# -*- coding: utf-8 -*-
"""
V2.1 数据筛选和搜索功能 - 搜索面板UI组件
提供专业的数据搜索界面和结果展示
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, List, Tuple
import threading
import sys
from dataclasses import dataclass
import logging
import json
import os
from datetime import datetime

# 添加项目根目录和子目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'filters'))
sys.path.insert(0, os.path.join(project_root, 'core'))

from filters.filter_models import SearchParams, FilterStats
from filters.search_manager import SearchManager, get_search_manager, SearchMatch
from core.data_manager import SNRDataPoint


@dataclass
class SearchPanelConfig:
    """
    搜索面板配置
    """
    # 界面配置
    width: int = 400
    height: int = 700
    padding: int = 10
    
    # 搜索配置
    max_history_items: int = 20
    auto_save_history: bool = True
    default_tolerance: float = 0.1
    
    # 结果显示配置
    max_results_display: int = 100
    result_page_size: int = 20
    show_score_details: bool = True
    
    # 性能配置
    enable_async: bool = True
    search_timeout: int = 30  # 秒
    
    # 样式配置
    primary_color: str = '#2ecc71'
    secondary_color: str = '#3498db'
    highlight_color: str = '#f39c12'
    error_color: str = '#e74c3c'


@dataclass
class SearchHistoryItem:
    """
    搜索历史项
    """
    timestamp: str
    params: SearchParams
    result_count: int
    avg_score: float
    description: str


class SearchResultsTree:
    """
    搜索结果树形显示组件
    """
    
    def __init__(self, parent: tk.Widget, config: SearchPanelConfig):
        self.parent = parent
        self.config = config
        
        # 创建树形控件
        self.tree_frame = ttk.Frame(parent)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建树形视图
        columns = ('index', 'pre', 'main', 'post', 'snr', 'score', 'type')
        self.tree = ttk.Treeview(
            self.tree_frame, 
            columns=columns, 
            show='tree headings',
            height=10
        )
        
        # 设置列标题和宽度
        self.tree.heading('#0', text='序号')
        self.tree.heading('index', text='索引')
        self.tree.heading('pre', text='PRE')
        self.tree.heading('main', text='MAIN')
        self.tree.heading('post', text='POST')
        self.tree.heading('snr', text='SNR')
        self.tree.heading('score', text='相似度')
        self.tree.heading('type', text='匹配类型')
        
        self.tree.column('#0', width=60, minwidth=50)
        self.tree.column('index', width=60, minwidth=50)
        self.tree.column('pre', width=80, minwidth=60)
        self.tree.column('main', width=80, minwidth=60)
        self.tree.column('post', width=80, minwidth=60)
        self.tree.column('snr', width=100, minwidth=80)
        self.tree.column('score', width=100, minwidth=80)
        self.tree.column('type', width=80, minwidth=60)
        
        # 添加滚动条
        v_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定事件
        self.tree.bind('<Double-1>', self.on_item_double_click)
        self.tree.bind('<Button-3>', self.on_right_click)
        
        # 回调函数
        self.on_item_selected: Optional[Callable[[SearchMatch], None]] = None
        
        # 当前结果
        self.current_results: List[SearchMatch] = []
        self.current_page = 0
        self.total_pages = 0
    
    def update_results(self, results: List[SearchMatch]):
        """更新搜索结果"""
        self.current_results = results
        self.current_page = 0
        self.total_pages = (len(results) + self.config.result_page_size - 1) // self.config.result_page_size
        
        self.refresh_display()
    
    def refresh_display(self):
        """刷新显示"""
        # 清除现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.current_results:
            return
        
        # 计算当前页的结果范围
        start_idx = self.current_page * self.config.result_page_size
        end_idx = min(start_idx + self.config.result_page_size, len(self.current_results))
        
        # 添加结果项
        for i, match in enumerate(self.current_results[start_idx:end_idx], start_idx + 1):
            # 根据匹配类型设置颜色标签
            tags = []
            if match.match_type == "exact":
                tags.append('exact')
            elif match.score > 0.9:
                tags.append('high_score')
            elif match.score > 0.7:
                tags.append('medium_score')
            else:
                tags.append('low_score')
            
            # 插入项目
            item_id = self.tree.insert(
                '', 'end',
                text=str(i),
                values=(
                    getattr(match.point, 'index', i),
                    match.point.pre,
                    match.point.main,
                    match.point.post,
                    f"{match.point.snr:.4f}",
                    f"{match.score:.4f}",
                    match.match_type
                ),
                tags=tags
            )
        
        # 配置标签样式
        self.tree.tag_configure('exact', background='#d5f4e6')
        self.tree.tag_configure('high_score', background='#fef9e7')
        self.tree.tag_configure('medium_score', background='#eaf2f8')
        self.tree.tag_configure('low_score', background='#fdedec')
    
    def on_item_double_click(self, event):
        """双击项目事件"""
        selection = self.tree.selection()
        if selection and self.on_item_selected:
            item = self.tree.item(selection[0])
            index = int(item['text']) - 1
            
            # 计算实际索引
            actual_index = self.current_page * self.config.result_page_size + (index % self.config.result_page_size)
            
            if 0 <= actual_index < len(self.current_results):
                self.on_item_selected(self.current_results[actual_index])
    
    def on_right_click(self, event):
        """右键菜单"""
        selection = self.tree.selection()
        if selection:
            # 创建右键菜单
            context_menu = tk.Menu(self.parent, tearoff=0)
            context_menu.add_command(label="查看详情", command=lambda: self.show_item_details(selection[0]))
            context_menu.add_command(label="复制参数", command=lambda: self.copy_item_params(selection[0]))
            context_menu.add_separator()
            context_menu.add_command(label="导出选中项", command=lambda: self.export_selected_item(selection[0]))
            
            # 显示菜单
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def show_item_details(self, item_id: str):
        """显示项目详情"""
        item = self.tree.item(item_id)
        index = int(item['text']) - 1
        actual_index = self.current_page * self.config.result_page_size + (index % self.config.result_page_size)
        
        if 0 <= actual_index < len(self.current_results):
            match = self.current_results[actual_index]
            
            # 创建详情窗口
            detail_window = tk.Toplevel(self.parent)
            detail_window.title("搜索结果详情")
            detail_window.geometry("400x300")
            detail_window.resizable(False, False)
            
            # 详情内容
            detail_text = tk.Text(detail_window, wrap=tk.WORD, padx=10, pady=10)
            detail_text.pack(fill=tk.BOTH, expand=True)
            
            details = f"""搜索结果详情

参数配置:
  PRE: {match.point.pre}
  MAIN: {match.point.main}
  POST: {match.point.post}
  SNR: {match.point.snr:.6f}

匹配信息:
  匹配类型: {match.match_type}
  相似度得分: {match.score:.6f}
  匹配字段: {', '.join(match.matched_fields) if match.matched_fields else '无'}

索引信息:
  数据索引: {getattr(match.point, 'index', '未知')}
  结果排序: {actual_index + 1}
"""
            
            detail_text.insert(tk.END, details)
            detail_text.configure(state=tk.DISABLED)
    
    def copy_item_params(self, item_id: str):
        """复制项目参数"""
        item = self.tree.item(item_id)
        values = item['values']
        
        # 构建参数字符串
        params_str = f"PRE={values[1]}, MAIN={values[2]}, POST={values[3]}, SNR={values[4]}"
        
        # 复制到剪贴板
        self.parent.clipboard_clear()
        self.parent.clipboard_append(params_str)
        
        messagebox.showinfo("复制成功", f"参数已复制到剪贴板:\n{params_str}")
    
    def export_selected_item(self, item_id: str):
        """导出选中项"""
        # 这里可以实现导出功能
        messagebox.showinfo("导出功能", "导出功能将在后续版本中实现")
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.refresh_display()
            return True
        return False
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_display()
            return True
        return False
    
    def get_page_info(self) -> Tuple[int, int, int]:
        """获取分页信息"""
        return self.current_page + 1, self.total_pages, len(self.current_results)


class SearchPanel:
    """
    搜索面板UI组件
    提供专业的数据搜索界面和结果展示
    """
    
    def __init__(self, parent: tk.Widget, config: Optional[SearchPanelConfig] = None):
        self.parent = parent
        self.config = config or SearchPanelConfig()
        
        # 管理器实例
        self.search_manager = get_search_manager()
        
        # 数据引用
        self.data: List[SNRDataPoint] = []
        self.search_results: List[SearchMatch] = []
        self.search_history: List[SearchHistoryItem] = []
        
        # 回调函数
        self.on_search_completed: Optional[Callable[[List[SearchMatch]], None]] = None
        self.on_result_selected: Optional[Callable[[SearchMatch], None]] = None
        
        # UI组件
        self.main_frame: Optional[ttk.Frame] = None
        self.search_frame: Optional[ttk.LabelFrame] = None
        self.history_frame: Optional[ttk.LabelFrame] = None
        self.results_frame: Optional[ttk.LabelFrame] = None
        
        # 搜索控件变量
        self.search_pre_var = tk.StringVar()
        self.search_main_var = tk.StringVar()
        self.search_post_var = tk.StringVar()
        self.search_snr_var = tk.StringVar()
        self.search_tolerance_var = tk.StringVar(value=str(self.config.default_tolerance))
        self.search_type_var = tk.StringVar(value="exact")
        
        # 搜索选项
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.include_partial_var = tk.BooleanVar(value=True)
        self.sort_by_score_var = tk.BooleanVar(value=True)
        
        # 状态变量
        self.search_status_var = tk.StringVar(value="就绪")
        self.result_info_var = tk.StringVar()
        
        # 结果显示组件
        self.results_tree: Optional[SearchResultsTree] = None
        
        # 线程控制
        self._search_thread: Optional[threading.Thread] = None
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 创建UI
        self.create_widgets()
        self.setup_bindings()
        
        # 加载搜索历史
        self.load_search_history()
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.parent, padding=self.config.padding)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建搜索参数区域
        self.create_search_section()
        
        # 创建搜索历史区域
        self.create_history_section()
        
        # 创建搜索结果区域
        self.create_results_section()
        
        # 创建状态栏
        self.create_status_section()
    
    def create_search_section(self):
        """创建搜索参数区域"""
        self.search_frame = ttk.LabelFrame(
            self.main_frame, 
            text="🔍 搜索参数", 
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
            value="exact",
            command=self.on_search_type_changed
        )
        exact_radio.pack(side=tk.LEFT, padx=(10, 0))
        
        fuzzy_radio = ttk.Radiobutton(
            type_frame, 
            text="模糊匹配", 
            variable=self.search_type_var, 
            value="fuzzy",
            command=self.on_search_type_changed
        )
        fuzzy_radio.pack(side=tk.LEFT, padx=(10, 0))
        
        # 参数输入区域
        params_frame = ttk.LabelFrame(self.search_frame, text="参数值", padding=5)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建参数输入网格
        self.create_parameter_inputs(params_frame)
        
        # SNR搜索区域
        snr_frame = ttk.LabelFrame(self.search_frame, text="SNR搜索", padding=5)
        snr_frame.pack(fill=tk.X, pady=(0, 10))
        
        # SNR值输入
        snr_input_frame = ttk.Frame(snr_frame)
        snr_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(snr_input_frame, text="目标SNR:").pack(side=tk.LEFT)
        snr_entry = ttk.Entry(snr_input_frame, textvariable=self.search_snr_var, width=15)
        snr_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(snr_input_frame, text="容差:").pack(side=tk.LEFT)
        tolerance_entry = ttk.Entry(snr_input_frame, textvariable=self.search_tolerance_var, width=10)
        tolerance_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # 搜索选项
        options_frame = ttk.LabelFrame(self.search_frame, text="搜索选项", padding=5)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill=tk.X)
        
        ttk.Checkbutton(
            options_grid, 
            text="区分大小写", 
            variable=self.case_sensitive_var
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        ttk.Checkbutton(
            options_grid, 
            text="包含部分匹配", 
            variable=self.include_partial_var
        ).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Checkbutton(
            options_grid, 
            text="按相似度排序", 
            variable=self.sort_by_score_var
        ).grid(row=0, column=2, sticky=tk.W)
        
        # 搜索控制按钮
        control_frame = ttk.Frame(self.search_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.search_btn = ttk.Button(
            control_frame,
            text="🔍 开始搜索",
            command=self.perform_search
        )
        self.search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(
            control_frame,
            text="🗑️ 清除",
            command=self.clear_search
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_search_btn = ttk.Button(
            control_frame,
            text="💾 保存搜索",
            command=self.save_current_search
        )
        self.save_search_btn.pack(side=tk.RIGHT)
    
    def create_parameter_inputs(self, parent: tk.Widget):
        """创建参数输入组件"""
        # PRE参数
        pre_frame = ttk.Frame(parent)
        pre_frame.grid(row=0, column=0, sticky=tk.W, padx=(0, 20), pady=2)
        ttk.Label(pre_frame, text="PRE:").pack(side=tk.LEFT)
        pre_entry = ttk.Entry(pre_frame, textvariable=self.search_pre_var, width=12)
        pre_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # MAIN参数
        main_frame = ttk.Frame(parent)
        main_frame.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=2)
        ttk.Label(main_frame, text="MAIN:").pack(side=tk.LEFT)
        main_entry = ttk.Entry(main_frame, textvariable=self.search_main_var, width=12)
        main_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # POST参数
        post_frame = ttk.Frame(parent)
        post_frame.grid(row=1, column=0, sticky=tk.W, padx=(0, 20), pady=2)
        ttk.Label(post_frame, text="POST:").pack(side=tk.LEFT)
        post_entry = ttk.Entry(post_frame, textvariable=self.search_post_var, width=12)
        post_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 输入验证
        for entry in [pre_entry, main_entry, post_entry]:
            entry.configure(validate='key', validatecommand=(self.parent.register(self.validate_int), '%P'))
    
    def create_history_section(self):
        """创建搜索历史区域"""
        self.history_frame = ttk.LabelFrame(
            self.main_frame, 
            text="📚 搜索历史", 
            padding=self.config.padding
        )
        self.history_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 历史列表框架
        history_list_frame = ttk.Frame(self.history_frame)
        history_list_frame.pack(fill=tk.X)
        
        # 历史列表
        self.history_listbox = tk.Listbox(
            history_list_frame, 
            height=4,
            selectmode=tk.SINGLE
        )
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 历史列表滚动条
        history_scrollbar = ttk.Scrollbar(
            history_list_frame, 
            orient=tk.VERTICAL, 
            command=self.history_listbox.yview
        )
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        # 历史操作按钮
        history_btn_frame = ttk.Frame(self.history_frame)
        history_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            history_btn_frame,
            text="📋 应用",
            command=self.apply_history_search,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            history_btn_frame,
            text="🗑️ 删除",
            command=self.delete_history_item,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            history_btn_frame,
            text="🧹 清空",
            command=self.clear_history,
            width=8
        ).pack(side=tk.RIGHT)
        
        # 绑定双击事件
        self.history_listbox.bind('<Double-1>', lambda e: self.apply_history_search())
    
    def create_results_section(self):
        """创建搜索结果区域"""
        self.results_frame = ttk.LabelFrame(
            self.main_frame, 
            text="📊 搜索结果", 
            padding=self.config.padding
        )
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 结果信息栏
        info_frame = ttk.Frame(self.results_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.result_info_label = ttk.Label(
            info_frame,
            textvariable=self.result_info_var,
            font=('Arial', 9)
        )
        self.result_info_label.pack(side=tk.LEFT)
        
        # 分页控制
        page_frame = ttk.Frame(info_frame)
        page_frame.pack(side=tk.RIGHT)
        
        self.prev_btn = ttk.Button(
            page_frame,
            text="◀ 上一页",
            command=self.prev_page,
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.page_label = ttk.Label(page_frame, text="")
        self.page_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_btn = ttk.Button(
            page_frame,
            text="下一页 ▶",
            command=self.next_page,
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.LEFT)
        
        # 创建结果树
        self.results_tree = SearchResultsTree(self.results_frame, self.config)
        self.results_tree.on_item_selected = self.on_result_item_selected
    
    def create_status_section(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 状态标签
        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.search_status_var,
            foreground=self.config.primary_color
        )
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 导出按钮
        ttk.Button(
            status_frame,
            text="📤 导出结果",
            command=self.export_results
        ).pack(side=tk.RIGHT)
    
    def setup_bindings(self):
        """设置事件绑定"""
        # 回车键搜索
        for var in [self.search_pre_var, self.search_main_var, 
                   self.search_post_var, self.search_snr_var]:
            # 这里需要绑定到实际的Entry组件，暂时跳过
            pass
    
    def validate_int(self, value: str) -> bool:
        """验证整数输入"""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def on_search_type_changed(self):
        """搜索类型改变事件"""
        search_type = self.search_type_var.get()
        
        # 根据搜索类型调整UI状态
        if search_type == "exact":
            self.search_tolerance_var.set("0.0")
        else:
            self.search_tolerance_var.set(str(self.config.default_tolerance))
    
    def perform_search(self):
        """执行搜索"""
        try:
            # 构建搜索参数
            params = self.build_search_params()
            
            if params.is_empty():
                messagebox.showwarning("搜索提示", "请输入至少一个搜索条件")
                return
            
            # 更新状态
            self.search_status_var.set("搜索中...")
            self.search_btn.configure(state=tk.DISABLED)
            
            # 执行搜索
            if self.config.enable_async and len(self.data) > 1000:
                self.perform_search_async(params)
            else:
                self.search_results = self.search_manager.search_data(self.data, params)
                self.on_search_completed_internal(params)
            
        except Exception as e:
            self.logger.error(f"搜索过程中发生错误: {e}")
            messagebox.showerror("搜索错误", f"搜索过程中发生错误:\n{e}")
            self.search_status_var.set("搜索失败")
            self.search_btn.configure(state=tk.NORMAL)
    
    def perform_search_async(self, params: SearchParams):
        """异步执行搜索"""
        def search_worker():
            try:
                search_results = self.search_manager.search_data(self.data, params)
                
                # 在主线程中更新UI
                self.parent.after(0, lambda: self.on_search_completed_async(search_results, params))
                
            except Exception as e:
                self.logger.error(f"异步搜索错误: {e}")
                self.parent.after(0, lambda: self.on_search_error(e))
        
        # 启动搜索线程
        if self._search_thread and self._search_thread.is_alive():
            return  # 已有搜索任务在进行
        
        self._search_thread = threading.Thread(target=search_worker, daemon=True)
        self._search_thread.start()
    
    def on_search_completed_async(self, search_results: List[SearchMatch], params: SearchParams):
        """异步搜索完成回调"""
        self.search_results = search_results
        self.on_search_completed_internal(params)
    
    def on_search_error(self, error: Exception):
        """搜索错误处理"""
        messagebox.showerror("搜索错误", f"搜索过程中发生错误:\n{error}")
        self.search_status_var.set("搜索失败")
        self.search_btn.configure(state=tk.NORMAL)
    
    def on_search_completed_internal(self, params: SearchParams):
        """搜索完成内部处理"""
        # 更新结果显示
        self.results_tree.update_results(self.search_results)
        
        # 更新结果信息
        self.update_result_info()
        
        # 更新分页控制
        self.update_pagination_controls()
        
        # 添加到搜索历史
        if self.config.auto_save_history:
            self.add_to_history(params)
        
        # 更新状态
        result_count = len(self.search_results)
        if result_count > 0:
            avg_score = sum(m.score for m in self.search_results) / result_count
            self.search_status_var.set(f"找到 {result_count} 个结果，平均相似度 {avg_score:.3f}")
        else:
            self.search_status_var.set("未找到匹配结果")
        
        self.search_btn.configure(state=tk.NORMAL)
        
        # 通知搜索完成
        if self.on_search_completed:
            self.on_search_completed(self.search_results)
    
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
        
        # 搜索选项
        params.case_sensitive = self.case_sensitive_var.get()
        params.include_partial = self.include_partial_var.get()
        params.sort_by_score = self.sort_by_score_var.get()
        
        return params
    
    def clear_search(self):
        """清除搜索"""
        # 清除搜索输入
        for var in [self.search_pre_var, self.search_main_var, 
                   self.search_post_var, self.search_snr_var]:
            var.set("")
        
        # 重置搜索类型和容差
        self.search_type_var.set("exact")
        self.search_tolerance_var.set(str(self.config.default_tolerance))
        
        # 重置选项
        self.case_sensitive_var.set(False)
        self.include_partial_var.set(True)
        self.sort_by_score_var.set(True)
        
        # 清除搜索结果
        self.search_results = []
        self.results_tree.update_results([])
        
        # 更新状态
        self.search_status_var.set("就绪")
        self.result_info_var.set("")
        
        # 更新分页控制
        self.update_pagination_controls()
    
    def save_current_search(self):
        """保存当前搜索"""
        try:
            params = self.build_search_params()
            
            if params.is_empty():
                messagebox.showwarning("保存提示", "请先输入搜索条件")
                return
            
            # 添加到历史
            self.add_to_history(params)
            
            messagebox.showinfo("保存成功", "搜索条件已保存到历史记录")
            
        except Exception as e:
            self.logger.error(f"保存搜索失败: {e}")
            messagebox.showerror("保存失败", f"保存搜索条件失败:\n{e}")
    
    def add_to_history(self, params: SearchParams):
        """添加到搜索历史"""
        # 创建历史项
        result_count = len(self.search_results)
        avg_score = sum(m.score for m in self.search_results) / result_count if result_count > 0 else 0
        
        # 生成描述
        description_parts = []
        if params.exact_pre is not None:
            description_parts.append(f"PRE={params.exact_pre}")
        if params.exact_main is not None:
            description_parts.append(f"MAIN={params.exact_main}")
        if params.exact_post is not None:
            description_parts.append(f"POST={params.exact_post}")
        if params.target_snr is not None:
            description_parts.append(f"SNR={params.target_snr}")
        
        description = ", ".join(description_parts) if description_parts else "空搜索"
        description += f" ({params.search_type})"
        
        history_item = SearchHistoryItem(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            params=params,
            result_count=result_count,
            avg_score=avg_score,
            description=description
        )
        
        # 添加到历史列表（最新的在前面）
        self.search_history.insert(0, history_item)
        
        # 限制历史记录数量
        if len(self.search_history) > self.config.max_history_items:
            self.search_history = self.search_history[:self.config.max_history_items]
        
        # 更新历史显示
        self.update_history_display()
        
        # 保存到文件
        if self.config.auto_save_history:
            self.save_search_history()
    
    def update_history_display(self):
        """更新历史显示"""
        self.history_listbox.delete(0, tk.END)
        
        for item in self.search_history:
            display_text = f"{item.timestamp} - {item.description} ({item.result_count}个结果)"
            self.history_listbox.insert(tk.END, display_text)
    
    def apply_history_search(self):
        """应用历史搜索"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("选择提示", "请先选择一个历史记录")
            return
        
        # 获取选中的历史项
        index = selection[0]
        if 0 <= index < len(self.search_history):
            history_item = self.search_history[index]
            params = history_item.params
            
            # 应用搜索参数
            self.search_type_var.set(params.search_type)
            
            if params.exact_pre is not None:
                self.search_pre_var.set(str(params.exact_pre))
            else:
                self.search_pre_var.set("")
            
            if params.exact_main is not None:
                self.search_main_var.set(str(params.exact_main))
            else:
                self.search_main_var.set("")
            
            if params.exact_post is not None:
                self.search_post_var.set(str(params.exact_post))
            else:
                self.search_post_var.set("")
            
            if params.target_snr is not None:
                self.search_snr_var.set(str(params.target_snr))
            else:
                self.search_snr_var.set("")
            
            if params.snr_tolerance is not None:
                self.search_tolerance_var.set(str(params.snr_tolerance))
            
            # 应用搜索选项
            self.case_sensitive_var.set(getattr(params, 'case_sensitive', False))
            self.include_partial_var.set(getattr(params, 'include_partial', True))
            self.sort_by_score_var.set(getattr(params, 'sort_by_score', True))
            
            messagebox.showinfo("应用成功", "历史搜索条件已应用")
    
    def delete_history_item(self):
        """删除历史项"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("选择提示", "请先选择要删除的历史记录")
            return
        
        index = selection[0]
        if 0 <= index < len(self.search_history):
            # 确认删除
            if messagebox.askyesno("确认删除", "确定要删除选中的历史记录吗？"):
                del self.search_history[index]
                self.update_history_display()
                
                if self.config.auto_save_history:
                    self.save_search_history()
    
    def clear_history(self):
        """清空历史"""
        if not self.search_history:
            messagebox.showinfo("清空提示", "历史记录已经为空")
            return
        
        if messagebox.askyesno("确认清空", "确定要清空所有搜索历史吗？"):
            self.search_history.clear()
            self.update_history_display()
            
            if self.config.auto_save_history:
                self.save_search_history()
    
    def load_search_history(self):
        """加载搜索历史"""
        try:
            history_file = "search_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                self.search_history = []
                for item_data in history_data:
                    # 重建SearchParams对象
                    params_data = item_data['params']
                    params = SearchParams(
                        search_type=params_data.get('search_type', 'exact'),
                        exact_pre=params_data.get('exact_pre'),
                        exact_main=params_data.get('exact_main'),
                        exact_post=params_data.get('exact_post'),
                        target_snr=params_data.get('target_snr'),
                        snr_tolerance=params_data.get('snr_tolerance')
                    )
                    
                    # 设置额外属性
                    for attr in ['case_sensitive', 'include_partial', 'sort_by_score']:
                        if attr in params_data:
                            setattr(params, attr, params_data[attr])
                    
                    history_item = SearchHistoryItem(
                        timestamp=item_data['timestamp'],
                        params=params,
                        result_count=item_data['result_count'],
                        avg_score=item_data['avg_score'],
                        description=item_data['description']
                    )
                    
                    self.search_history.append(history_item)
                
                self.update_history_display()
                
        except Exception as e:
            self.logger.warning(f"加载搜索历史失败: {e}")
    
    def save_search_history(self):
        """保存搜索历史"""
        try:
            history_data = []
            for item in self.search_history:
                # 序列化SearchParams
                params_data = {
                    'search_type': item.params.search_type,
                    'exact_pre': item.params.exact_pre,
                    'exact_main': item.params.exact_main,
                    'exact_post': item.params.exact_post,
                    'target_snr': item.params.target_snr,
                    'snr_tolerance': item.params.snr_tolerance
                }
                
                # 添加额外属性
                for attr in ['case_sensitive', 'include_partial', 'sort_by_score']:
                    if hasattr(item.params, attr):
                        params_data[attr] = getattr(item.params, attr)
                
                item_data = {
                    'timestamp': item.timestamp,
                    'params': params_data,
                    'result_count': item.result_count,
                    'avg_score': item.avg_score,
                    'description': item.description
                }
                
                history_data.append(item_data)
            
            with open("search_history.json", 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存搜索历史失败: {e}")
    
    def update_result_info(self):
        """更新结果信息"""
        if not self.search_results:
            self.result_info_var.set("无搜索结果")
            return
        
        result_count = len(self.search_results)
        avg_score = sum(m.score for m in self.search_results) / result_count
        
        # 按匹配类型分组统计
        exact_count = sum(1 for m in self.search_results if m.match_type == "exact")
        fuzzy_count = result_count - exact_count
        
        info_text = f"共 {result_count} 个结果，平均相似度 {avg_score:.3f}"
        
        if exact_count > 0 and fuzzy_count > 0:
            info_text += f" (精确: {exact_count}, 模糊: {fuzzy_count})"
        elif exact_count > 0:
            info_text += f" (全部精确匹配)"
        elif fuzzy_count > 0:
            info_text += f" (全部模糊匹配)"
        
        self.result_info_var.set(info_text)
    
    def update_pagination_controls(self):
        """更新分页控制"""
        if not self.results_tree:
            return
        
        current_page, total_pages, total_results = self.results_tree.get_page_info()
        
        if total_pages <= 1:
            self.prev_btn.configure(state=tk.DISABLED)
            self.next_btn.configure(state=tk.DISABLED)
            self.page_label.configure(text="")
        else:
            self.prev_btn.configure(state=tk.NORMAL if current_page > 1 else tk.DISABLED)
            self.next_btn.configure(state=tk.NORMAL if current_page < total_pages else tk.DISABLED)
            self.page_label.configure(text=f"{current_page}/{total_pages}")
    
    def prev_page(self):
        """上一页"""
        if self.results_tree and self.results_tree.prev_page():
            self.update_pagination_controls()
    
    def next_page(self):
        """下一页"""
        if self.results_tree and self.results_tree.next_page():
            self.update_pagination_controls()
    
    def on_result_item_selected(self, match: SearchMatch):
        """结果项选中事件"""
        if self.on_result_selected:
            self.on_result_selected(match)
    
    def export_results(self):
        """导出搜索结果"""
        if not self.search_results:
            messagebox.showwarning("导出提示", "没有可导出的搜索结果")
            return
        
        try:
            from tkinter import filedialog
            import csv
            
            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                title="导出搜索结果",
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
            )
            
            if filename:
                # 导出数据
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # 写入表头
                    writer.writerow(['序号', 'PRE', 'MAIN', 'POST', 'SNR', '相似度', '匹配类型', '匹配字段'])
                    
                    # 写入数据
                    for i, match in enumerate(self.search_results, 1):
                        writer.writerow([
                            i,
                            match.point.pre,
                            match.point.main,
                            match.point.post,
                            match.point.snr,
                            match.score,
                            match.match_type,
                            ', '.join(match.matched_fields) if match.matched_fields else ''
                        ])
                
                messagebox.showinfo("导出成功", f"搜索结果已导出到:\n{filename}")
                
        except Exception as e:
            self.logger.error(f"导出错误: {e}")
            messagebox.showerror("导出错误", f"导出过程中发生错误:\n{e}")
    
    def set_data(self, data: List[SNRDataPoint]):
        """设置数据"""
        self.data = data.copy()
        self.search_results = []
        
        # 清除当前结果
        if self.results_tree:
            self.results_tree.update_results([])
        
        # 更新状态
        self.search_status_var.set(f"数据已加载 ({len(data)} 条记录)")
        self.result_info_var.set("")
    
    def get_search_results(self) -> List[SearchMatch]:
        """获取搜索结果"""
        return self.search_results.copy()
    
    def set_search_completed_callback(self, callback: Callable[[List[SearchMatch]], None]):
        """设置搜索完成回调"""
        self.on_search_completed = callback
    
    def set_result_selected_callback(self, callback: Callable[[SearchMatch], None]):
        """设置结果选中回调"""
        self.on_result_selected = callback
    
    def get_widget(self) -> ttk.Frame:
        """获取主组件"""
        return self.main_frame
    
    def destroy(self):
        """销毁组件"""
        # 保存搜索历史
        if self.config.auto_save_history:
            self.save_search_history()
        
        # 等待线程结束
        if self._search_thread and self._search_thread.is_alive():
            self._search_thread.join(timeout=1.0)
        
        # 销毁UI组件
        if self.main_frame:
            self.main_frame.destroy()


# 便捷函数
def create_search_panel(parent: tk.Widget, 
                       config: Optional[SearchPanelConfig] = None) -> SearchPanel:
    """
    创建搜索面板
    
    Args:
        parent: 父组件
        config: 配置对象
        
    Returns:
        SearchPanel实例
    """
    return SearchPanel(parent, config)


def create_search_window(title: str = "数据搜索", 
                        config: Optional[SearchPanelConfig] = None) -> Tuple[tk.Toplevel, SearchPanel]:
    """
    创建独立的搜索窗口
    
    Args:
        title: 窗口标题
        config: 配置对象
        
    Returns:
        (窗口对象, 搜索面板对象)
    """
    if config is None:
        config = SearchPanelConfig()
    
    # 创建窗口
    window = tk.Toplevel()
    window.title(title)
    window.geometry(f"{config.width}x{config.height}")
    window.resizable(True, True)
    
    # 创建搜索面板
    panel = SearchPanel(window, config)
    
    return window, panel