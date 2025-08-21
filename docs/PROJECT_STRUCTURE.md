# 项目结构说明

## 目录结构

```
SNR_SHOW/
├── core/                 # 核心模块
│   ├── config.py         # 配置管理
│   ├── data_manager.py   # 数据管理
│   └── visualization.py  # 可视化模块
├── filters/              # 筛选和搜索模块
│   ├── filter_manager.py # 筛选管理器
│   ├── filter_models.py  # 数据模型
│   └── search_manager.py # 搜索管理器
├── ui/                   # 用户界面模块
│   ├── filter_panel.py   # 筛选面板
│   └── search_panel.py   # 搜索面板
├── tests/                # 测试文件
│   ├── test_all_features.py
│   ├── test_filter_search.py
│   ├── test_integration.py
│   └── test_search_suggestions.py
├── data/                 # 数据文件
│   ├── sample_snr_data.csv
│   └── test_data.csv
├── docs/                 # 文档
│   ├── V2.0_PLANNING.md
│   ├── V2.1_DataFilter/
│   ├── V2.1数据筛选和搜索功能/
│   └── UPDATE_LOG_20250821.md
├── requirements.txt      # 依赖包列表
├── run.bat               # 启动脚本
├── README.md             # 项目说明
├── QWEN.md               # Qwen助手上下文
├── TROUBLESHOOTING.md    # 故障排除指南
└── VERSION.md            # 版本信息
```

## 模块说明

### 核心模块 (core/)
包含应用程序的核心功能组件：
- **config.py**: 应用程序配置管理，包括主题、图表和UI配置
- **data_manager.py**: 数据加载、验证、处理和分析功能
- **visualization.py**: 图表绘制和可视化组件

### 筛选和搜索模块 (filters/)
实现数据筛选和搜索功能：
- **filter_models.py**: 定义筛选条件和搜索参数的数据结构
- **filter_manager.py**: 实现数据筛选逻辑和缓存机制
- **search_manager.py**: 实现数据搜索算法和搜索建议功能

### 用户界面模块 (ui/)
提供用户界面组件：
- **filter_panel.py**: 筛选面板UI组件和交互逻辑
- **search_panel.py**: 搜索面板UI组件和交互逻辑

### 测试文件 (tests/)
包含所有测试用例：
- **test_all_features.py**: 完整功能测试
- **test_filter_search.py**: 筛选和搜索功能测试
- **test_integration.py**: 集成测试
- **test_search_suggestions.py**: 搜索建议功能测试

### 数据文件 (data/)
包含示例数据和测试数据：
- **sample_snr_data.csv**: 示例SNR数据文件
- **test_data.csv**: 测试数据文件

## 运行方式

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用程序：
   ```bash
   python snr_visualizer_optimized.py
   ```
   或使用批处理脚本：
   ```bash
   run.bat
   ```

3. 运行测试：
   ```bash
   cd tests
   python test_all_features.py
   ```

## 更新日志

最新的结构优化和功能修复记录在 `docs/UPDATE_LOG_20250821.md` 文件中。