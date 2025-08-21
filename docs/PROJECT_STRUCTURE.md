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
│   ├── test_search_suggestions.py
│   ├── bug_detector.py   # Bug检测脚本
│   ├── program_functionality_test.py  # 程序功能测试脚本
│   └── simplified_automated_gui_test.py  # 简化版自动化GUI测试脚本
├── data/                 # 数据文件
│   ├── sample_snr_data.csv
│   └── test_data.csv
├── docs/                 # 文档
│   ├── PROJECT_STRUCTURE.md      # 项目结构说明
│   ├── V1.0_RELEASE_NOTES.md     # V1.0版本发布说明
│   ├── V2.0_PLANNING.md          # V2.0版本规划
│   ├── BUG_REPORT.md             # Bug检测报告
│   ├── TEST_REPORT.md            # 程序测试报告
│   ├── GUI_TEST_REPORT.md        # GUI测试报告
│   └── screenshots/              # 测试截图目录
├── .claude/              # Claude相关配置
├── .git/                 # Git版本控制
├── .gitignore            # Git忽略文件配置
├── .env                  # 环境变量配置（已忽略）
├── QWEN.md               # Qwen助手上下文
├── README.md             # 项目说明
├── VERSION.md            # 版本信息
├── TROUBLESHOOTING.md    # 故障排除指南
├── requirements.txt      # 依赖包列表
├── run.bat               # 启动脚本
└── snr_visualizer_optimized.py  # 主程序文件
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

## 版本状态

**当前版本**: V1.0 (完结版)  
**状态**: 正式发布  
**发布日期**: 2025年8月21日

## 核心功能

### 1. 多样化可视化支持
- 折线图、热力图、3D热力图、3D散点图、多子图

### 2. 专业交互功能
- 精确数据点拾取、实时信息显示、3D视图操作、智能缓存

### 3. 数据处理能力
- CSV格式支持、数据验证、异步加载、统计分析

### 4. 数据筛选和搜索功能 (V2.1)
- 参数范围筛选、SNR值筛选、组合筛选
- 精确搜索、模糊搜索、搜索建议、筛选结果高亮

### 5. 用户体验优化
- 现代化界面、中文支持、响应式布局、状态反馈

## 技术栈

- **Python 3.x**: 主要开发语言
- **Tkinter**: GUI框架
- **Matplotlib**: 图表绘制和3D可视化
- **Pandas**: 数据处理和分析
- **NumPy**: 数值计算支持

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

## 项目状态

- ✅ 所有功能开发完成
- ✅ 所有测试通过
- ✅ 文档完整
- ✅ 项目结构优化
- ✅ 版本正式发布

## 后续规划

### V3.0 版本规划
- 更多图表类型支持
- 图表导出功能增强
- 主题和样式自定义
- 界面响应式改进
- 数据缓存优化
- 配置管理增强

### 长期规划 (V4.0)
- 插件系统支持
- Web版本开发
- AI辅助数据分析
- 实时数据流支持
- 数据源扩展

---
*文档创建日期: 2025年8月21日*  
*项目状态: V1.0完结版*