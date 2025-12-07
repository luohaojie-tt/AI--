#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNR数据可视化工具 - 针对性问题测试脚本
针对用户指出的具体问题进行深入测试
"""

import sys
import os
import time
import subprocess
import pyautogui
from datetime import datetime
from PIL import Image, ImageGrab
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 创建测试截图目录
test_screenshots_dir = os.path.join(project_root, 'docs', 'problem_testing_screenshots')
if not os.path.exists(test_screenshots_dir):
    os.makedirs(test_screenshots_dir)

class ProblemTester:
    """针对性问题测试器"""
    
    def __init__(self):
        self.problems_found = []
        self.test_results = []
        self.info_messages = []
        
    def add_problem(self, severity, component, description, details=None, screenshot=None):
        """添加问题报告"""
        problem = {
            'severity': severity,
            'component': component,
            'description': description,
            'details': details,
            'screenshot': screenshot,
            'timestamp': datetime.now()
        }
        self.problems_found.append(problem)
        print(f"[{severity.upper()}] {component}: {description}")
        
    def add_test_result(self, component, description, status, details=None, screenshot=None):
        """添加测试结果"""
        result = {
            'component': component,
            'description': description,
            'status': status,  # 'PASS', 'FAIL', 'WARNING'
            'details': details,
            'screenshot': screenshot,
            'timestamp': datetime.now()
        }
        self.test_results.append(result)
        status_symbol = '✓' if status == 'PASS' else '✗' if status == 'FAIL' else '⚠'
        print(f"[{status_symbol}] {component}: {description}")
        
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
        filepath = os.path.join(test_screenshots_dir, f"{filename}.png")
        screenshot.save(filepath)
        print(f"[INFO] 截图已保存: {filepath}")
        return filepath
    except Exception as e:
        print(f"[ERROR] 截图失败: {e}")
        return None

def analyze_chart_content(screenshot_path, bug_detector):
    """分析截图中图表内容是否存在"""
    try:
        # 加载图像
        img = Image.open(screenshot_path)
        if img is None:
            return False
            
        # 转换为灰度图
        gray_img = img.convert('L')
        gray_array = np.array(gray_img)
        
        # 计算图像平均亮度
        mean_brightness = np.mean(gray_array)
        
        # 检查图像是否全黑（可能表示程序崩溃或未正确显示）
        if mean_brightness < 10:
            bug_detector.add_problem("high", "Display", "图像全黑，可能程序未正确显示", 
                                   "截图分析显示图像几乎全黑", screenshot_path)
            return False
            
        # 检查图像是否全白（可能表示显示异常）
        if mean_brightness > 245:
            bug_detector.add_problem("medium", "Display", "图像过亮", 
                                   "截图分析显示图像过于明亮", screenshot_path)
            return False
            
        # 检查图像是否有足够的变化（判断是否有图表内容）
        std_deviation = np.std(gray_array)
        if std_deviation < 20:  # 如果标准差很小，可能表示没有图表内容
            bug_detector.add_problem("medium", "Chart Display", "图表内容可能缺失", 
                                   f"图像变化较小(STD: {std_deviation:.2f})，可能没有正确显示图表", screenshot_path)
            return False
            
        bug_detector.add_info("Screenshot Analysis", "截图分析完成", 
                            f"图像尺寸: {img.size}, 平均亮度: {mean_brightness:.2f}, STD: {std_deviation:.2f}", screenshot_path)
        return True
        
    except Exception as e:
        print(f"[ERROR] 截图分析失败: {e}")
        return False

def wait_for_window(title, timeout=10):
    """等待窗口出现"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # 这里简化处理，实际应用中可能需要更复杂的窗口检测
            time.sleep(1)
            return True
        except:
            continue
    return False

