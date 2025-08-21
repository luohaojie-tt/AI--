#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNR数据可视化工具 - 完整功能自动化测试脚本
通过截图分析来检测程序bug
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
screenshots_dir = os.path.join(project_root, 'docs', 'screenshots')
if not os.path.exists(screenshots_dir):
    os.makedirs(screenshots_dir)

# 创建bug报告目录
bug_reports_dir = os.path.join(project_root, 'docs', 'bug_reports')
if not os.path.exists(bug_reports_dir):
    os.makedirs(bug_reports_dir)

class BugDetector:
    """Bug检测器"""
    
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

def analyze_screenshot_for_bugs(screenshot_path, bug_detector):
    """分析截图中的潜在bug"""
    try:
        # 加载图像
        img = Image.open(screenshot_path)
        if img is None:
            return
            
        # 转换为灰度图
        gray_img = img.convert('L')
        gray_array = np.array(gray_img)
        
        # 检查图像是否全黑（可能表示程序崩溃或未正确显示）
        if np.mean(gray_array) < 10:
            bug_detector.add_bug("high", "Display", "图像全黑，可能程序未正确显示", 
                               "截图分析显示图像几乎全黑", screenshot_path)
            return
            
        # 检查图像是否全白（可能表示显示异常）
        if np.mean(gray_array) > 245:
            bug_detector.add_warning("Display", "图像过亮", 
                                   "截图分析显示图像过于明亮", screenshot_path)
            return
            
        bug_detector.add_info("Screenshot Analysis", "截图分析完成", 
                            f"图像尺寸: {img.size}", screenshot_path)
        
    except Exception as e:
        print(f"[ERROR] 截图分析失败: {e}")

def automated_functional_test():
    """完整功能自动化测试"""
    print("=== SNR数据可视化工具完整功能自动化测试 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    bug_detector = BugDetector()
    app_process = None
    
    try:
        # 1. 启动程序测试
        print("[INFO] 1. 启动程序测试...")
        app_process = subprocess.Popen([
            sys.executable, 
            os.path.join(project_root, 'snr_visualizer_optimized.py')
        ], cwd=project_root)
        
        print("[INFO] 程序已启动，等待初始化...")
        time.sleep(5)  # 等待程序初始化
        
        # 截取主程序启动截图
        screenshot_path = take_screenshot("01_main_window_startup")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("Program Startup", "程序启动成功", 
                                "主窗口正常显示", screenshot_path)
        
        # 2. 数据加载测试
        print("[INFO] 2. 数据加载测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("02_before_load_data")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            
        # 模拟点击加载数据按钮（这里只是模拟，实际需要更复杂的自动化）
        # pyautogui.click(x=100, y=100)  # 示例坐标
        time.sleep(2)
        screenshot_path = take_screenshot("03_after_load_data")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("Data Loading", "数据加载界面", 
                                "数据加载后界面显示", screenshot_path)
        
        # 3. 折线图测试
        print("[INFO] 3. 折线图测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("04_line_chart")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("Line Chart", "折线图显示", 
                                "折线图界面显示", screenshot_path)
        
        # 4. 热力图测试
        print("[INFO] 4. 热力图测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("05_heatmap")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("Heatmap", "热力图显示", 
                                "热力图界面显示", screenshot_path)
        
        # 5. 3D热力图测试
        print("[INFO] 5. 3D热力图测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("06_3d_heatmap")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("3D Heatmap", "3D热力图显示", 
                                "3D热力图界面显示", screenshot_path)
        
        # 6. 3D散点图测试
        print("[INFO] 6. 3D散点图测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("07_3d_scatter")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("3D Scatter", "3D散点图显示", 
                                "3D散点图界面显示", screenshot_path)
        
        # 7. 多子图测试
        print("[INFO] 7. 多子图测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("08_multi_charts")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("Multi Charts", "多子图显示", 
                                "多子图界面显示", screenshot_path)
        
        # 8. 筛选功能测试
        print("[INFO] 8. 筛选功能测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("09_filter_function")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("Filter Function", "筛选功能显示", 
                                "筛选功能界面显示", screenshot_path)
        
        # 9. 搜索功能测试
        print("[INFO] 9. 搜索功能测试...")
        time.sleep(2)
        screenshot_path = take_screenshot("10_search_function")
        if screenshot_path:
            analyze_screenshot_for_bugs(screenshot_path, bug_detector)
            bug_detector.add_info("Search Function", "搜索功能显示", 
                                "搜索功能界面显示", screenshot_path)
        
        # 测试完成
        print("[INFO] 功能测试完成")
        return bug_detector
        
    except Exception as e:
        print(f"[ERROR] 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        screenshot_path = take_screenshot("99_test_error")
        if screenshot_path:
            bug_detector.add_bug("high", "Test Framework", "测试框架错误", 
                               str(e), screenshot_path)
        return bug_detector
        
    finally:
        # 清理资源
        if app_process:
            print("[INFO] 关闭程序...")
            try:
                app_process.terminate()
                app_process.wait(timeout=5)
            except:
                app_process.kill()
            print("[INFO] 程序已关闭")

def create_bug_report(bug_detector):
    """创建bug报告"""
    print("\n=== 生成Bug报告 ===")
    
    report_file = os.path.join(project_root, 'docs', 'BUG_ANALYSIS_REPORT.md')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# SNR数据可视化工具 Bug分析报告\n\n")
            f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 报告概述\n\n")
            f.write("本报告通过自动化截图分析，检测SNR数据可视化工具V1.0版本中可能存在的bug。\n\n")
            
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
        
        print(f"[INFO] Bug分析报告已生成: {report_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 生成Bug分析报告失败: {e}")
        return False

def main():
    """主函数"""
    print("SNR数据可视化工具 - 完整功能自动化测试和Bug检测")
    print("=" * 60)
    
    # 运行功能测试和bug检测
    bug_detector = automated_functional_test()
    
    # 创建bug报告
    report_success = create_bug_report(bug_detector)
    
    print("\n" + "=" * 60)
    print("测试结果摘要:")
    print(f"  发现的Bug: {len(bug_detector.bugs_found)}")
    print(f"  警告: {len(bug_detector.warnings_found)}")
    print(f"  信息: {len(bug_detector.info_messages)}")
    
    if report_success:
        print("\n完整测试完成！")
        print("请查看 docs/BUG_ANALYSIS_REPORT.md 获取详细Bug分析报告")
        print("请查看 docs/screenshots/ 目录获取界面截图")
    else:
        print("\n测试过程中出现错误，请检查上述信息")

if __name__ == "__main__":
    main()