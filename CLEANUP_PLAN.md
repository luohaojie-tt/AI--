# A股短线选股应用清理计划

## 目标
将当前SNR_SHOW目录清理为一个全新的A股短线选股应用项目，移除所有之前项目的遗留内容。

## 保留的文件和目录

### 核心代码
- `core/` - 包含股票选股应用的核心代码
- `stock_selector.py` - 主脚本
- `requirements.txt` - 依赖文件

### 数据
- `data/` - 包含项目进度跟踪和数据库文件

### 文档
- `docs/` - 包含项目文档

### 配置文件
- `.env` - 环境变量
- `.gitignore` - Git忽略文件

## 需要删除的文件和目录

### 旧项目文件
- `QWEN.md` - 与当前项目无关
- `README.md` - 旧项目的README，需要重新创建
- `run.bat` - 旧项目的运行脚本
- `snr_visualizer_optimized.py` - 旧项目的可视化工具
- `VERSION.md` - 旧项目的版本文档
- `VERSION.txt` - 旧项目的版本文件
- `TROUBLESHOOTING.md` - 旧项目的故障排除文档

### 测试文件
- `test_*.py` - 所有测试脚本，将在新项目中重新创建
- `test_data.csv` - 旧测试数据

### 爬取临时文件
- `*.html` - 所有HTML临时文件
- `*.json` - 除配置文件外的所有JSON文件
- `*.txt` - 除配置文件外的所有TXT文件
- `.cookie.txt` - Cookie文件

### 旧项目目录
- `filters/` - 旧项目的过滤模块
- `logs/` - 旧项目的日志目录
- `patches/` - 旧项目的补丁目录
- `tests/` - 旧项目的测试目录，将在新项目中重新创建
- `ui/` - 旧项目的UI目录
- `V3.0_backup/` - 旧项目的备份
- `V4.0_release/` - 旧项目的发布版本
- `__pycache__/` - Python编译缓存

### IDE相关
- `.claude/` - Claude相关配置
- `.trae/` - Trae相关配置

## 执行步骤

1. 删除所有需要删除的文件和目录
2. 重新创建必要的目录结构
3. 初始化Git仓库（如果需要）
4. 创建新的README.md文件
5. 确保项目能够正常运行

## 预期结果

一个干净的、只包含A股短线选股应用相关内容的项目目录，便于后续开发和维护。