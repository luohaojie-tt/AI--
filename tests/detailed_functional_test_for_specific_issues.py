#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNR数据可视化工具 - 详细功能测试脚本
针对性测试您提到的具体问题
"""

import sys
import os
import time
import subprocess
import threading
from datetime import datetime
from PIL import Image, ImageGrab
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 创建截图目录
screenshots_dir = os.path.join(project_root, 'docs', 'detailed_screenshots')
if not os.path.exists(screenshots_dir):
    os.makedirs(screenshots_dir)

class DetailedBugDetector:
    """详细Bug检测器"""
    
    def __init__(self):
        self.bugs_found = []
        self.warnings_found = []
        self.info_messages = []
        
    def add_bug(self, severity, component, description, details=None, screenshot=None):
        """添加bug报告"""
        bug = {
            'severity': severity,
            'component': component,
            'description': description,
            'details': details,
            'screenshot': screenshot,
            'timestamp': datetime.now()
        }
        self.bugs_found.append(bug)
        print(f"[{severity.upper()}] {component}: {description}")
        
    def add_warning(self, component, description, details=None, screenshot=None):
        """添加警告"""
        warning = {
            'component': component,
            'description': description,
            'details': details,
            'screenshot': screenshot,
            'timestamp': datetime.now()
        }
        self.warnings_found.append(warning)
        print(f"[WARNING] {component}: {description}")
        
    def add_info(self, component, description, details=None, screenshot=None):
        """添加信息"""
        info = {
            'component': component,
            'description': description,
            'details': details,
            'screenshot': screenshot,
            'timestamp': datetime.now()
        }
        self.info_messages.append(info)
        print(f"[INFO] {component}: {description}")

def take_screenshot(filename):
    """截取屏幕截图"""
    try:
        # 使用Pillow截图
        screenshot = ImageGrab.grab()
        # 保存截图
        filepath = os.path.join(screenshots_dir, f"{filename}.png")
        screenshot.save(filepath)
        print(f"[INFO] 截图已保存: {filepath}")
        return filepath
    except Exception as e:
        print(f"[ERROR] 截图失败: {e}")
        return None

def analyze_screenshot_for_graph_content(screenshot_path, bug_detector):
    """分析截图中图表内容是否存在"""
    try:
        # 加载图像
        img = Image.open(screenshot_path)
        if img is None:
            return
            
        # 转换为灰度图
        gray_img = img.convert('L')
        gray_array = np.array(gray_img)
        
        # 计算图像平均亮度
        mean_brightness = np.mean(gray_array)
        
        # 检查图像是否全黑（可能表示程序崩溃或未正确显示）
        if mean_brightness < 10:
            bug_detector.add_bug("high", "Display", "图像全黑，可能程序未正确显示", 
                               "截图分析显示图像几乎全黑", screenshot_path)
            return
            
        # 检查图像是否全白（可能表示显示异常）
        if mean_brightness > 245:
            bug_detector.add_warning("Display", "图像过亮", 
                                   "截图分析显示图像过于明亮", screenshot_path)
            return
            
        # 检查图像是否有足够的变化（判断是否有图表内容）
        std_deviation = np.std(gray_array)
        if std_deviation < 20:  # 如果标准差很小，可能表示没有图表内容
            bug_detector.add_warning("Chart Display", "图表内容可能缺失", 
                                   f"图像变化较小(STD: {std_deviation:.2f})，可能没有正确显示图表", screenshot_path)
            
        bug_detector.add_info("Screenshot Analysis", "截图分析完成", 
                            f"图像尺寸: {img.size}, 平均亮度: {mean_brightness:.2f}, STD: {std_deviation:.2f}", screenshot_path)
        
    except Exception as e:
        print(f"[ERROR] 截图分析失败: {e}")

def detailed_functional_test():
    """详细功能测试 - 针对您提到的具体问题"""
    print("=== SNR数据可视化工具详细功能测试 ===")
    print("针对性测试您提到的具体问题")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    bug_detector = DetailedBugDetector()
    
    try:
        # 1. 启动程序并加载数据文件
        print("[INFO] 1. 启动程序并加载数据文件...")
        
        # 首先启动程序
        print("[INFO] 启动SNR数据可视化工具...")
        app_process = subprocess.Popen([
            sys.executable, 
            os.path.join(project_root, 'snr_visualizer_optimized.py')
        ], cwd=project_root)
        
        print("[INFO] 程序已启动，等待初始化...")
        time.sleep(5)  # 等待程序初始化
        
        # 截取主程序启动截图
        screenshot_path = take_screenshot("01_main_window_startup")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("Program Startup", "程序启动成功", 
                                "主窗口正常显示", screenshot_path)
        
        # 等待用户手动加载文件（这里我们假设用户已经加载了文件）
        print("[INFO] 请手动加载数据文件(sample_snr_data.csv)...")
        time.sleep(3)
        screenshot_path = take_screenshot("02_after_load_data")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("Data Loading", "数据加载界面", 
                                "数据加载后界面显示", screenshot_path)
        
        # 2. 测试折线图显示
        print("[INFO] 3. 测试折线图显示...")
        print("[INFO] 请手动切换到折线图视图...")
        time.sleep(3)
        screenshot_path = take_screenshot("03_line_chart")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("Line Chart", "折线图显示", 
                                "折线图界面显示", screenshot_path)
        
        # 3. 测试3D散点图显示
        print("[INFO] 4. 测试3D散点图显示...")
        print("[INFO] 请手动切换到3D散点图视图...")
        time.sleep(3)
        screenshot_path = take_screenshot("04_3d_scatter")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("3D Scatter", "3D散点图显示", 
                                "3D散点图界面显示", screenshot_path)
        
        # 4. 测试热力图显示
        print("[INFO] 5. 测试热力图显示...")
        print("[INFO] 请手动切换到热力图视图...")
        time.sleep(3)
        screenshot_path = take_screenshot("05_heatmap")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("Heatmap", "热力图显示", 
                                "热力图界面显示", screenshot_path)
        
        # 5. 测试3D热力图显示
        print("[INFO] 6. 测试3D热力图显示...")
        print("[INFO] 请手动切换到3D热力图视图...")
        time.sleep(3)
        screenshot_path = take_screenshot("06_3d_heatmap")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("3D Heatmap", "3D热力图显示", 
                                "3D热力图界面显示", screenshot_path)
        
        # 6. 测试图表间切换功能
        print("[INFO] 7. 测试图表间切换功能...")
        print("[INFO] 请手动在不同图表间切换几次...")
        time.sleep(3)
        screenshot_path = take_screenshot("07_chart_switching")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("Chart Switching", "图表切换功能", 
                                "图表切换后界面显示", screenshot_path)
        
        # 7. 测试全局配置功能
        print("[INFO] 8. 测试全局配置功能...")
        print("[INFO] 请手动使用筛选和搜索功能...")
        time.sleep(3)
        screenshot_path = take_screenshot("08_global_config")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("Global Config", "全局配置功能", 
                                "全局配置界面显示", screenshot_path)
        
        # 8. 测试查找最优SNR功能
        print("[INFO] 9. 测试查找最优SNR功能...")
        print("[INFO] 请手动使用查找最优SNR功能...")
        time.sleep(3)
        screenshot_path = take_screenshot("09_find_best_snr")
        if screenshot_path:
            analyze_screenshot_for_graph_content(screenshot_path, bug_detector)
            bug_detector.add_info("Find Best SNR", "查找最优SNR功能", 
                                "查找最优SNR界面显示", screenshot_path)
        
        # 测试完成
        print("[INFO] 详细功能测试完成")
        
        # 关闭程序
        print("[INFO] 关闭程序...")
        try:
            app_process.terminate()
            app_process.wait(timeout=5)
        except:
            app_process.kill()
        print("[INFO] 程序已关闭")
        
        return bug_detector
        
    except Exception as e:
        print(f"[ERROR] 详细功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        screenshot_path = take_screenshot("99_test_error")
        if screenshot_path:
            bug_detector.add_bug("high", "Test Framework", "测试框架错误", 
                               str(e), screenshot_path)
        
        # 关闭程序
        if 'app_process' in locals():
            try:
                app_process.terminate()
                app_process.wait(timeout=5)
            except:
                app_process.kill()
        
        return bug_detector

def create_detailed_bug_report(bug_detector):
    """创建详细bug报告"""
    print("\n=== 生成详细Bug报告 ===")
    
    report_file = os.path.join(project_root, 'docs', 'DETAILED_BUG_ANALYSIS_REPORT.md')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# SNR数据可视化工具 详细Bug分析报告\n\n")
            f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 报告概述\n\n")
            f.write("本报告针对您提到的具体问题，对SNR数据可视化工具V1.0版本进行详细的功能测试和Bug分析。\n")
            f.write("测试重点包括：折线图加载、3D散点图加载、图表间切换、全局配置、查找最优SNR等功能。\n\n")
            
            f.write("## 测试方法\n\n")
            f.write("1. 启动程序并手动加载数据文件\n")
            f.write("2. 逐一测试各个图表显示功能\n")
            f.write("3. 测试图表间切换功能\n")
            f.write("4. 测试全局配置和查找最优SNR功能\n")
            f.write("5. 通过截图分析判断功能是否正常\n\n")
            
            f.write("## 检测结果\n\n")
            f.write(f"**发现的Bug**: {len(bug_detector.bugs_found)}\n")
            f.write(f"**警告**: {len(bug_detector.warnings_found)}\n")
            f.write(f"**信息**: {len(bug_detector.info_messages)}\n\n")
            
            if bug_detector.bugs_found:
                f.write("## 发现的Bug\n\n")
                for i, bug in enumerate(bug_detector.bugs_found, 1):
                    f.write(f"{i}. **[{bug['severity'].upper()}]** {bug['component']}: {bug['description']}\n")
                    if bug['details']:
                        f.write(f"   详情: {bug['details']}\n")
                    if bug['screenshot']:
                        f.write(f"   截图: ![截图]({os.path.relpath(bug['screenshot'], project_root).replace(os.sep, '/')})\n")
                    f.write("\n")
            
            if bug_detector.warnings_found:
                f.write("## 警告\n\n")
                for i, warning in enumerate(bug_detector.warnings_found, 1):
                    f.write(f"{i}. {warning['component']}: {warning['description']}\n")
                    if warning['details']:
                        f.write(f"   详情: {warning['details']}\n")
                    if warning['screenshot']:
                        f.write(f"   截图: ![截图]({os.path.relpath(warning['screenshot'], project_root).replace(os.sep, '/')})\n")
                    f.write("\n")
            
            if bug_detector.info_messages:
                f.write("## 信息\n\n")
                for i, info in enumerate(bug_detector.info_messages, 1):
                    f.write(f"{i}. {info['component']}: {info['description']}\n")
                    if info['details']:
                        f.write(f"   详情: {info['details']}\n")
                    if info['screenshot']:
                        f.write(f"   截图: ![截图]({os.path.relpath(info['screenshot'], project_root).replace(os.sep, '/')})\n")
                    f.write("\n")
        
        print(f"[INFO] 详细Bug分析报告已生成: {report_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 生成详细Bug分析报告失败: {e}")
        return False

def main():
    """主函数"""
    print("SNR数据可视化工具 - 详细功能测试和Bug检测")
    print("=" * 60)
    print("请按照提示手动操作程序，测试各个功能模块")
    print("=" * 60)
    
    # 运行详细功能测试和bug检测
    bug_detector = detailed_functional_test()
    
    # 创建详细bug报告
    report_success = create_detailed_bug_report(bug_detector)
    
    print("\n" + "=" * 60)
    print("测试结果摘要:")
    print(f"  发现的Bug: {len(bug_detector.bugs_found)}")
    print(f"  警告: {len(bug_detector.warnings_found)}")
    print(f"  信息: {len(bug_detector.info_messages)}")
    
    if report_success:
        print("\n详细测试完成！")
        print("请查看 docs/DETAILED_BUG_ANALYSIS_REPORT.md 获取详细Bug分析报告")
        print("请查看 docs/detailed_screenshots/ 目录获取界面截图")
        print("\n请注意：本次测试需要您手动操作程序来验证各项功能。")
        print("如果您发现了具体的问题，请告诉我详细的操作步骤，我可以帮您创建更针对性的测试。")
    else:
        print("\n测试过程中出现错误，请检查上述信息")

if __name__ == "__main__":
    main()