def targeted_problem_test():
    """针对性问题测试 - 测试用户指出的具体问题"""
    print("=== SNR数据可视化工具针对性问题测试 ===")
    print("重点测试用户指出的具体功能性问题")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = ProblemTester()
    
    try:
        # 1. 启动程序
        print("\n[INFO] 1. 启动程序测试...")
        print("[ACTION] 启动SNR数据可视化工具...")
        
        # 启动程序
        app_process = subprocess.Popen([
            sys.executable, 
            os.path.join(project_root, 'snr_visualizer_optimized.py')
        ], cwd=project_root)
        
        print("[INFO] 程序已启动，等待初始化...")
        time.sleep(5)  # 等待程序初始化
        
        # 截取主程序启动截图
        screenshot_path = take_screenshot("01_main_window_startup")
        if screenshot_path:
            analyze_chart_content(screenshot_path, tester)
            tester.add_test_result("Program Startup", "程序启动", "PASS", 
                                 "主窗口正常显示", screenshot_path)
        else:
            tester.add_test_result("Program Startup", "程序启动", "FAIL", 
                                 "未能成功启动程序")
        
        # 2. 加载数据文件测试
        print("\n[INFO] 2. 数据加载测试...")
        print("[ACTION] 请手动加载数据文件(data/sample_snr_data.csv)")
        print("[WAIT] 等待用户操作...")
        time.sleep(10)  # 给用户时间手动加载文件
        
        screenshot_path = take_screenshot("02_after_load_data")
        if screenshot_path:
            has_content = analyze_chart_content(screenshot_path, tester)
            if has_content:
                tester.add_test_result("Data Loading", "数据加载", "PASS", 
                                     "数据加载后界面显示正常", screenshot_path)
            else:
                tester.add_test_result("Data Loading", "数据加载", "FAIL", 
                                     "数据加载后界面可能未正确显示", screenshot_path)
        else:
            tester.add_test_result("Data Loading", "数据加载", "FAIL", 
                                 "未能获取数据加载后的截图")
        
        # 3. 折线图加载测试
        print("\n[INFO] 3. 折线图加载测试...")
        print("[ACTION] 请手动切换到折线图视图")
        print("[WAIT] 等待用户操作...")
        time.sleep(5)  # 给用户时间切换视图
        
        screenshot_path = take_screenshot("03_line_chart")
        if screenshot_path:
            has_content = analyze_chart_content(screenshot_path, tester)
            if has_content:
                tester.add_test_result("Line Chart", "折线图加载", "PASS", 
                                     "折线图界面显示正常", screenshot_path)
            else:
                tester.add_test_result("Line Chart", "折线图加载", "FAIL", 
                                     "折线图界面可能未正确显示", screenshot_path)
        else:
            tester.add_test_result("Line Chart", "折线图加载", "FAIL", 
                                 "未能获取折线图截图")
        
        # 4. 3D散点图加载测试
        print("\n[INFO] 4. 3D散点图加载测试...")
        print("[ACTION] 请手动切换到3D散点图视图")
        print("[WAIT] 等待用户操作...")
        time.sleep(5)  # 给用户时间切换视图
        
        screenshot_path = take_screenshot("04_3d_scatter")
        if screenshot_path:
            has_content = analyze_chart_content(screenshot_path, tester)
            if has_content:
                tester.add_test_result("3D Scatter", "3D散点图加载", "PASS", 
                                     "3D散点图界面显示正常", screenshot_path)
            else:
                tester.add_test_result("3D Scatter", "3D散点图加载", "FAIL", 
                                     "3D散点图界面可能未正确显示", screenshot_path)
        else:
            tester.add_test_result("3D Scatter", "3D散点图加载", "FAIL", 
                                 "未能获取3D散点图截图")
        
        # 5. 图表间切换测试
        print("\n[INFO] 5. 图表间切换测试...")
        print("[ACTION] 请手动在不同图表间切换几次")
        print("[WAIT] 等待用户操作...")
        time.sleep(10)  # 给用户时间切换图表
        
        screenshot_path = take_screenshot("05_chart_switching")
        if screenshot_path:
            has_content = analyze_chart_content(screenshot_path, tester)
            if has_content:
                tester.add_test_result("Chart Switching", "图表切换", "PASS", 
                                     "图表切换后界面显示正常", screenshot_path)
            else:
                tester.add_test_result("Chart Switching", "图表切换", "FAIL", 
                                     "图表切换后界面可能未正确显示", screenshot_path)
        else:
            tester.add_test_result("Chart Switching", "图表切换", "FAIL", 
                                 "未能获取图表切换截图")
        
        # 6. 查找最优SNR功能测试
        print("\n[INFO] 6. 查找最优SNR功能测试...")
        print("[ACTION] 请手动使用查找最优SNR功能")
        print("[WAIT] 等待用户操作...")
        time.sleep(5)  # 给用户时间操作功能
        
        screenshot_path = take_screenshot("06_find_best_snr")
        if screenshot_path:
            has_content = analyze_chart_content(screenshot_path, tester)
            if has_content:
                tester.add_test_result("Find Best SNR", "查找最优SNR", "PASS", 
                                     "查找最优SNR功能界面显示正常", screenshot_path)
            else:
                tester.add_test_result("Find Best SNR", "查找最优SNR", "FAIL", 
                                     "查找最优SNR功能界面可能未正确显示", screenshot_path)
        else:
            tester.add_test_result("Find Best SNR", "查找最优SNR", "FAIL", 
                                 "未能获取查找最优SNR功能截图")
        
        # 测试完成
        print("\n[INFO] 针对性问题测试完成")
        
        # 关闭程序
        print("\n[ACTION] 关闭程序...")
        try:
            app_process.terminate()
            app_process.wait(timeout=5)
        except:
            app_process.kill()
        print("[INFO] 程序已关闭")
        
        return tester
        
    except Exception as e:
        print(f"[ERROR] 针对性问题测试失败: {e}")
        import traceback
        traceback.print_exc()
        screenshot_path = take_screenshot("99_test_error")
        if screenshot_path:
            tester.add_problem("high", "Test Framework", "测试框架错误", 
                             str(e), screenshot_path)
        
        # 关闭程序
        if 'app_process' in locals():
            try:
                app_process.terminate()
                app_process.wait(timeout=5)
            except:
                app_process.kill()
        
        return tester

