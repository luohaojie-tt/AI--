import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
from matplotlib import cm
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D
import csv
import platform
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import time

# 添加项目根目录和子目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filters'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui'))

from core.data_manager import DataManager
from ui.filter_panel import FilterPanel, create_filter_window
from ui.search_panel import SearchPanel, create_search_window

# 配置中文字体支持，避免字体警告
def configure_chinese_font():
    """配置中文字体支持"""
    try:
        # 全面禁用所有警告
        import warnings
        warnings.filterwarnings('ignore')
        
        # 设置环境变量禁用Python警告
        import os
        os.environ['PYTHONWARNINGS'] = 'ignore'
        
        import matplotlib.font_manager as fm
        
        # 根据操作系统选择合适的中文字体
        if platform.system() == 'Windows':
            # Windows系统常用中文字体
            fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi']
        elif platform.system() == 'Darwin':  # macOS
            fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti']
        else:  # Linux
            fonts = ['WenQuanYi Micro Hei', 'DejaVu Sans']
        
        # 尝试设置字体
        for font in fonts:
            try:
                plt.rcParams['font.sans-serif'] = [font]
                plt.rcParams['axes.unicode_minus'] = False
                break
            except:
                continue
        
    except Exception as e:
        print(f"字体配置警告: {e}")
        # 确保禁用所有警告
        import warnings
        warnings.filterwarnings('ignore')

# 初始化字体配置
configure_chinese_font()

