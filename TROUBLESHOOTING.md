# SNR配置可视化工具故障排除指南

如果您在运行SNR配置可视化工具时遇到问题，请按照以下步骤进行故障排除。

## 常见问题

### 1. 双击批处理文件没有反应

如果您双击`run_snr_visualizer.bat`或`run_snr_visualizer_advanced.bat`没有任何反应，可能有以下几个原因：

#### 可能的原因：

- **Python未安装**：程序需要Python 3.6或更高版本才能运行。
- **Python未添加到PATH**：即使安装了Python，如果未添加到系统PATH环境变量，批处理文件也无法找到Python。
- **依赖项未安装**：程序需要numpy、matplotlib和pandas库。
- **批处理文件权限问题**：批处理文件可能没有执行权限。
- **命令窗口闪退**：如果程序出错，命令窗口可能会立即关闭，看起来像没有反应。

#### 解决方案：

1. **使用新的简化启动脚本**：
   - 双击`start_visualizer.bat`，这是一个增强版的启动脚本，提供更详细的错误信息。

2. **测试Python环境**：
   - 双击`test_environment.bat`运行环境测试脚本，检查Python安装和依赖项。

3. **手动检查Python安装**：
   - 打开命令提示符（按Win+R，输入cmd，按回车）
   - 输入`python --version`并按回车
   - 如果显示版本号，说明Python已安装；如果显示"不是内部或外部命令"，则需要安装Python或将其添加到PATH。

4. **手动安装依赖项**：
   - 打开命令提示符
   - 输入以下命令：
     ```
     python -m pip install --upgrade pip
     python -m pip install numpy matplotlib pandas
     ```

5. **手动运行Python脚本**：
   - 打开命令提示符
   - 导航到程序所在目录：`cd 程序所在路径`（例如：`cd C:\Users\lhj\Desktop\work\AI\SNR_SHOW`）
   - 运行脚本：`python snr_visualizer.py`或`python snr_visualizer_advanced.py`
   - 这样可以看到详细的错误信息，而不会立即关闭窗口

### 2. 程序启动但显示错误

如果程序启动但显示错误消息，请注意错误内容并参考以下解决方案：

#### 常见错误和解决方案：

- **ModuleNotFoundError**：表示缺少依赖库，请按照上述步骤4安装依赖项。
- **FileNotFoundError**：表示找不到数据文件，请确保`sample_snr_data.txt`文件存在于程序目录中。
- **SyntaxError**：可能是Python版本不兼容，请确保使用Python 3.6或更高版本。
- **PermissionError**：表示权限不足，请尝试以管理员身份运行批处理文件。

## 高级故障排除

### 检查日志文件

运行`start_visualizer.bat`后，会在同一目录下生成`start_visualizer_log.txt`日志文件，查看此文件可以获取更详细的错误信息。

### 检查Python路径

如果您有多个Python版本，可能会导致冲突。请确保系统PATH中的Python版本与您安装的依赖项版本兼容。

### 重新安装Python

如果以上方法都无效，可以尝试重新安装Python：

1. 从[Python官网](https://www.python.org/downloads/)下载最新版本
2. 安装时勾选"Add Python to PATH"
3. 安装完成后，重新安装依赖项

## 联系支持

如果您尝试了以上所有方法仍然无法解决问题，请提供以下信息寻求帮助：

1. 操作系统版本
2. Python版本（如果已安装）
3. 错误日志（start_visualizer_log.txt或python_error.txt）
4. 尝试过的解决方案

祝您使用愉快！