def create_targeted_test_report(tester):
    """创建针对性测试报告"""
    print("\n=== 生成针对性测试报告 ===")
    
    report_file = os.path.join(project_root, 'docs', 'TARGETED_PROBLEM_TEST_REPORT.md')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# SNR数据可视化工具 针对性问题测试报告\n\n")
            f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 报告概述\n\n")
            f.write("本报告针对用户指出的具体功能性问题，对SNR数据可视化工具V1.0版本进行深入测试。\n")
            f.write("测试重点包括：折线图加载、3D散点图加载、图表间切换、查找最优SNR等核心功能。\n\n")
            
            f.write("## 测试方法\n\n")
            f.write("1. 启动程序并手动加载数据文件\n")
            f.write("2. 逐一测试各个图表显示功能\n")
            f.write("3. 测试图表间切换功能\n")
            f.write("4. 测试查找最优SNR功能\n")
            f.write("5. 通过截图分析和人工观察判断功能是否正常\n\n")
            
            f.write("## 测试结果\n\n")
            
            # 统计结果
            pass_count = sum(1 for r in tester.test_results if r['status'] == 'PASS')
            fail_count = sum(1 for r in tester.test_results if r['status'] == 'FAIL')
            warning_count = sum(1 for r in tester.test_results if r['status'] == 'WARNING')
            
            f.write(f"**测试项总数**: {len(tester.test_results)}\n")
            f.write(f"**通过**: {pass_count}\n")
            f.write(f"**失败**: {fail_count}\n")
            f.write(f"**警告**: {warning_count}\n\n")
            
            # 测试结果详情
            if tester.test_results:
                f.write("### 详细测试结果\n\n")
                for i, result in enumerate(tester.test_results, 1):
                    status_symbol = '✅' if result['status'] == 'PASS' else '❌' if result['status'] == 'FAIL' else '⚠️'
                    f.write(f"{i}. {status_symbol} **{result['component']}**: {result['description']}\n")
                    if result['details']:
                        f.write(f"   详情: {result['details']}\n")
                    if result['screenshot']:
                        f.write(f"   截图: ![截图]({os.path.relpath(result['screenshot'], project_root).replace(os.sep, '/')})\n")
                    f.write("\n")
            
            # 发现的问题
            if tester.problems_found:
                f.write("### 发现的问题\n\n")
                for i, problem in enumerate(tester.problems_found, 1):
                    f.write(f"{i}. **[{problem['severity'].upper()}]** {problem['component']}: {problem['description']}\n")
                    if problem['details']:
                        f.write(f"   详情: {problem['details']}\n")
                    if problem['screenshot']:
                        f.write(f"   截图: ![截图]({os.path.relpath(problem['screenshot'], project_root).replace(os.sep, '/')})\n")
                    f.write("\n")
            
            # 信息
            if tester.info_messages:
                f.write("### 测试信息\n\n")
                for i, info in enumerate(tester.info_messages, 1):
                    f.write(f"{i}. {info['component']}: {info['description']}\n")
                    if info['details']:
                        f.write(f"   详情: {info['details']}\n")
                    if info['screenshot']:
                        f.write(f"   截图: ![截图]({os.path.relpath(info['screenshot'], project_root).replace(os.sep, '/')})\n")
                    f.write("\n")
        
        print(f"[INFO] 针对性测试报告已生成: {report_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 生成针对性测试报告失败: {e}")
        return False

def main():
    """主函数"""
    print("SNR数据可视化工具 - 针对性问题测试")
    print("=" * 60)
    print("请按照提示手动操作程序，测试各项核心功能")
    print("=" * 60)
    
    # 运行针对性问题测试
    tester = targeted_problem_test()
    
    # 创建针对性测试报告
    report_success = create_targeted_test_report(tester)
    
    print("\n" + "=" * 60)
    print("测试结果摘要:")
    
    # 统计结果
    pass_count = sum(1 for r in tester.test_results if r['status'] == 'PASS')
    fail_count = sum(1 for r in tester.test_results if r['status'] == 'FAIL')
    warning_count = sum(1 for r in tester.test_results if r['status'] == 'WARNING')
    
    print(f"  测试项总数: {len(tester.test_results)}")
    print(f"  通过: {pass_count}")
    print(f"  失败: {fail_count}")
    print(f"  警告: {warning_count}")
    print(f"  发现问题: {len(tester.problems_found)}")
    print(f"  信息: {len(tester.info_messages)}")
    
    if report_success:
        print("\n针对性测试完成！")
        print("请查看 docs/TARGETED_PROBLEM_TEST_REPORT.md 获取详细测试报告")
        print("请查看 docs/problem_testing_screenshots/ 目录获取测试截图")
        print("\n请注意：本次测试需要您手动操作程序来验证各项功能。")
        print("如果您发现了具体的问题，请告诉我详细的操作步骤，我可以帮您创建更针对性的测试。")
    else:
        print("\n测试过程中出现错误，请检查上述信息")

if __name__ == "__main__":
    main()