class SNRVisualizerOptimized:
    def __init__(self, root):
        self.root = root
        # 配置tkinter中文字体
        self.configure_tkinter_font()
        self.root.title("🔬 SNR性能分析工具 - 优化版")
        self.root.geometry("1600x900")
        self.root.minsize(1000, 700)
        self.root.configure(bg='#f0f0f0')
        
        # 设置窗口图标和样式
        try:
            self.root.state('zoomed')  # Windows最大化
        except:
            pass
        
        self.file_path = None
        self.data = None
        self.df = None  # Pandas DataFrame for data analysis
        self.pre_values = []
        self.main_values = []
        self.post_values = []
        self.current_pre = None
        self.current_main = None
        self.current_post = None
        self.current_view = "heatmap"  # Current view mode: "heatmap" or "scatter3d"
        self.current_colorbar = None  # 用于跟踪当前的颜色条，避免重复叠加
        self.loading = False  # 加载状态标志
        
        # 添加缓存机制
        self.plot_cache = {}
        
        # 初始化数据管理器
        self.data_manager = DataManager()
        
        # 异步处理支持
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.task_queue = queue.Queue()
        self.is_processing = False
        self.cancel_current_task = False
        self.cache_enabled = True
        
        # 筛选和搜索面板
        self.filter_window = None
        self.search_window = None
        self.filter_panel = None
        self.search_panel = None
        self.filtered_data = None  # 筛选后的数据
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.create_widgets()
        
    def create_widgets(self):
        # 设置深色主题样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义样式
        style.configure('Title.TLabelframe.Label', font=('Arial', 12, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Action.TButton', font=('Arial', 9, 'bold'))
        style.configure('Success.TButton', font=('Arial', 9, 'bold'))
        style.configure('Warning.TButton', font=('Arial', 9, 'bold'))
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题框架
        title_frame = tk.Frame(main_frame, bg='#3498db', height=70)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🔬 SNR性能分析工具 - 优化版", 
                              font=('Arial', 20, 'bold'), fg='white', bg='#3498db')
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(title_frame, text="专业级信噪比可视化分析平台 | 数据驱动决策", 
                                 font=('Arial', 11), fg='#ecf0f1', bg='#3498db')
        subtitle_label.pack()
        
        # 创建顶部控制区域
        control_frame = ttk.LabelFrame(main_frame, text="📋 控制面板", padding="15", style='Title.TLabelframe')
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 文件选择区域 - 改进布局
        file_section = ttk.LabelFrame(control_frame, text="📁 数据文件管理", padding="10")
        file_section.pack(fill=tk.X, pady=(0, 15))
        
        file_frame = ttk.Frame(file_section)
        file_frame.pack(fill=tk.X)
        
        # 文件选择按钮 - 改进样式
        self.load_button = ttk.Button(file_frame, text="📂 选择SNR配置文件", command=self.load_file, style='Action.TButton')
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(file_frame, variable=self.progress_var, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 10))
        self.progress_bar.pack_forget()  # 初始隐藏
        
        # 文件路径显示
        self.file_label = ttk.Label(file_frame, text="未选择文件", font=('Arial', 9))
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 创建参数选择区域 - 改进布局
        param_section = ttk.LabelFrame(control_frame, text="⚙️ 参数配置选择", padding="10")
        param_section.pack(fill=tk.X, pady=(0, 15))
        
        # 创建参数选择和视图切换的框架
        param_view_frame = ttk.Frame(param_section)
        param_view_frame.pack(fill=tk.X)
        
        # 左侧参数选择
        param_select_frame = ttk.Frame(param_view_frame)
        param_select_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 参数选择网格布局
        param_grid_frame = ttk.Frame(param_select_frame)
        param_grid_frame.pack(fill=tk.X)
        
        # Pre参数选择 - 改进样式
        pre_frame = ttk.Frame(param_grid_frame)
        pre_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(pre_frame, text="Pre参数:", style='Header.TLabel').pack()
        self.pre_combobox = ttk.Combobox(pre_frame, state="readonly", width=18, font=('Arial', 9))
        self.pre_combobox.pack(pady=(5, 0))
        self.pre_combobox.bind("<<ComboboxSelected>>", self.update_plot)
        
        # Main参数选择
        main_frame_widget = ttk.Frame(param_grid_frame)
        main_frame_widget.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(main_frame_widget, text="Main参数:", style='Header.TLabel').pack()
        self.main_combobox = ttk.Combobox(main_frame_widget, state="readonly", width=18, font=('Arial', 9))
        self.main_combobox.pack(pady=(5, 0))
        self.main_combobox.bind("<<ComboboxSelected>>", self.update_plot)
        
        # Post参数选择
        post_frame = ttk.Frame(param_grid_frame)
        post_frame.pack(side=tk.LEFT)
        ttk.Label(post_frame, text="Post参数:", style='Header.TLabel').pack()
        self.post_combobox = ttk.Combobox(post_frame, state="readonly", width=18, font=('Arial', 9))
        self.post_combobox.pack(pady=(5, 0))
        self.post_combobox.bind("<<ComboboxSelected>>", self.update_plot)
        
        # 视图切换区域 - 改进布局
        view_section = ttk.LabelFrame(control_frame, text="🎯 视图模式与分析", padding="10")
        view_section.pack(fill=tk.X, pady=(0, 15))
        
        view_buttons_frame = ttk.Frame(view_section)
        view_buttons_frame.pack(fill=tk.X)
        
        # 视图切换按钮 - 改进样式
        view_frame = ttk.Frame(view_buttons_frame)
        view_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(view_frame, text="视图模式:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 15))
        self.view_var = tk.StringVar(value="heatmap")
        
        # 改进单选按钮样式
        self.heatmap_radio = ttk.Radiobutton(view_frame, text="🔥 热力图", variable=self.view_var, value="heatmap", command=self.change_view)
        self.heatmap_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        self.scatter3d_radio = ttk.Radiobutton(view_frame, text="🎯 3D散点图", variable=self.view_var, value="scatter3d", command=self.change_view)
        self.scatter3d_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        # 分析按钮 - 改进样式
        analysis_frame = ttk.Frame(view_buttons_frame)
        analysis_frame.pack(side=tk.RIGHT)
        ttk.Button(analysis_frame, text="🔍 数据筛选", command=self.open_filter_panel, style='Info.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(analysis_frame, text="🔎 数据搜索", command=self.open_search_panel, style='Info.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(analysis_frame, text="🏆 查找全局最优配置", command=self.find_global_best, style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(analysis_frame, text="📊 导出分析数据", command=self.export_data, style='Warning.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(analysis_frame, text="💾 导出筛选结果", command=self.export_filtered_data, style='Warning.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(analysis_frame, text="📤 导出搜索结果", command=self.export_search_results, style='Warning.TButton').pack(side=tk.LEFT)
        
        # 创建图表区域 - 改进样式
        plot_frame = ttk.LabelFrame(main_frame, text="📊 SNR性能可视化图表", padding="15", style='Title.TLabelframe')
        plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置matplotlib样式
        try:
            import matplotlib.pyplot as plt
            plt.style.use('seaborn-v0_8-whitegrid')
        except:
            try:
                plt.style.use('seaborn-whitegrid')
            except:
                pass
        
        self.fig = Figure(figsize=(14, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # 创建画布
        self.canvas_frame = ttk.Frame(plot_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(fill=tk.X, pady=(5, 0))
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        # 事件管理
        self.current_event_id = None
        
        # 创建状态栏 - 应用深色主题
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("🚀 系统就绪")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, 
                              font=('Arial', 9), foreground='#27ae60')
        status_bar.pack(fill=tk.X)
        
        # 创建信息显示区域
        info_frame = ttk.LabelFrame(main_frame, text="📋 数据分析报告", padding="15", style='Title.TLabelframe')
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 创建信息显示区域
        info_container = ttk.Frame(info_frame)
        info_container.pack(fill=tk.BOTH, expand=True)
        
        self.info_text = tk.Text(info_container, height=6, wrap=tk.WORD, 
                                font=('Consolas', 9), bg='white', fg='black')
        scrollbar = ttk.Scrollbar(info_container, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(state=tk.DISABLED)
        
        # 初始化信息文本 - 改进内容
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, "🚀 欢迎使用SNR性能分析工具 - 优化版！\n")
        self.info_text.insert(tk.END, "📁 请先选择并加载CSV数据文件开始分析。\n")
        self.info_text.insert(tk.END, "💡 支持的数据格式：pre, main, post, snr\n")
        self.info_text.insert(tk.END, "✨ 新增功能：进度提示、错误恢复、性能优化\n")
        self.info_text.config(state=tk.DISABLED)
        
        # 初始化图表
        self.init_empty_plot()
    
    def configure_tkinter_font(self):
        """配置tkinter中文字体支持"""
        try:
            # 重定向stderr来禁用tkinter字体警告
            import sys
            import io
            
            # 创建一个空的stderr来吞掉警告
            class NullWriter:
                def write(self, txt): pass
                def flush(self): pass
            
            # 临时重定向stderr
            original_stderr = sys.stderr
            sys.stderr = NullWriter()
            
            if platform.system() == 'Windows':
                # Windows系统设置默认字体
                fonts_to_try = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
                for font_name in fonts_to_try:
                    try:
                        default_font = (font_name, 9)
                        self.root.option_add('*Font', default_font)
                        # 设置ttk样式字体
                        style = ttk.Style()
                        style.configure('.', font=default_font)
                        print(f"成功设置字体: {font_name}")
                        break
                    except:
                        continue
            elif platform.system() == 'Darwin':  # macOS
                default_font = ('PingFang SC', 9)
                self.root.option_add('*Font', default_font)
            else:  # Linux
                default_font = ('DejaVu Sans', 9)
                self.root.option_add('*Font', default_font)
            
            # 恢复stderr
            sys.stderr = original_stderr
                
        except Exception as e:
            print(f"tkinter字体配置警告: {e}")
            # 确保恢复stderr
            try:
                sys.stderr = original_stderr
            except:
                pass
    
    def load_file(self):
        """加载数据文件 - 异步版本"""
        file_path = filedialog.askopenfilename(
            title="选择SNR配置文件",
            filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        # 如果正在处理其他任务，取消它
        if self.is_processing:
            self.cancel_current_task = True
            time.sleep(0.1)  # 给取消操作一点时间
        
        self.file_path = file_path
        self.file_label.config(text=file_path)
        
        # 显示加载状态
        self.loading = True
        self.is_processing = True
        self.cancel_current_task = False
        self.load_button.config(state='disabled')
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 10))
        self.progress_var.set(0)
        self.status_var.set("📂 正在加载文件...")
        self.root.update()
        
        # 异步执行数据加载
        future = self.executor.submit(self._load_file_async, file_path)
        
        # 启动结果检查
        self._check_load_result(future)
    
    def _load_file_async(self, file_path):
        """异步加载文件数据"""
        try:
            # 检查是否被取消
            if self.cancel_current_task:
                return {"status": "cancelled"}
            
            # 解析数据
            result = self._parse_data_async()
            
            if self.cancel_current_task:
                return {"status": "cancelled"}
            
            return {
                "status": "success",
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": e,
                "error_type": type(e).__name__
            }
    
    def _check_load_result(self, future):
        """检查异步加载结果"""
        if future.done():
            try:
                result = future.result()
                
                if result["status"] == "cancelled":
                    self._reset_loading_state()
                    return
                elif result["status"] == "success":
                    self._handle_load_success(result["data"])
                else:
                    self._handle_load_error(result["error"], result["error_type"])
                    
            except Exception as e:
                self._handle_load_error(e, type(e).__name__)
        else:
            # 继续检查
            self.root.after(100, lambda: self._check_load_result(future))
    
    def _handle_load_success(self, data):
        """处理加载成功"""
        try:
            self.update_comboboxes()
            # 自动切换到"全部配置"视图以展示所有数据
            self.view_var.set("all")
            self.current_view = "all"
            self.update_plot()
            # 同步数据到筛选和搜索面板
            self.sync_data_to_panels()
            self.status_var.set(f"✅ 已加载文件: {os.path.basename(self.file_path)} - 共{len(self.data)}个配置")
        except Exception as e:
            self._handle_load_error(e, type(e).__name__)
        finally:
            self._reset_loading_state()
    
    def _handle_load_error(self, error, error_type):
        """处理加载错误"""
        if error_type == "FileNotFoundError":
            error_msg = f"文件未找到: {self.file_path}"
            self._show_detailed_error("文件错误", error_msg, "请检查文件路径是否正确")
        elif error_type == "PermissionError":
            error_msg = "文件访问被拒绝，请检查文件权限"
            self._show_detailed_error("权限错误", error_msg, "请确保有读取文件的权限")
        elif error_type == "UnicodeDecodeError":
            error_msg = f"文件编码错误: {error}"
            suggestion = "请确保文件使用UTF-8、GBK或GB2312编码"
            self._show_detailed_error("编码错误", error_msg, suggestion)
        elif error_type == "ValueError":
            error_msg = f"数据格式错误: {error}"
            suggestion = "请确保文件格式正确:\n- CSV格式: pre,main,post,snr\n- 支持十六进制(0x前缀)和十进制\n- 数值范围: -32768 到 65535"
            self._show_detailed_error("数据格式错误", error_msg, suggestion)
        elif "EmptyDataError" in error_type:
            error_msg = "文件为空或没有有效数据"
            suggestion = "请检查文件是否包含有效的数据行"
            self._show_detailed_error("数据错误", error_msg, suggestion)
        else:
            error_msg = f"加载失败: {error}"
            self._show_detailed_error("未知错误", error_msg, "请检查文件格式或联系技术支持")
        
        self._reset_loading_state()
    
    def _reset_loading_state(self):
        """重置加载状态"""
        self.loading = False
        self.is_processing = False
        self.cancel_current_task = False
        self.load_button.config(state='normal')
        self.progress_bar.pack_forget()
        self.progress_var.set(0)
    
    def _parse_data_async(self):
        """异步解析数据 - 基于原parse_data方法"""
        # 这里复用原来的parse_data逻辑，但去掉UI更新部分
        try:
            # 尝试使用pandas直接读取CSV文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'ascii']
            df = None
            
            for encoding in encodings:
                if self.cancel_current_task:
                    return None
                    
                try:
                    # 尝试多种分隔符
                    for sep in [',', '\t', ';', ' ']:
                        try:
                            df = pd.read_csv(self.file_path, encoding=encoding, sep=sep, 
                                           names=['pre', 'main', 'post', 'snr'],
                                           comment='#', skip_blank_lines=True)
                            
                            # 检查是否成功读取到4列数据
                            if len(df.columns) == 4 and len(df) > 0:
                                break
                        except:
                            continue
                    
                    if df is not None and len(df.columns) == 4:
                        break
                except UnicodeDecodeError:
                    continue
            
            if df is None or len(df.columns) != 4:
                raise ValueError("无法解析文件格式，请检查文件是否为有效的CSV格式")
            
            # 检查是否有表头行
            if df.iloc[0].astype(str).str.contains('pre|main|post|snr', case=False).any():
                df = df.iloc[1:].reset_index(drop=True)
            
            # 数据清理和转换
            original_count = len(df)
            error_count = 0
            
            # 处理十六进制和十进制混合格式
            def parse_value(val):
                try:
                    if pd.isna(val):
                        return None
                    val_str = str(val).strip()
                    if '0x' in val_str.lower():
                        return int(val_str, 16)
                    else:
                        return int(float(val_str))
                except:
                    return None
            
            if self.cancel_current_task:
                return None
            
            # 转换数据类型
            df['pre'] = df['pre'].apply(parse_value)
            df['main'] = df['main'].apply(parse_value)
            df['post'] = df['post'].apply(parse_value)
            
            # 转换SNR为浮点数
            df['snr'] = pd.to_numeric(df['snr'], errors='coerce')
            
            # 删除无效数据
            df = df.dropna()
            
            # 数据验证
            valid_mask = (
                (df['pre'] >= -32768) & (df['pre'] <= 65535) &
                (df['main'] >= -32768) & (df['main'] <= 65535) &
                (df['post'] >= -32768) & (df['post'] <= 65535)
            )
            df = df[valid_mask]
            
            error_count = original_count - len(df)
            
            if len(df) == 0:
                raise ValueError("没有找到有效数据")
            
            # 转换为整数类型
            df['pre'] = df['pre'].astype(int)
            df['main'] = df['main'].astype(int)
            df['post'] = df['post'].astype(int)
            
            if self.cancel_current_task:
                return None
            
            # 在主线程中更新数据
            self.root.after(0, lambda: self._update_data_in_main_thread(df, error_count))
            
            return {"df": df, "error_count": error_count}
            
        except pd.errors.EmptyDataError:
            raise ValueError("文件为空或没有有效数据")
        except pd.errors.ParserError as e:
            raise ValueError(f"文件格式解析错误: {e}")
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, f"文件编码错误: {e.reason}")
        except Exception as e:
            # 如果pandas方法失败，回退到原始方法
            print(f"pandas解析失败，回退到传统方法: {e}")
            try:
                return self._parse_data_fallback_async()
            except Exception as fallback_error:
                raise ValueError(f"数据解析失败: {fallback_error}")
    
    def _update_data_in_main_thread(self, df, error_count):
        """在主线程中更新数据和UI"""
        # 存储数据
        self.df = df
        self.data = list(df.itertuples(index=False, name=None))
        self.pre_values = sorted(df['pre'].unique())
        self.main_values = sorted(df['main'].unique())
        self.post_values = sorted(df['post'].unique())
        
        # 将数据加载到data_manager中
        try:
            self.data_manager.load_data(self.file_path)
            print("DataManager数据加载成功")
        except Exception as e:
            print(f"DataManager数据加载失败: {e}")
        
        # 更新进度
        self.progress_var.set(100)
        
        # 更新信息显示
        info_text = f"""📊 数据加载完成 (异步优化版)
        
✅ 成功解析: {len(self.data)} 条数据
📈 Pre参数: {len(self.pre_values)}个值 ({self.format_hex(min(self.pre_values))} - {self.format_hex(max(self.pre_values))})
📈 Main参数: {len(self.main_values)}个值 ({self.format_hex(min(self.main_values))} - {self.format_hex(max(self.main_values))})
📈 Post参数: {len(self.post_values)}个值 ({self.format_hex(min(self.post_values))} - {self.format_hex(max(self.post_values))})
📊 SNR范围: {self.df['snr'].min():.3f} - {self.df['snr'].max():.3f}"""
        
        if error_count > 0:
            info_text += f"\n⚠️  跳过无效数据: {error_count}行"
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state=tk.DISABLED)
        
        print(f"成功解析 {len(self.data)} 条数据 (异步优化版)")
        print(f"Pre值范围: {len(self.pre_values)}个 ({self.format_hex(min(self.pre_values))} - {self.format_hex(max(self.pre_values))})")
        print(f"Main值范围: {len(self.main_values)}个 ({self.format_hex(min(self.main_values))} - {self.format_hex(max(self.main_values))})")
        print(f"Post值范围: {len(self.post_values)}个 ({self.format_hex(min(self.post_values))} - {self.format_hex(max(self.post_values))})")
    
    def _parse_data_fallback_async(self):
        """异步回退解析方法"""
        # 这里可以实现回退的异步解析逻辑
        # 为简化，暂时抛出异常
        raise ValueError("回退解析方法暂未实现异步版本")
    
    def _show_detailed_error(self, title: str, message: str, suggestion: str = ""):
        """显示详细的错误信息"""
        full_message = message
        if suggestion:
            full_message += f"\n\n建议解决方案:\n{suggestion}"
        
        messagebox.showerror(title, full_message)
        self.status_var.set(f"❌ {title}: {message.split(':')[0]}")
        
        # 在信息文本框中也显示错误
        if hasattr(self, 'info_text'):
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"❌ {title}\n\n{message}\n\n{suggestion if suggestion else ''}")
            self.info_text.config(state=tk.DISABLED)
    
    def parse_data(self):
        """解析数据文件 - 优化版本使用pandas"""
        try:
            # 尝试使用pandas直接读取CSV文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'ascii']
            df = None
            
            for encoding in encodings:
                try:
                    # 尝试多种分隔符
                    for sep in [',', '\t', ';', ' ']:
                        try:
                            df = pd.read_csv(self.file_path, encoding=encoding, sep=sep, 
                                           names=['pre', 'main', 'post', 'snr'],
                                           comment='#', skip_blank_lines=True)
                            
                            # 检查是否成功读取到4列数据
                            if len(df.columns) == 4 and len(df) > 0:
                                break
                        except:
                            continue
                    
                    if df is not None and len(df.columns) == 4:
                        break
                except UnicodeDecodeError:
                    continue
            
            if df is None or len(df.columns) != 4:
                raise ValueError("无法解析文件格式，请检查文件是否为有效的CSV格式")
            
            # 检查是否有表头行
            if df.iloc[0].astype(str).str.contains('pre|main|post|snr', case=False).any():
                df = df.iloc[1:].reset_index(drop=True)
            
            # 数据清理和转换
            original_count = len(df)
            error_count = 0
            
            # 处理十六进制和十进制混合格式
            def parse_value(val):
                try:
                    if pd.isna(val):
                        return None
                    val_str = str(val).strip()
                    if '0x' in val_str.lower():
                        return int(val_str, 16)
                    else:
                        return int(float(val_str))
                except:
                    return None
            
            # 转换数据类型
            df['pre'] = df['pre'].apply(parse_value)
            df['main'] = df['main'].apply(parse_value)
            df['post'] = df['post'].apply(parse_value)
            
            # 转换SNR为浮点数
            df['snr'] = pd.to_numeric(df['snr'], errors='coerce')
            
            # 删除无效数据
            df = df.dropna()
            
            # 数据验证
            valid_mask = (
                (df['pre'] >= -32768) & (df['pre'] <= 65535) &
                (df['main'] >= -32768) & (df['main'] <= 65535) &
                (df['post'] >= -32768) & (df['post'] <= 65535)
            )
            df = df[valid_mask]
            
            error_count = original_count - len(df)
            
            if len(df) == 0:
                raise ValueError("没有找到有效数据")
            
            # 转换为整数类型
            df['pre'] = df['pre'].astype(int)
            df['main'] = df['main'].astype(int)
            df['post'] = df['post'].astype(int)
            
            # 更新进度
            self.progress_var.set(50)
            self.root.update()
            
            # 存储数据
            self.df = df
            self.data = list(df.itertuples(index=False, name=None))
            self.pre_values = sorted(df['pre'].unique())
            self.main_values = sorted(df['main'].unique())
            self.post_values = sorted(df['post'].unique())
            
            # 更新进度
            self.progress_var.set(100)
            self.root.update()
            
            # 更新信息显示
            info_text = f"""📊 数据加载完成 (优化版)
            
✅ 成功解析: {len(self.data)} 条数据
📈 Pre参数: {len(self.pre_values)}个值 ({self.format_hex(min(self.pre_values))} - {self.format_hex(max(self.pre_values))})
📈 Main参数: {len(self.main_values)}个值 ({self.format_hex(min(self.main_values))} - {self.format_hex(max(self.main_values))})
📈 Post参数: {len(self.post_values)}个值 ({self.format_hex(min(self.post_values))} - {self.format_hex(max(self.post_values))})
📊 SNR范围: {self.df['snr'].min():.3f} - {self.df['snr'].max():.3f}"""
            
            if error_count > 0:
                info_text += f"\n⚠️  跳过无效数据: {error_count}行"
            
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, info_text)
            self.info_text.config(state=tk.DISABLED)
            
            print(f"成功解析 {len(self.data)} 条数据 (pandas优化版)")
            print(f"Pre值范围: {len(self.pre_values)}个 ({self.format_hex(min(self.pre_values))} - {self.format_hex(max(self.pre_values))})")
            print(f"Main值范围: {len(self.main_values)}个 ({self.format_hex(min(self.main_values))} - {self.format_hex(max(self.main_values))})")
            print(f"Post值范围: {len(self.post_values)}个 ({self.format_hex(min(self.post_values))} - {self.format_hex(max(self.post_values))})") 
            
        except pd.errors.EmptyDataError:
            raise ValueError("文件为空或没有有效数据")
        except pd.errors.ParserError as e:
            raise ValueError(f"文件格式解析错误: {e}")
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, f"文件编码错误: {e.reason}")
        except Exception as e:
            # 如果pandas方法失败，回退到原始方法
            print(f"pandas解析失败，回退到传统方法: {e}")
            try:
                self.parse_data_fallback()
            except Exception as fallback_error:
                raise ValueError(f"数据解析失败: {fallback_error}")
    
    def parse_data_fallback(self):
        """回退的数据解析方法 - 原始逐行解析"""
        # 支持多种编码格式
        encodings = ['utf-8', 'gbk', 'gb2312', 'ascii']
        lines = None
        
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        
        if lines is None:
            raise UnicodeDecodeError('unknown', b'', 0, 0, "无法使用任何支持的编码(UTF-8, GBK, GB2312, ASCII)读取文件")
        
        data = []
        pre_set = set()
        main_set = set()
        post_set = set()
        error_lines = []
        
        # 跳过第一行如果是CSV表头
        start_line = 0
        if lines and ('pre' in lines[0].lower() and 'main' in lines[0].lower() and 'post' in lines[0].lower() and 'snr' in lines[0].lower()):
            start_line = 1
        
        total_lines = len(lines) - start_line
        processed_lines = 0
        
        for i, line in enumerate(lines[start_line:], start_line):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 支持多种分隔符
            separators = [',', '\t', ' ', ';']
            parts = None
            for sep in separators:
                test_parts = line.split(sep)
                if len(test_parts) == 4:
                    parts = test_parts
                    break
            
            if parts is None or len(parts) != 4:
                error_lines.append(i+1)
                continue
            
            try:
                # 解析十六进制或十进制值
                pre_val = int(parts[0], 0) if '0x' in parts[0].lower() else int(parts[0])
                main_val = int(parts[1], 0) if '0x' in parts[1].lower() else int(parts[1])
                post_val = int(parts[2], 0) if '0x' in parts[2].lower() else int(parts[2])
                snr_val = float(parts[3])
                
                # 数据验证
                if not (-32768 <= pre_val <= 65535 and -32768 <= main_val <= 65535 and -32768 <= post_val <= 65535):
                    error_lines.append(i+1)
                    continue
                
                data.append((pre_val, main_val, post_val, snr_val))
                pre_set.add(pre_val)
                main_set.add(main_val)
                post_set.add(post_val)
                
            except ValueError as e:
                print(f"警告: 第{i+1}行数据解析失败: {line} - {e}")
                error_lines.append(i+1)
                continue
            
            # 更新进度
            processed_lines += 1
            if processed_lines % 100 == 0:  # 每100行更新一次进度
                progress = (processed_lines / total_lines) * 100
                self.progress_var.set(progress)
                self.root.update()
        
        self.data = data
        self.pre_values = sorted(list(pre_set))
        self.main_values = sorted(list(main_set))
        self.post_values = sorted(list(post_set))
        
        # 创建DataFrame用于数据分析
        self.df = pd.DataFrame(data, columns=['pre', 'main', 'post', 'snr'])
        
        if not self.data:
            if error_lines:
                raise ValueError(f"文件中没有有效数据。共{len(error_lines)}行数据格式错误，请检查数据格式")
            else:
                raise ValueError("文件中没有找到任何数据行")
        
        # 更新信息显示
        info_text = f"""📊 数据加载完成 (回退方法)
        
✅ 成功解析: {len(self.data)} 条数据
📈 Pre参数: {len(self.pre_values)}个值 ({self.format_hex(min(self.pre_values))} - {self.format_hex(max(self.pre_values))})
📈 Main参数: {len(self.main_values)}个值 ({self.format_hex(min(self.main_values))} - {self.format_hex(max(self.main_values))})
📈 Post参数: {len(self.post_values)}个值 ({self.format_hex(min(self.post_values))} - {self.format_hex(max(self.post_values))})
📊 SNR范围: {self.df['snr'].min():.3f} - {self.df['snr'].max():.3f}"""
        
        if error_lines:
            info_text += f"\n⚠️  跳过错误行: {len(error_lines)}行 (行号: {', '.join(map(str, error_lines[:10]))}{'...' if len(error_lines) > 10 else ''})"
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state=tk.DISABLED)
        
        print(f"成功解析 {len(self.data)} 条数据 (回退方法)")
        print(f"Pre值范围: {len(self.pre_values)}个 ({self.format_hex(min(self.pre_values))} - {self.format_hex(max(self.pre_values))})")
        print(f"Main值范围: {len(self.main_values)}个 ({self.format_hex(min(self.main_values))} - {self.format_hex(max(self.main_values))})")
        print(f"Post值范围: {len(self.post_values)}个 ({self.format_hex(min(self.post_values))} - {self.format_hex(max(self.post_values))})")
    

    
    def format_hex(self, val):
         """格式化十六进制显示"""
         # 确保val是整数类型
         val = int(val)
         if val < 0:
             return f"0x{val & 0xFFFF:04x}"
         else:
             return f"0x{val:04x}"
    
    def find_global_best(self):
         if not self.data:
             messagebox.showinfo("信息", "请先加载数据文件")
             return
         
         # 找出全局最优配置
         best_config = max(self.data, key=lambda x: x[3])
         pre, main, post, snr = best_config
         
         # 显示全局最优配置信息
         self.info_text.config(state=tk.NORMAL)
         self.info_text.delete(1.0, tk.END)
         
         info = f"全局最优配置:\n"
         info += f"Pre = {self.format_hex(pre)}\n"
         info += f"Main = {self.format_hex(main)}\n"
         info += f"Post = {self.format_hex(post)}\n"
         info += f"SNR = {snr:.4f} dB"
         
         self.info_text.insert(tk.END, info)
         self.info_text.config(state=tk.DISABLED)
         
         # 更新下拉框选择
         pre_idx = self.pre_values.index(pre) if pre in self.pre_values else 0
         main_idx = self.main_values.index(main) if main in self.main_values else 0
         post_idx = self.post_values.index(post) if post in self.post_values else 0
         
         self.pre_combobox.current(pre_idx)
         self.main_combobox.current(main_idx)
         self.post_combobox.current(post_idx)
         self.current_pre = pre
         self.current_main = main
         self.current_post = post
         
         # 切换到折线图视图并更新图表
         self.view_var.set("line")
         self.current_view = "line"
         self.update_plot()
         
         self.status_var.set(f"已找到全局最优配置: Pre={self.format_hex(pre)}, Main={self.format_hex(main)}, Post={self.format_hex(post)}, SNR={snr:.4f} dB")
    
    def export_data(self):
         if not self.data:
             messagebox.showinfo("信息", "请先加载数据文件")
             return
         
         # 创建分析结果
         analysis_results = []
         
         # 对于每个pre和post组合，找出最大的SNR值
         for pre in self.pre_values:
             for post in self.post_values:
                 # 筛选当前pre和post组合的数据
                 filtered = [(main, snr) for p, main, po, snr in self.data if p == pre and po == post]
                 if filtered:
                     # 找出最大SNR值及其对应的main值
                     best = max(filtered, key=lambda x: x[1])
                     max_main, max_snr = best
                     
                     analysis_results.append({
                         'pre': pre,
                         'pre_hex': self.format_hex(pre),
                         'post': post,
                         'post_hex': self.format_hex(post),
                         'best_main': max_main,
                         'best_main_hex': self.format_hex(max_main),
                         'max_snr': max_snr
                     })
         
         # 按SNR值排序
         analysis_results.sort(key=lambda x: x['max_snr'], reverse=True)
         
         # 选择保存文件路径
         file_path = filedialog.asksaveasfilename(
             title="保存分析结果",
             defaultextension=".csv",
             filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
         )
         
         if not file_path:
             return
         
         # 保存为CSV文件
         try:
             import csv
             with open(file_path, 'w', newline='') as csvfile:
                 fieldnames = ['pre_hex', 'best_main_hex', 'post_hex', 'max_snr']
                 writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                 
                 writer.writeheader()
                 for result in analysis_results:
                     writer.writerow({
                         'pre_hex': result['pre_hex'],
                         'best_main_hex': result['best_main_hex'],
                         'post_hex': result['post_hex'],
                         'max_snr': result['max_snr']
                     })
             
             messagebox.showinfo("成功", f"分析结果已保存到: {file_path}")
         except Exception as e:
             messagebox.showerror("错误", f"保存文件失败: {str(e)}")
    
    def update_comboboxes(self):
        """更新下拉框选项 - 改进显示格式"""
        # 格式化显示选项
        pre_options = [f"{self.format_hex(val)} ({val})" for val in self.pre_values]
        main_options = [f"{self.format_hex(val)} ({val})" for val in self.main_values]
        post_options = [f"{self.format_hex(val)} ({val})" for val in self.post_values]
        
        self.pre_combobox['values'] = pre_options
        self.main_combobox['values'] = main_options
        self.post_combobox['values'] = post_options
        
        # 设置默认选择
        if pre_options:
            self.pre_combobox.current(0)
            self.current_pre = self.pre_values[0]
        if main_options:
            self.main_combobox.current(0)
            self.current_main = self.main_values[0]
        if post_options:
            self.post_combobox.current(0)
            self.current_post = self.post_values[0]
    
    def change_view(self):
        """切换视图模式"""
        self.current_view = self.view_var.get()
        self.update_plot()
    
    def update_plot(self, event=None):
        """更新图表 - 异步版本避免UI冻结"""
        if not self.data:
            return
        
        # 如果正在处理，取消当前任务
        if self.is_processing:
            self.cancel_current_task = True
            return
        
        # 检查缓存
        cache_key = self._get_cache_key()
        if self.cache_enabled and cache_key in self.plot_cache:
            cached_data = self.plot_cache[cache_key]
            self.restore_plot_from_cache(cached_data)
            return
        
        # 异步绘制图表
        self.is_processing = True
        self.cancel_current_task = False
        self.status_var.set("🔄 正在绘制图表...")
        
        # 提交异步任务
        future = self.executor.submit(self._update_plot_async)
        self.root.after(100, lambda: self._check_plot_result(future))
    
    def _get_cache_key(self):
        """生成缓存键"""
        # 获取当前选择的参数值
        current_pre = self.current_pre
        current_main = self.current_main
        current_post = self.current_post
        
        # 更新当前参数值
        if self.pre_combobox.get() != "":
            pre_index = self.pre_combobox.current()
            if 0 <= pre_index < len(self.pre_values):
                current_pre = self.pre_values[pre_index]
        
        if self.main_combobox.get() != "":
            main_index = self.main_combobox.current()
            if 0 <= main_index < len(self.main_values):
                current_main = self.main_values[main_index]
        
        if self.post_combobox.get() != "":
            post_index = self.post_combobox.current()
            if 0 <= post_index < len(self.post_values):
                current_post = self.post_values[post_index]
        
        return f"{self.current_view}_{current_pre}_{current_main}_{current_post}"
    
    def _update_plot_async(self):
        """异步绘制图表"""
        try:
            # 获取当前选择的参数值
            if self.pre_combobox.get() != "":
                pre_index = self.pre_combobox.current()
                if 0 <= pre_index < len(self.pre_values):
                    self.current_pre = self.pre_values[pre_index]
            
            if self.main_combobox.get() != "":
                main_index = self.main_combobox.current()
                if 0 <= main_index < len(self.main_values):
                    self.current_main = self.main_values[main_index]
            
            if self.post_combobox.get() != "":
                post_index = self.post_combobox.current()
                if 0 <= post_index < len(self.post_values):
                    self.current_post = self.post_values[post_index]
            
            if self.cancel_current_task:
                return None
            
            # 获取绘图数据（这部分在后台线程中执行）
            plot_data = None
            if self.current_view == "heatmap":
                plot_data = self._get_heatmap_data_async()
            elif self.current_view == "scatter3d":
                plot_data = self._get_scatter3d_data_async()
            
            if self.cancel_current_task:
                return None
            
            return {
                'plot_data': plot_data,
                'cache_key': self._get_cache_key(),
                'view_type': self.current_view
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _check_plot_result(self, future):
        """检查异步绘图结果"""
        if future.done():
            try:
                result = future.result()
                if result is None:
                    # 任务被取消
                    self.is_processing = False
                    self.status_var.set("⏹️ 绘图已取消")
                    return
                
                if 'error' in result:
                    self._handle_plot_error(result['error'])
                else:
                    self._handle_plot_success(result)
                    
            except Exception as e:
                self._handle_plot_error(str(e))
        else:
            # 继续检查
            self.root.after(100, lambda: self._check_plot_result(future))
    
    def _handle_plot_success(self, result):
        """处理绘图成功"""
        try:
            # 在主线程中更新UI
            # 对于3D散点图，需要重新创建3D子图
            if result['view_type'] == "scatter3d":
                self.fig.clear()
                self.ax = self.fig.add_subplot(111, projection='3d')
            else:
                self.ax.clear()
            
            # 移除之前的颜色条
            if self.current_colorbar:
                try:
                    self.current_colorbar.remove()
                except:
                    pass
                self.current_colorbar = None
            
            # 根据视图类型绘制图表
            plot_data = result['plot_data']
            if result['view_type'] == "heatmap":
                self._draw_heatmap(plot_data)
            elif result['view_type'] == "scatter3d":
                self._draw_scatter3d(plot_data)
            
            # 缓存绘图数据
            if self.cache_enabled and plot_data is not None:
                cache_key = result['cache_key']
                self.plot_cache[cache_key] = plot_data
                # 限制缓存大小
                if len(self.plot_cache) > 50:
                    oldest_key = next(iter(self.plot_cache))
                    del self.plot_cache[oldest_key]
            
            self.canvas.draw()
            self.status_var.set("✅ 图表绘制完成")
            
        except Exception as e:
            self._handle_plot_error(str(e))
        finally:
            self.is_processing = False
            self.cancel_current_task = False
    
    def _handle_plot_error(self, error):
        """处理绘图错误"""
        print(f"绘图错误: {error}")
        import traceback
        traceback.print_exc()
        self.status_var.set(f"❌ 绘图失败: {error}")
        self.is_processing = False
        self.cancel_current_task = False
    

    def _get_heatmap_data_async(self):
        """异步获取热力图数据"""
        # 构建参数字典
        params = {
            'fixed_param': 'main',  # 固定main参数
            'fixed_value': self.current_main
        }
        # 复用data_manager的get_heatmap_data方法
        return self.data_manager.get_heatmap_data(params)
    
    def _get_all_configurations_data_async(self):
        """异步获取所有配置数据"""
        if not self.data or len(self.data) == 0:
            return None
        
        # 准备所有配置数据
        all_config_data = {
            'total_points': len(self.data),
            'pre_values': self.pre_values,
            'main_values': self.main_values,
            'post_values': self.post_values
        }
        
        return all_config_data
    
    def _get_scatter3d_data_async(self):
        """异步获取3D散点图数据"""
        if not self.data or len(self.data) == 0:
            return None
        
        # 获取所有数据点的三个参数和SNR值
        scatter_data = []
        for row in self.data:
            try:
                # row是元组 (pre, main, post, snr)，数据已经是数值类型
                pre_val = float(row[0])
                main_val = float(row[1])
                post_val = float(row[2])
                snr_val = float(row[3])
                
                scatter_data.append({
                    'pre': pre_val,
                    'main': main_val,
                    'post': post_val,
                    'snr': snr_val,
                    'pre_hex': self.format_hex(int(pre_val)),
                    'main_hex': self.format_hex(int(main_val)),
                    'post_hex': self.format_hex(int(post_val))
                })
            except (ValueError, IndexError) as e:
                print(f"处理数据点时出错: {e}, 数据: {row}")
                continue
        
        return scatter_data
    
    
    def _draw_heatmap(self, plot_data):
        """绘制热力图"""
        if 'error' in plot_data:
            self.ax.text(0.5, 0.5, f"❌ {plot_data['error']}", 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, color='red')
            return
        
        # 绘制热力图
        matrix = plot_data.get('matrix')
        x_labels = plot_data.get('x_labels', [])
        y_labels = plot_data.get('y_labels', [])
        
        if matrix is not None and len(x_labels) > 0 and len(y_labels) > 0:
            import numpy as np
            
            # 创建热力图
            im = self.ax.imshow(matrix, cmap='viridis', aspect='auto', origin='lower')
            
            # 设置标签
            self.ax.set_xticks(range(len(x_labels)))
            self.ax.set_yticks(range(len(y_labels)))
            self.ax.set_xticklabels([self.format_hex(x) for x in x_labels])
            self.ax.set_yticklabels([self.format_hex(y) for y in y_labels])
            
            # 设置标题和标签
            self.ax.set_xlabel(plot_data.get('x_label', 'X轴'))
            self.ax.set_ylabel(plot_data.get('y_label', 'Y轴'))
            title = plot_data.get('title', '热力图')
            # 如果有筛选数据，在标题中标识
            if self.filtered_data and len(self.filtered_data) > 0:
                title += f" - 筛选结果: {len(self.filtered_data)}个"
            self.ax.set_title(title)
            
            # 添加颜色条
            if self.current_colorbar:
                self.current_colorbar.remove()
            self.current_colorbar = self.fig.colorbar(im, ax=self.ax, label='SNR (dB)')
        else:
            self.ax.text(0.5, 0.5, '📊 没有数据可显示', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, color='gray')
    
    
    def _draw_scatter3d(self, plot_data):
        """绘制3D散点图"""
        if not plot_data or len(plot_data) == 0:
            self.ax.text(0.5, 0.5, '❌ 没有可用的数据绘制3D散点图', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, color='red')
            return
        
        # 清除当前图表并创建3D子图
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # 提取数据
        pre_values = [point['pre'] for point in plot_data]
        main_values = [point['main'] for point in plot_data]
        post_values = [point['post'] for point in plot_data]
        snr_values = [point['snr'] for point in plot_data]
        
        # 检查是否有筛选数据需要高亮显示
        highlight_indices = []
        if self.filtered_data and len(self.filtered_data) > 0:
            # 创建筛选数据的集合以便快速查找
            filtered_set = set((point.pre, point.main, point.post, point.snr) for point in self.filtered_data)
            
            # 找到需要高亮的数据点索引
            for i, point in enumerate(plot_data):
                point_tuple = (point['pre'], point['main'], point['post'], point['snr'])
                if point_tuple in filtered_set:
                    highlight_indices.append(i)
        
        # 创建颜色映射
        norm = Normalize(vmin=min(snr_values), vmax=max(snr_values))
        colors = cm.viridis(norm(snr_values))
        
        # 绘制3D散点图，启用专业的拾取功能
        scatter = self.ax.scatter(pre_values, main_values, post_values, 
                                c=snr_values, cmap='viridis', s=60, alpha=0.7, picker=True)
        
        # 如果有筛选数据需要高亮显示，则绘制高亮点
        if highlight_indices:
            highlight_pre = [pre_values[i] for i in highlight_indices]
            highlight_main = [main_values[i] for i in highlight_indices]
            highlight_post = [post_values[i] for i in highlight_indices]
            highlight_snr = [snr_values[i] for i in highlight_indices]
            
            # 绘制高亮点（更大的点，不同的颜色）
            self.ax.scatter(highlight_pre, highlight_main, highlight_post, 
                          c='red', s=100, alpha=1.0, edgecolors='black', linewidth=2,
                          label=f'筛选结果 ({len(highlight_indices)}个)')
        
        # 设置轴标签
        self.ax.set_xlabel('PRE 参数', fontsize=12, labelpad=10)
        self.ax.set_ylabel('MAIN 参数', fontsize=12, labelpad=10)
        self.ax.set_zlabel('POST 参数', fontsize=12, labelpad=10)
        
        # 设置标题
        title = '🎯 三参数与SNR关系的3D散点图'
        if highlight_indices:
            title += f' - 筛选结果高亮显示'
        self.ax.set_title(title, fontsize=14, pad=20)
        
        # 添加图例（如果有高亮点）
        if highlight_indices:
            self.ax.legend()
        
        # 添加颜色条
        if self.current_colorbar:
            self.current_colorbar.remove()
        self.current_colorbar = self.fig.colorbar(scatter, ax=self.ax, shrink=0.8, aspect=20)
        self.current_colorbar.set_label('SNR (dB)', fontsize=12)
        
        # 添加网格
        self.ax.grid(True, alpha=0.3)
        
        # 设置视角
        self.ax.view_init(elev=20, azim=45)
        
        # 添加统计信息
        stats_text = f'数据点数: {len(plot_data)}\n'
        stats_text += f'SNR范围: {min(snr_values):.2f} ~ {max(snr_values):.2f} dB\n'
        stats_text += f'最优SNR: {max(snr_values):.2f} dB'
        if highlight_indices:
            stats_text += f'\n筛选结果: {len(highlight_indices)}个'
        
        # 在图表上添加统计信息
        self.ax.text2D(0.02, 0.98, stats_text, transform=self.ax.transAxes, 
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 生成缓存数据
        cache_data = {
            'type': 'scatter3d',
            'data': {
                'pre_values': pre_values,
                'main_values': main_values,
                'post_values': post_values,
                'snr_values': snr_values,
                'xlabel': 'PRE 参数',
                'ylabel': 'MAIN 参数',
                'zlabel': 'POST 参数',
                'title': title,
                'elev': 20,
                'azim': 45,
                'stats_text': stats_text,
                'plot_data': plot_data,
                'highlight_indices': highlight_indices
            },
            'cache_key': self._get_cache_key()
        }
        
        # 存储到缓存
        self.plot_cache[cache_data['cache_key']] = cache_data
        
        # 添加交互功能
        self._add_3d_interaction(plot_data)
        
        # 刷新画布
        self.canvas.draw()
    
    def _add_3d_interaction(self, plot_data):
        """为3D散点图添加专业的交互功能"""
        # 存储数据点信息用于交互
        self.scatter_data = plot_data
        
        # 创建一个文本框用于显示数据点信息
        if hasattr(self, 'hover_text'):
            self.hover_text.remove()
        self.hover_text = None
        
        # 使用专业的pick_event进行精确的数据点检测
        def on_pick(event):
            """处理数据点拾取事件"""
            if hasattr(event, 'ind') and len(event.ind) > 0:
                # 获取被点击的数据点索引
                point_index = event.ind[0]  # 取第一个点的索引
                
                if point_index < len(self.scatter_data):
                    point = self.scatter_data[point_index]
                    
                    # 显示数据点详细信息
                    info_text = f"PRE: {point['pre_hex']} ({point['pre']})"
                    info_text += f" | MAIN: {point['main_hex']} ({point['main']})"
                    info_text += f" | POST: {point['post_hex']} ({point['post']})"
                    info_text += f" | SNR: {point['snr']:.2f} dB"
                    
                    # 更新状态栏
                    self.status_var.set(info_text)
                    
                    # 在图上显示选中信息
                    if self.hover_text:
                        self.hover_text.remove()
                    
                    # 创建显示文本
                    display_text = f"PRE: {point['pre_hex']}\nMAIN: {point['main_hex']}\nPOST: {point['post_hex']}\nSNR: {point['snr']:.2f} dB"
                    
                    # 使用2D文本标注显示选中的数据点信息
                    self.hover_text = self.ax.text2D(0.02, 0.02, display_text,
                                                     transform=self.ax.transAxes,
                                                     fontsize=11, 
                                                     bbox=dict(boxstyle='round,pad=0.6', 
                                                             facecolor='lightgreen', 
                                                             alpha=0.95,
                                                             edgecolor='darkgreen',
                                                             linewidth=2),
                                                     verticalalignment='bottom',
                                                     horizontalalignment='left',
                                                     zorder=1000)
                    
                    print(f"精确选中数据点 {point_index}: PRE={point['pre']}, MAIN={point['main']}, POST={point['post']}, SNR={point['snr']:.2f}")
                    self.canvas.draw_idle()
        
        # 绑定专业的拾取事件
        self.canvas.mpl_connect('pick_event', on_pick)
        
        # 添加鼠标移动事件来清除选择（可选）
        def on_mouse_move(event):
            # 当鼠标移动到非数据点区域时，可以选择清除显示
            pass
        
        # 可选：绑定鼠标移动事件
        # self.canvas.mpl_connect('motion_notify_event', on_mouse_move)
        
        # 添加点击事件处理
        def on_click(event):
            if event.inaxes == self.ax and event.dblclick:
                # 双击重置视角，但不清空图形
                print(f"双击重置视角前，散点图数据: {len(self.scatter_data) if hasattr(self, 'scatter_data') and self.scatter_data else 0} 个点")
                self.ax.view_init(elev=20, azim=45)
                # 确保散点图数据仍然存在
                if hasattr(self, 'scatter_data') and self.scatter_data:
                    print(f"重置视角后，散点图数据仍然存在: {len(self.scatter_data)} 个点")
                    # 重新绘制散点图以确保数据不丢失
                    self._redraw_scatter_plot()
                self.canvas.draw_idle()
        
        # 绑定点击事件
        self.canvas.mpl_connect('button_press_event', on_click)
    
    # 旧的距离检测方法已被专业的pick_event替代
    
    # 旧的屏幕坐标检测方法已被专业的pick_event替代
    
    # 旧的简化检测方法已被专业的pick_event替代
    
    def on_heatmap_click(self, event):
        """处理热力图鼠标点击事件"""
        if event.inaxes != self.ax:
            return
        
        # 获取点击位置的坐标
        x, y = event.xdata, event.ydata
        
        # 获取当前热力图数据
        if not hasattr(self, 'current_plot_cache') or not self.current_plot_cache or self.current_plot_cache.get('type') != 'heatmap':
            print("热力图缓存数据不可用")
            return
        
        heatmap_data = self.current_plot_cache['data']
        values = np.array(heatmap_data['values'])
        xticks = heatmap_data['xticks']
        yticks = heatmap_data['yticks']
        xticklabels = heatmap_data['xticklabels']
        yticklabels = heatmap_data['yticklabels']
        
        # 找到最近的格子索引
        if len(xticks) > 0 and len(yticks) > 0:
            x_idx = np.abs(xticks - x).argmin()
            y_idx = np.abs(yticks - y).argmin()
            
            if 0 <= x_idx < len(xticklabels) and 0 <= y_idx < len(yticklabels):
                # 获取对应的参数值
                pre_value = yticklabels[y_idx]
                main_value = xticklabels[x_idx]
                snr_value = values[y_idx, x_idx]
                
                # 显示点击信息
                info_text = f"点击位置: Pre={pre_value}, Main={main_value}\nSNR值: {snr_value:.3f}"
                self.status_var.set(info_text)
                
                # 更新信息显示区域
                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, f"🔍 热力图点击信息\n\n{info_text}")
                self.info_text.config(state=tk.DISABLED)
    
    def _redraw_scatter_plot(self):
        """重新绘制散点图（用于双击重置视角后恢复数据显示）"""
        if not hasattr(self, 'scatter_data') or not self.scatter_data:
            return
        
        try:
            # 清除当前图形但保留轴
            self.ax.clear()
            
            # 重新设置轴标签
            self.ax.set_xlabel('PRE')
            self.ax.set_ylabel('MAIN')
            self.ax.set_zlabel('POST')
            self.ax.set_title('3D散点图 - PRE/MAIN/POST vs SNR')
            
            # 重新绘制散点图
            pre_values = [point['pre'] for point in self.scatter_data]
            main_values = [point['main'] for point in self.scatter_data]
            post_values = [point['post'] for point in self.scatter_data]
            snr_values = [point['snr'] for point in self.scatter_data]
            
            # 使用SNR值作为颜色映射
            scatter = self.ax.scatter(pre_values, main_values, post_values, 
                                    c=snr_values, cmap='viridis', s=50, alpha=0.7)
            
            # 重新添加颜色条（如果之前有的话）
            if not hasattr(self, 'colorbar') or self.colorbar is None:
                self.colorbar = self.fig.colorbar(scatter, ax=self.ax, shrink=0.8)
                self.colorbar.set_label('SNR')
            
            print(f"重新绘制散点图完成: {len(self.scatter_data)} 个数据点")
            
        except Exception as e:
            print(f"重新绘制散点图错误: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 取消当前任务
            self.cancel_current_task = True
            
            # 关闭线程池
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=True)
                print("线程池已关闭")
        except Exception as e:
            print(f"清理资源时出错: {e}")
    
    def on_closing(self):
        """窗口关闭事件处理"""
        self.cleanup()
        self.root.destroy()
    
    def init_empty_plot(self):
        """初始化空图表"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, '📊 请加载数据文件开始分析', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes, fontsize=16, color='gray')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def clear_plot_cache(self):
        """清除绘图缓存"""
        self.plot_cache.clear()
        print("绘图缓存已清除")
    
    def restore_plot_from_cache(self, cached_data):
        """从缓存恢复绘图"""
        try:
            # 检查缓存数据格式
            if not isinstance(cached_data, dict) or 'type' not in cached_data:
                print("缓存数据格式错误")
                return
                
            # 根据图表类型清除当前图表
            if cached_data['type'] == 'scatter3d':
                # 对于3D散点图，需要重新创建3D子图
                self.fig.clear()
                self.ax = self.fig.add_subplot(111, projection='3d')
            else:
                # 对于其他图表类型，清除当前轴
                self.ax.clear()
            
            # 移除之前的颜色条
            if self.current_colorbar:
                try:
                    self.current_colorbar.remove()
                except:
                    pass
                self.current_colorbar = None
            
            # 恢复缓存的绘图数据
            plot_type = cached_data['type']
            data = cached_data['data']
            
            if plot_type == 'heatmap':
                im = self.ax.imshow(data['values'], cmap='viridis', aspect='auto', interpolation='nearest')
                self.ax.set_xticks(data['xticks'])
                self.ax.set_yticks(data['yticks'])
                self.ax.set_xticklabels(data['xticklabels'], rotation=45, color='black')
                self.ax.set_yticklabels(data['yticklabels'], color='black')
                self.ax.set_xlabel(data['xlabel'], fontsize=12, color='black')
                self.ax.set_ylabel(data['ylabel'], fontsize=12, color='black')
                self.ax.set_title(data['title'], fontsize=14, color='black')
                self.ax.tick_params(axis='both', colors='black')
                
                # 恢复颜色条
                self.current_colorbar = self.fig.colorbar(im, ax=self.ax, label='SNR值')
                
                # 恢复文本标注
                if 'text_annotations' in data:
                    for annotation in data['text_annotations']:
                        self.ax.text(annotation['x'], annotation['y'], annotation['text'], 
                                   ha='center', va='center', color=annotation['color'])
                
                # 保存当前热力图数据到缓存属性
                self.current_plot_cache = {
                    'type': 'heatmap',
                    'data': {
                        'values': data['values'],
                        'xticks': data['xticks'],
                        'yticks': data['yticks'],
                        'xticklabels': data['xticklabels'],
                        'yticklabels': data['yticklabels']
                    }
                }
            
            elif plot_type == 'scatter3d':
                # 恢复3D散点图
                scatter = self.ax.scatter(data['pre_values'], data['main_values'], data['post_values'], 
                                        c=data['snr_values'], cmap='viridis', s=60, alpha=0.7)
                
                # 恢复轴标签和标题
                self.ax.set_xlabel(data['xlabel'], fontsize=12, labelpad=10)
                self.ax.set_ylabel(data['ylabel'], fontsize=12, labelpad=10)
                self.ax.set_zlabel(data['zlabel'], fontsize=12, labelpad=10)
                self.ax.set_title(data['title'], fontsize=14, pad=20)
                
                # 恢复颜色条
                self.current_colorbar = self.fig.colorbar(scatter, ax=self.ax, shrink=0.8, aspect=20)
                self.current_colorbar.set_label('SNR (dB)', fontsize=12)
                
                # 恢复网格和视角
                self.ax.grid(True, alpha=0.3)
                self.ax.view_init(elev=data.get('elev', 20), azim=data.get('azim', 45))
                
                # 恢复统计信息
                if 'stats_text' in data:
                    self.ax.text2D(0.02, 0.98, data['stats_text'], transform=self.ax.transAxes, 
                                   fontsize=10, verticalalignment='top',
                                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                
                # 恢复交互功能
                if 'plot_data' in data:
                    self._add_3d_interaction(data['plot_data'])
            
            self.canvas.draw()
            print(f"从缓存恢复了 {plot_type} 图表")
            
        except Exception as e:
            print(f"缓存恢复失败: {str(e)}")
            # 如果缓存恢复失败，清除缓存但不重新绘制（避免递归）
            if isinstance(cached_data, dict):
                self.plot_cache.pop(cached_data.get('cache_key', ''), None)
            # 清空图表并显示错误信息
            self.ax.clear()
            if hasattr(self.ax, 'text'):
                self.ax.text(0.5, 0.5, '缓存数据损坏，请重新加载文件', 
                            ha='center', va='center', transform=self.ax.transAxes, 
                            fontsize=12, color='red')
            else:
                # 对于3D轴，使用text2D
                self.ax.text2D(0.5, 0.5, '缓存数据损坏，请重新加载文件', 
                              ha='center', va='center', transform=self.ax.transAxes, 
                              fontsize=12, color='red')
            self.canvas.draw()
    
    
    def plot_heatmap(self):
        """绘制热力图 - 优化显示效果，支持缓存"""
        try:
            # 创建数据透视表 - 修复：使用DataFrame
            pivot_data = self.df.pivot_table(
                values='snr', 
                index='post', 
                columns='main', 
                aggfunc='mean'
            )
            
            if pivot_data.empty:
                self.ax.text(0.5, 0.5, '❌ 数据不足以生成热力图', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.ax.transAxes, fontsize=14, color='red')
                return None
            
            # 准备缓存数据
            values = pivot_data.values
            xticks = list(range(len(pivot_data.columns)))
            yticks = list(range(len(pivot_data.index)))
            xticklabels = [self.format_hex(x) for x in pivot_data.columns]
            yticklabels = [self.format_hex(y) for y in pivot_data.index]
            xlabel = 'Main参数'
            ylabel = 'Post参数'
            title = f'SNR热力图 (Pre: {self.format_hex(self.current_pre)})'
            
            # 绘制热力图
            im = self.ax.imshow(values, cmap='viridis', aspect='auto', interpolation='nearest')
            
            # 设置坐标轴标签
            self.ax.set_xticks(xticks)
            self.ax.set_yticks(yticks)
            self.ax.set_xticklabels(xticklabels, rotation=45, color='black')
            self.ax.set_yticklabels(yticklabels, color='black')
            
            self.ax.set_xlabel(xlabel, fontsize=12, color='black')
            self.ax.set_ylabel(ylabel, fontsize=12, color='black')
            self.ax.set_title(title, fontsize=14, color='black')
            
            # 设置坐标轴刻度标签颜色
            self.ax.tick_params(axis='both', colors='black')
            
            # 添加颜色条
            self.current_colorbar = self.fig.colorbar(im, ax=self.ax, label='SNR值')
            
            # 在每个格子中显示数值并收集文本标注信息
            text_annotations = []
            mean_value = np.nanmean(values)
            for i in range(len(pivot_data.index)):
                for j in range(len(pivot_data.columns)):
                    value = pivot_data.iloc[i, j]
                    if not pd.isna(value):
                        color = 'black' if value < mean_value else 'white'
                        text = f'{value:.1f}'
                        self.ax.text(j, i, text, ha='center', va='center', color=color)
                        text_annotations.append({
                            'x': j, 'y': i, 'text': text, 'color': color
                        })
            
            # 绑定鼠标点击事件
            self.fig.canvas.mpl_connect('button_press_event', self.on_heatmap_click)
            
            # 保存当前热力图数据到缓存属性
            self.current_plot_cache = {
                'type': 'heatmap',
                'data': {
                    'values': values.tolist(),
                    'xticks': xticks,
                    'yticks': yticks,
                    'xticklabels': xticklabels,
                    'yticklabels': yticklabels
                }
            }
            
            # 返回缓存数据
            return {
                'type': 'heatmap',
                'data': {
                    'values': values.tolist(),
                    'xticks': xticks,
                    'yticks': yticks,
                    'xticklabels': xticklabels,
                    'yticklabels': yticklabels,
                    'xlabel': xlabel,
                    'ylabel': ylabel,
                    'title': title,
                    'text_annotations': text_annotations
                }
            }
            
        except KeyError as e:
            error_msg = f"数据列缺失: {e}"
            print(f"热力图绘制错误: {error_msg}")
            self.ax.text(0.5, 0.5, f'❌ {error_msg}', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12, color='red')
            return None
        except ValueError as e:
            error_msg = f"数据透视表生成失败: {e}"
            print(f"热力图绘制错误: {error_msg}")
            self.ax.text(0.5, 0.5, f'❌ {error_msg}', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12, color='red')
            return None
        except Exception as e:
            error_msg = f"热力图生成失败: {str(e)}"
            print(f"热力图绘制错误: {error_msg}")
            self.ax.text(0.5, 0.5, f'❌ {error_msg}', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12, color='red')
            return None
    
    def plot_all_configurations(self):
        """显示所有配置的SNR分布 - 优化布局，支持缓存"""
        try:
            # 计算每个配置组合的平均SNR - 修复：使用DataFrame
            config_stats = self.df.groupby(['pre', 'main', 'post'])['snr'].agg(['mean', 'std', 'count']).reset_index()
            config_stats = config_stats.sort_values('mean', ascending=False)
            
            if config_stats.empty:
                self.ax.text(0.5, 0.5, '❌ 没有可用的配置数据', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.ax.transAxes, fontsize=14, color='red')
                return None
            
            # 取前20个配置
            top_configs = config_stats.head(20)
            
            # 准备缓存数据
            x_data = list(range(len(top_configs)))
            y_data = top_configs['mean'].tolist()
            yerr_data = top_configs['std'].tolist()
            labels = [f'{self.format_hex(row.pre)}-{self.format_hex(row.main)}-{self.format_hex(row.post)}' 
                     for _, row in top_configs.iterrows()]
            colors = plt.cm.viridis(np.linspace(0, 1, len(top_configs))).tolist()
            xlabel = '配置组合 (Pre-Main-Post)'
            ylabel = '平均SNR值'
            title = 'Top 20 配置SNR性能排名'
            
            # 绘制柱状图
            bars = self.ax.bar(x_data, y_data, yerr=yerr_data, capsize=3, alpha=0.8, color=colors)
            
            self.ax.set_xlabel(xlabel, fontsize=12, color='black')
            self.ax.set_ylabel(ylabel, fontsize=12, color='black')
            self.ax.set_title(title, fontsize=14, color='black')
            self.ax.set_xticks(x_data)
            self.ax.set_xticklabels(labels, rotation=45, ha='right', color='black')
            self.ax.grid(True, alpha=0.3, axis='y', color='gray')
            
            # 设置坐标轴刻度标签颜色
            self.ax.tick_params(axis='both', colors='black')
            
            # 添加数值标签并收集标签信息
            value_labels = []
            for i, (bar, value) in enumerate(zip(bars, y_data)):
                label_text = f'{value:.1f}'
                self.ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           label_text, ha='center', va='bottom', fontsize=8, color='black')
                value_labels.append(label_text)
            
            # 调整布局
            plt.tight_layout()
            
            # 返回缓存数据
            return {
                'type': 'bar',
                'data': {
                    'x': x_data,
                    'y': y_data,
                    'yerr': yerr_data,
                    'colors': colors,
                    'xlabel': xlabel,
                    'ylabel': ylabel,
                    'title': title,
                    'xticks': x_data,
                    'xticklabels': labels,
                    'value_labels': value_labels
                }
            }
            
        except KeyError as e:
            error_msg = f"数据列缺失: {e}"
            print(f"全配置图绘制错误: {error_msg}")
            self.ax.text(0.5, 0.5, f'❌ {error_msg}', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12, color='red')
            return None
        except ValueError as e:
            error_msg = f"数据分组失败: {e}"
            print(f"全配置图绘制错误: {error_msg}")
            self.ax.text(0.5, 0.5, f'❌ {error_msg}', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12, color='red')
            return None
        except Exception as e:
            error_msg = f"配置分析失败: {str(e)}"
            print(f"全配置图绘制错误: {error_msg}")
            self.ax.text(0.5, 0.5, f'❌ {error_msg}', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12, color='red')
            return None
    
    def find_optimal_config(self):
        """查找全局最优配置 - 改进算法"""
        if not self.data:
            messagebox.showwarning("警告", "请先加载数据文件！")
            return
        
        try:
            # 计算每个配置组合的统计信息 - 修复：使用DataFrame
            config_stats = self.df.groupby(['pre', 'main', 'post'])['snr'].agg([
                'mean', 'std', 'count', 'min', 'max'
            ]).reset_index()
            
            # 计算综合评分 (平均值权重0.7，稳定性权重0.3)
            config_stats['stability_score'] = 1 / (1 + config_stats['std'])  # 标准差越小，稳定性越高
            config_stats['composite_score'] = (config_stats['mean'] * 0.7 + 
                                              config_stats['stability_score'] * config_stats['mean'] * 0.3)
            
            # 找到最优配置
            best_config = config_stats.loc[config_stats['composite_score'].idxmax()]
            
            # 显示结果
            result_text = f"""🎯 全局最优配置分析结果
            
📊 最优配置参数：
• Pre参数: {self.format_hex(int(best_config['pre']))} ({int(best_config['pre'])})
• Main参数: {self.format_hex(int(best_config['main']))} ({int(best_config['main'])})
• Post参数: {self.format_hex(int(best_config['post']))} ({int(best_config['post'])})

📈 性能指标：
• 平均SNR: {best_config['mean']:.3f}
• 标准差: {best_config['std']:.3f}
• 最小值: {best_config['min']:.3f}
• 最大值: {best_config['max']:.3f}
• 数据点数: {int(best_config['count'])}
• 综合评分: {best_config['composite_score']:.3f}

💡 评分说明：综合考虑平均性能(70%)和稳定性(30%)"""
            
            # 更新信息显示区域
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, result_text)
            self.info_text.config(state=tk.DISABLED)
            
            # 自动设置为最优配置并更新图表
            self.current_pre = int(best_config['pre'])
            self.current_main = int(best_config['main'])
            self.current_post = int(best_config['post'])
            
            # 更新下拉框选择
            try:
                pre_idx = self.pre_values.index(self.current_pre)
                main_idx = self.main_values.index(self.current_main)
                post_idx = self.post_values.index(self.current_post)
                
                self.pre_combobox.current(pre_idx)
                self.main_combobox.current(main_idx)
                self.post_combobox.current(post_idx)
            except ValueError:
                pass  # 如果找不到对应的索引，忽略
            
            self.update_plot()
            self.status_var.set(f"✅ 已找到最优配置并应用")
            
        except Exception as e:
            print(f"最优配置查找错误: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"查找最优配置失败：{str(e)}")
    
    def export_analysis(self):
        """导出分析数据 - 增强功能"""
        if not self.data:
            messagebox.showwarning("警告", "请先加载数据文件！")
            return
        
        try:
            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                title="保存分析报告",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
            )
            
            if not filename:
                return
            
            # 显示进度
            self.status_var.set("📊 正在生成分析报告...")
            self.root.update()
            
            if filename.endswith('.xlsx'):
                # 导出到Excel，包含多个工作表
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    # 原始数据
                    self.data.to_excel(writer, sheet_name='原始数据', index=False)
                    
                    # 配置统计
                    config_stats = self.data.groupby(['pre', 'main', 'post'])['snr'].agg([
                        'count', 'mean', 'std', 'min', 'max'
                    ]).round(3)
                    config_stats.to_excel(writer, sheet_name='配置统计')
                    
                    # 参数分析
                    pre_stats = self.data.groupby('pre')['snr'].agg(['count', 'mean', 'std']).round(3)
                    main_stats = self.data.groupby('main')['snr'].agg(['count', 'mean', 'std']).round(3)
                    post_stats = self.data.groupby('post')['snr'].agg(['count', 'mean', 'std']).round(3)
                    
                    pre_stats.to_excel(writer, sheet_name='Pre参数分析')
                    main_stats.to_excel(writer, sheet_name='Main参数分析')
                    post_stats.to_excel(writer, sheet_name='Post参数分析')
                    
                    # 最优配置
                    config_stats_with_score = config_stats.copy()
                    config_stats_with_score['stability_score'] = 1 / (1 + config_stats_with_score['std'])
                    config_stats_with_score['composite_score'] = (
                        config_stats_with_score['mean'] * 0.7 + 
                        config_stats_with_score['stability_score'] * config_stats_with_score['mean'] * 0.3
                    )
                    top_configs = config_stats_with_score.sort_values('composite_score', ascending=False).head(10)
                    top_configs.to_excel(writer, sheet_name='Top10最优配置')
                
                messagebox.showinfo("成功", f"分析报告已保存到：\n{filename}")
                
            else:
                # 导出到CSV
                config_stats = self.data.groupby(['pre', 'main', 'post'])['snr'].agg([
                    'count', 'mean', 'std', 'min', 'max'
                ]).round(3)
                config_stats.to_csv(filename)
                messagebox.showinfo("成功", f"配置统计数据已保存到：\n{filename}")
            
            self.status_var.set("✅ 分析报告导出完成")
            
        except Exception as e:
            print(f"导出错误: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"导出失败：{str(e)}")
            self.status_var.set("❌ 导出失败")
    
    def open_filter_panel(self):
        """打开数据筛选面板"""
        if not self.data:
            messagebox.showwarning("警告", "请先加载数据文件！")
            return
        
        try:
            # 如果筛选窗口已存在，则激活它
            if self.filter_window and self.filter_window.winfo_exists():
                self.filter_window.lift()
                self.filter_window.focus_force()
                return
        except tk.TclError:
            # 窗口已被销毁
            self.filter_window = None
        
        # 创建新的筛选窗口
        self.filter_window, self.filter_panel = create_filter_window(
            title="SNR数据筛选工具"
        )
        # 设置数据和回调函数
        self.filter_panel.set_data(self.data)
        self.filter_panel.set_filter_changed_callback(self.on_filter_applied)
    
    def open_search_panel(self):
        """打开数据搜索面板"""
        if not self.data:
            messagebox.showwarning("警告", "请先加载数据文件！")
            return
        
        try:
            # 如果搜索窗口已存在，则激活它
            if self.search_window and self.search_window.winfo_exists():
                self.search_window.lift()
                self.search_window.focus_force()
                return
        except tk.TclError:
            # 窗口已被销毁
            self.search_window = None
        
        # 创建新的搜索窗口
        self.search_window, self.search_panel = create_search_window(
            title="SNR数据搜索工具"
        )
        # 设置数据和回调函数
        self.search_panel.set_data(self.data)
        self.search_panel.set_result_selected_callback(self.on_search_result_selected)
    
    def on_filter_applied(self, filtered_data):
        """筛选应用回调函数"""
        try:
            self.filtered_data = filtered_data
            
            # 更新状态栏显示筛选结果
            total_count = len(self.data)
            filtered_count = len(filtered_data)
            self.status_var.set(
                f"🔍 筛选完成：{filtered_count}/{total_count} 条数据"
            )
            
            # 可选：自动更新图表显示筛选后的数据
            # 这里可以根据需要实现图表更新逻辑
            
        except Exception as e:
            print(f"筛选回调错误: {str(e)}")
            messagebox.showerror("错误", f"筛选结果处理失败：{str(e)}")
    
    def on_search_result_selected(self, selected_match):
        """搜索结果选择回调函数"""
        try:
            if selected_match:
                # 获取选中的数据点
                selected_data = selected_match.point
                
                # 自动设置为选中的配置
                self.current_pre = int(selected_data.pre)
                self.current_main = int(selected_data.main)
                self.current_post = int(selected_data.post)
                
                # 更新下拉框选择
                try:
                    pre_idx = self.pre_values.index(self.current_pre)
                    main_idx = self.main_values.index(self.current_main)
                    post_idx = self.post_values.index(self.current_post)
                    
                    self.pre_combobox.current(pre_idx)
                    self.main_combobox.current(main_idx)
                    self.post_combobox.current(post_idx)
                except ValueError:
                    pass  # 如果找不到对应的索引，忽略
                
                # 更新图表
                self.update_plot()
                
                # 更新状态栏
                self.status_var.set(
                    f"🎯 已选择配置：Pre={self.current_pre}, Main={self.current_main}, "
                    f"Post={self.current_post}, SNR={selected_data.snr:.2f}"
                )
                
        except Exception as e:
            print(f"搜索结果选择错误: {str(e)}")
            messagebox.showerror("错误", f"搜索结果处理失败：{str(e)}")
    
    def sync_data_to_panels(self):
        """同步数据到筛选和搜索面板"""
        try:
            # 如果筛选面板已打开，同步数据
            if self.filter_panel:
                self.filter_panel.set_data(self.data)
            
            # 如果搜索面板已打开，同步数据
            if self.search_panel:
                self.search_panel.set_data(self.data)
                
        except Exception as e:
            print(f"数据同步错误: {str(e)}")
    
    def export_filtered_data(self):
        """导出筛选结果数据"""
        if not self.filtered_data or len(self.filtered_data) == 0:
            messagebox.showinfo("信息", "没有筛选结果可导出，请先进行数据筛选")
            return
        
        # 选择保存文件路径
        file_path = filedialog.asksaveasfilename(
            title="导出筛选结果",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        # 保存为CSV文件
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                writer.writerow(['PRE', 'MAIN', 'POST', 'SNR'])
                
                # 写入筛选后的数据
                for point in self.filtered_data:
                    writer.writerow([point.pre, point.main, point.post, point.snr])
            
            messagebox.showinfo("成功", f"筛选结果已导出到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出筛选结果失败: {str(e)}")
    
    def export_search_results(self):
        """导出搜索结果数据"""
        # 检查是否有打开的搜索面板并且有搜索结果
        if not self.search_panel or not hasattr(self.search_panel, 'search_results') or not self.search_panel.search_results:
            messagebox.showinfo("信息", "没有搜索结果可导出，请先进行数据搜索")
            return
        
        search_results = self.search_panel.search_results
        if len(search_results) == 0:
            messagebox.showinfo("信息", "没有搜索结果可导出，请先进行数据搜索")
            return
        
        # 选择保存文件路径
        file_path = filedialog.asksaveasfilename(
            title="导出搜索结果",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        # 保存为CSV文件
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                writer.writerow(['序号', 'PRE', 'MAIN', 'POST', 'SNR', '相似度', '匹配类型', '匹配字段'])
                
                # 写入搜索结果
                for i, match in enumerate(search_results, 1):
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
            
            messagebox.showinfo("成功", f"搜索结果已导出到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出搜索结果失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SNRVisualizerOptimized(root)
    root.mainloop()