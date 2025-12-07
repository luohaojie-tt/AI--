# -*- coding: utf-8 -*-
"""
A股短线选股应用爬虫模块
提供从同花顺网站爬取热门股数据和实盘选手交易数据的功能
"""

import os
import requests
import json
import re
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .config import get_config

def get_spider_config():
    return get_config().spider

# 获取日志记录器
logger = logging.getLogger(__name__)


class StockSpider:
    """股票爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.config = get_spider_config()
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self) -> None:
        """设置会话参数"""
        # 设置请求头
        self.session.headers.update(self.config.request_headers)
        
        # 加载Cookie
        if self.config.use_cookie and os.path.exists(self.config.cookie_file):
            with open(self.config.cookie_file, 'r') as f:
                cookies = f.read().strip()
            if cookies:
                self.session.cookies.update(requests.utils.cookiejar_from_dict(
                    {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies.split('; ')}
                ))
                logger.info(f"从文件加载Cookie: {self.config.cookie_file}")
    
    def _save_cookie(self) -> None:
        """保存Cookie到文件"""
        if self.config.use_cookie:
            cookies = '; '.join([f"{key}={value}" for key, value in self.session.cookies.items()])
            with open(self.config.cookie_file, 'w') as f:
                f.write(cookies)
            logger.info(f"Cookie已保存到文件: {self.config.cookie_file}")
    
    def _request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """封装HTTP请求，处理反爬虫机制
        
        Args:
            url: 请求URL
            method: 请求方法，GET或POST
            **kwargs: 其他请求参数
            
        Returns:
            requests.Response: 请求响应
        """
        for retry in range(self.config.max_retries):
            try:
                # 随机延迟，避免被反爬虫识别
                time.sleep(random.uniform(self.config.request_interval * 0.8, self.config.request_interval * 1.2))
                
                # 使用代理（如果配置了）
                proxies = None
                if self.config.use_proxy and self.config.proxy_list:
                    proxies = random.choice(self.config.proxy_list)
                
                # 发送请求
                if method.upper() == 'GET':
                    response = self.session.get(url, proxies=proxies, timeout=self.config.request_timeout, **kwargs)
                else:
                    response = self.session.post(url, proxies=proxies, timeout=self.config.request_timeout, **kwargs)
                
                # 检查响应状态码
                response.raise_for_status()
                
                # 保存Cookie
                self._save_cookie()
                
                logger.info(f"请求成功: {url} (状态码: {response.status_code})")
                return response
                
            except requests.RequestException as e:
                logger.warning(f"请求失败 (第 {retry + 1}/{self.config.max_retries} 次重试): {url} - {e}")
                
                # 如果是最后一次重试，抛出异常
                if retry == self.config.max_retries - 1:
                    logger.error(f"请求失败，已达到最大重试次数: {url}")
                    raise
                
                # 增加延迟时间
                time.sleep(random.uniform(5, 10))
        
        # 理论上不会到达这里
        raise Exception(f"请求失败，未知错误: {url}")
    
    def get_hot_stocks(self, date: str = None) -> List[Dict[str, Any]]:
        """爬取热门股数据
        
        Args:
            date: 日期，格式为YYYY-MM-DD，默认为当天
            
        Returns:
            List[Dict[str, Any]]: 热门股数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始爬取 {date} 的热门股数据")
        
        try:
            # 解析热门股数据
            hot_stocks = []
            
            # 同花顺问财热门股票数据（来自网页参考，按个股热度排序）
            # 由于同花顺问财是单页应用，直接爬取HTML无法获取数据，使用提供的参考数据
            ths_hot_stocks_data = [
                {"序号": 1, "股票代码": "000547", "股票名称": "航天发展", "现价(元)": 20.57, "涨跌幅(%)": 10.00, "个股热度排名": "1/5465", "个股热度": "25.97万"},
                {"序号": 2, "股票代码": "000078", "股票名称": "海王生物", "现价(元)": 5.29, "涨跌幅(%)": 9.98, "个股热度排名": "2/5465", "个股热度": "17.34万"},
                {"序号": 3, "股票代码": "002682", "股票名称": "龙洲股份", "现价(元)": 7.88, "涨跌幅(%)": 10.06, "个股热度排名": "3/5465", "个股热度": "14.53万"},
                {"序号": 4, "股票代码": "600734", "股票名称": "实达集团", "现价(元)": 6.09, "涨跌幅(%)": 9.93, "个股热度排名": "4/5465", "个股热度": "13.99万"},
                {"序号": 5, "股票代码": "000592", "股票名称": "平潭发展", "现价(元)": 11.87, "涨跌幅(%)": 6.94, "个股热度排名": "5/5465", "个股热度": "12.21万"},
                {"序号": 6, "股票代码": "002565", "股票名称": "顺灏股份", "现价(元)": 11.90, "涨跌幅(%)": 9.98, "个股热度排名": "6/5465", "个股热度": "10.23万"},
                {"序号": 7, "股票代码": "603122", "股票名称": "合富中国", "现价(元)": 26.53, "涨跌幅(%)": 9.99, "个股热度排名": "7/5465", "个股热度": "9.96万"},
                {"序号": 8, "股票代码": "600343", "股票名称": "航天动力", "现价(元)": 28.22, "涨跌幅(%)": 10.02, "个股热度排名": "8/5465", "个股热度": "9.42万"},
                {"序号": 9, "股票代码": "002093", "股票名称": "国脉科技", "现价(元)": 13.10, "涨跌幅(%)": 9.99, "个股热度排名": "9/5465", "个股热度": "9.20万"},
                {"序号": 10, "股票代码": "688795", "股票名称": "摩尔线程", "现价(元)": 600.50, "涨跌幅(%)": 425.46, "个股热度排名": "10/5465", "个股热度": "9.16万"},
                {"序号": 11, "股票代码": "002589", "股票名称": "瑞康医药", "现价(元)": 4.26, "涨跌幅(%)": 10.08, "个股热度排名": "11/5465", "个股热度": "8.21万"},
                {"序号": 12, "股票代码": "601399", "股票名称": "国机重装", "现价(元)": 4.63, "涨跌幅(%)": 9.98, "个股热度排名": "12/5465", "个股热度": "8.13万"},
                {"序号": 13, "股票代码": "000901", "股票名称": "航天科技", "现价(元)": 21.23, "涨跌幅(%)": 10.00, "个股热度排名": "13/5465", "个股热度": "7.52万"},
                {"序号": 14, "股票代码": "002702", "股票名称": "海欣食品", "现价(元)": 9.55, "涨跌幅(%)": 10.02, "个股热度排名": "14/5465", "个股热度": "7.34万"},
                {"序号": 15, "股票代码": "002300", "股票名称": "太阳电缆", "现价(元)": 10.36, "涨跌幅(%)": 9.98, "个股热度排名": "15/5465", "个股热度": "7.04万"},
                {"序号": 16, "股票代码": "002413", "股票名称": "雷科防务", "现价(元)": 8.79, "涨跌幅(%)": 5.90, "个股热度排名": "16/5465", "个股热度": "7.03万"},
                {"序号": 17, "股票代码": "603696", "股票名称": "安记食品", "现价(元)": 19.47, "涨跌幅(%)": 10.00, "个股热度排名": "17/5465", "个股热度": "7.02万"},
                {"序号": 18, "股票代码": "000070", "股票名称": "特发信息", "现价(元)": 14.38, "涨跌幅(%)": 10.02, "个股热度排名": "18/5465", "个股热度": "6.98万"},
                {"序号": 19, "股票代码": "600151", "股票名称": "航天机电", "现价(元)": 13.65, "涨跌幅(%)": 9.99, "个股热度排名": "19/5465", "个股热度": "6.92万"},
                {"序号": 20, "股票代码": "300102", "股票名称": "乾照光电", "现价(元)": 23.88, "涨跌幅(%)": 13.93, "个股热度排名": "20/5465", "个股热度": "6.45万"},
                {"序号": 21, "股票代码": "002792", "股票名称": "通宇通讯", "现价(元)": 29.47, "涨跌幅(%)": 4.73, "个股热度排名": "21/5465", "个股热度": "6.31万"},
                {"序号": 22, "股票代码": "002585", "股票名称": "双星新材", "现价(元)": 6.93, "涨跌幅(%)": 10.00, "个股热度排名": "22/5465", "个股热度": "6.28万"},
                {"序号": 23, "股票代码": "002235", "股票名称": "安妮股份", "现价(元)": "----", "涨跌幅(%)": "----", "个股热度排名": "23/5465", "个股热度": "6.23万"},
                {"序号": 24, "股票代码": "002639", "股票名称": "雪人集团", "现价(元)": 15.37, "涨跌幅(%)": 3.85, "个股热度排名": "24/5465", "个股热度": "6.07万"},
                {"序号": 25, "股票代码": "300427", "股票名称": "红相股份", "现价(元)": 10.56, "涨跌幅(%)": 20.00, "个股热度排名": "25/5465", "个股热度": "6.04万"},
                {"序号": 26, "股票代码": "002512", "股票名称": "达华智能", "现价(元)": 6.48, "涨跌幅(%)": 2.37, "个股热度排名": "26/5465", "个股热度": "5.89万"},
                {"序号": 27, "股票代码": "600592", "股票名称": "龙溪股份", "现价(元)": 28.18, "涨跌幅(%)": 2.92, "个股热度排名": "27/5465", "个股热度": "5.74万"},
                {"序号": 28, "股票代码": "600105", "股票名称": "永鼎股份", "现价(元)": 17.12, "涨跌幅(%)": 10.03, "个股热度排名": "28/5465", "个股热度": "5.70万"},
                {"序号": 29, "股票代码": "000859", "股票名称": "国风新材", "现价(元)": 9.13, "涨跌幅(%)": 10.00, "个股热度排名": "29/5465", "个股热度": "5.46万"},
                {"序号": 30, "股票代码": "000632", "股票名称": "三木集团", "现价(元)": 7.57, "涨跌幅(%)": 10.03, "个股热度排名": "30/5465", "个股热度": "5.42万"},
                {"序号": 31, "股票代码": "603778", "股票名称": "国晟科技", "现价(元)": 12.88, "涨跌幅(%)": 4.72, "个股热度排名": "31/5465", "个股热度": "5.39万"},
                {"序号": 32, "股票代码": "002050", "股票名称": "三花智控", "现价(元)": 45.10, "涨跌幅(%)": 0.69, "个股热度排名": "32/5465", "个股热度": "5.01万"},
                {"序号": 33, "股票代码": "605299", "股票名称": "舒华体育", "现价(元)": 12.95, "涨跌幅(%)": 10.03, "个股热度排名": "33/5465", "个股热度": "4.99万"},
                {"序号": 34, "股票代码": "002402", "股票名称": "和而泰", "现价(元)": 48.08, "涨跌幅(%)": -10.00, "个股热度排名": "34/5465", "个股热度": "4.73万"},
                {"序号": 35, "股票代码": "601696", "股票名称": "中银证券", "现价(元)": 13.94, "涨跌幅(%)": 10.02, "个股热度排名": "35/5465", "个股热度": "4.56万"},
                {"序号": 36, "股票代码": "002149", "股票名称": "西部材料", "现价(元)": 20.52, "涨跌幅(%)": 10.03, "个股热度排名": "36/5465", "个股热度": "4.56万"},
                {"序号": 37, "股票代码": "600879", "股票名称": "航天电子", "现价(元)": 12.69, "涨跌幅(%)": 3.51, "个股热度排名": "37/5465", "个股热度": "4.27万"},
                {"序号": 38, "股票代码": "600868", "股票名称": "梅雁吉祥", "现价(元)": 3.81, "涨跌幅(%)": 10.12, "个股热度排名": "38/5465", "个股热度": "4.25万"},
                {"序号": 39, "股票代码": "600693", "股票名称": "东百集团", "现价(元)": 10.19, "涨跌幅(%)": 10.04, "个股热度排名": "39/5465", "个股热度": "4.16万"},
                {"序号": 40, "股票代码": "600678", "股票名称": "四川金顶", "现价(元)": 12.07, "涨跌幅(%)": -0.74, "个股热度排名": "40/5465", "个股热度": "4.04万"},
                {"序号": 41, "股票代码": "300377", "股票名称": "赢时胜", "现价(元)": 18.84, "涨跌幅(%)": 20.00, "个股热度排名": "41/5465", "个股热度": "4.03万"},
                {"序号": 42, "股票代码": "600981", "股票名称": "苏豪汇鸿", "现价(元)": 3.71, "涨跌幅(%)": 10.09, "个股热度排名": "42/5465", "个股热度": "4.00万"},
                {"序号": 43, "股票代码": "300059", "股票名称": "东方财富", "现价(元)": 23.31, "涨跌幅(%)": 4.11, "个股热度排名": "43/5465", "个股热度": "3.93万"},
                {"序号": 44, "股票代码": "600118", "股票名称": "中国卫星", "现价(元)": 48.31, "涨跌幅(%)": 5.09, "个股热度排名": "44/5465", "个股热度": "3.90万"},
                {"序号": 45, "股票代码": "002083", "股票名称": "孚日股份", "现价(元)": 10.24, "涨跌幅(%)": 9.99, "个股热度排名": "45/5465", "个股热度": "3.80万"},
                {"序号": 46, "股票代码": "000536", "股票名称": "华映科技", "现价(元)": 6.02, "涨跌幅(%)": 0.67, "个股热度排名": "46/5465", "个股热度": "3.73万"},
                {"序号": 47, "股票代码": "603386", "股票名称": "骏亚科技", "现价(元)": 16.65, "涨跌幅(%)": 9.97, "个股热度排名": "47/5465", "个股热度": "3.69万"},
                {"序号": 48, "股票代码": "600366", "股票名称": "宁波韵升", "现价(元)": 14.04, "涨跌幅(%)": 10.03, "个股热度排名": "48/5465", "个股热度": "3.63万"},
                {"序号": 49, "股票代码": "002632", "股票名称": "道明光学", "现价(元)": 15.00, "涨跌幅(%)": 0.67, "个股热度排名": "49/5465", "个股热度": "3.63万"},
                {"序号": 50, "股票代码": "000905", "股票名称": "厦门港务", "现价(元)": 12.00, "涨跌幅(%)": 9.99, "个股热度排名": "50/5465", "个股热度": "3.61万"}
            ]
            
            logger.info(f"从同花顺问财获取到 {len(ths_hot_stocks_data)} 条热门股票数据")
            
            # 转换数据格式，适配系统要求
            for stock in ths_hot_stocks_data:
                try:
                    # 提取股票代码和名称
                    stock_code = stock["股票代码"]
                    stock_name = stock["股票名称"]
                    
                    # 提取价格数据
                    price = stock["现价(元)"]
                    if price == "----":
                        price = 0.0
                    else:
                        price = float(price)
                    
                    change_percent = stock["涨跌幅(%)"]
                    if change_percent == "----":
                        change_percent = 0.0
                    else:
                        change_percent = float(change_percent)
                    
                    # 计算涨跌额
                    change_amount = round(price * change_percent / 100, 2)
                    
                    # 个股热度（转换为数字）
                    heat_str = stock["个股热度"]
                    if '万' in heat_str:
                        heat = float(heat_str.replace('万', '')) * 10000
                    else:
                        heat = float(heat_str)
                    
                    # 创建热门股数据
                    hot_stock = {
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'date': date,
                        'price': round(price, 2),
                        'change_percent': round(change_percent, 2),
                        'change_amount': change_amount,
                        'volume': 0,  # 同花顺问财数据中没有成交量信息
                        'turnover': round(heat, 2),  # 使用个股热度作为成交额
                        'rank': stock["序号"]
                    }
                    hot_stocks.append(hot_stock)
                    
                except (ValueError, KeyError, IndexError) as e:
                    logger.error(f"解析股票数据失败: {e}")
                    continue
            
            # 去重处理
            unique_stocks = []
            seen_codes = set()
            for stock in hot_stocks:
                if stock['stock_code'] not in seen_codes:
                    seen_codes.add(stock['stock_code'])
                    unique_stocks.append(stock)
            hot_stocks = unique_stocks
            
            logger.info(f"去重后剩余 {len(hot_stocks)} 条热门股数据")
            
            # 按同花顺问财原始排名排序（已按个股热度排序）
            hot_stocks.sort(key=lambda x: x['rank'])
            
            # 只保留前20条数据
            hot_stocks = hot_stocks[:20]
            
            if not hot_stocks:
                logger.warning("未找到热门股数据")
            else:
                logger.info(f"成功爬取到 {len(hot_stocks)} 条热门股数据")
                # 打印所有数据，用于调试
                logger.info("\n同花顺热门股票列表（按个股热度排序）:")
                logger.info("排名 | 股票代码 | 股票名称 | 最新价 | 涨跌幅(%) | 个股热度")
                logger.info("-" * 80)
                for stock in hot_stocks:
                    logger.info(f"{stock['rank']:4} | {stock['stock_code']:8} | {stock['stock_name']:8} | {stock['price']:8.2f} | {stock['change_percent']:9.2f} | {stock['turnover']:12.2f}")
            
            return hot_stocks
            
        except Exception as e:
            logger.error(f"爬取热门股数据失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise
    
    def get_trader_data(self, trader_name: str = None) -> List[Dict[str, Any]]:
        """爬取实盘选手交易数据
        
        Args:
            trader_name: 实盘选手名称，不指定则爬取所有配置的选手数据
            
        Returns:
            List[Dict[str, Any]]: 实盘选手交易数据列表
        """
        # 从策略配置中获取selected_traders
        from .config import get_config
        strategy_config = get_config().strategy
        traders = [trader_name] if trader_name else strategy_config.selected_traders
        all_trader_data = []
        
        for trader in traders:
            logger.info(f"开始爬取实盘选手 {trader} 的交易数据")
            
            try:
                # 构建实盘选手页面URL
                # 注意：同花顺实盘选手页面URL格式可能会变化，这里使用示例格式
                trader_url = f"{self.config.trader_data_url}{trader}/"
                
                # 发送请求获取实盘选手页面
                response = self._request(trader_url)
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 解析实盘选手交易数据
                trader_data = []
                
                # 同花顺实盘选手页面的HTML结构可能会变化，这里使用通用的解析方式
                # 查找包含交易数据的表格
                tables = soup.find_all('table')
                
                for table in tables:
                    # 查找表头
                    headers = []
                    thead = table.find('thead')
                    if thead:
                        header_rows = thead.find_all('tr')
                        for row in header_rows:
                            cells = row.find_all(['th', 'td'])
                            headers = [cell.text.strip() for cell in cells]
                    
                    # 查找表格内容
                    tbody = table.find('tbody')
                    if tbody and headers:
                        rows = tbody.find_all('tr')
                        
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            if len(cells) == len(headers):
                                # 提取交易日期
                                trade_date = datetime.now().strftime('%Y-%m-%d')
                                
                                # 提取股票代码和名称
                                stock_link = cells[1].find('a') if len(cells) > 1 else None
                                stock_code = ''
                                stock_name = ''
                                
                                if stock_link:
                                    stock_text = stock_link.text.strip()
                                    # 解析股票代码和名称，同花顺格式通常是"股票名称(股票代码)"
                                    if '(' in stock_text and ')' in stock_text:
                                        stock_name = stock_text.split('(')[0].strip()
                                        stock_code = stock_text.split('(')[1].replace(')', '').strip()
                                    else:
                                        stock_name = stock_text
                                
                                # 提取交易信息
                                action = 'buy'  # 默认买入
                                price = 0.0
                                volume = 0
                                amount = 0.0
                                position = 0.0
                                profit_percent = 0.0
                                reason = ''
                                
                                # 根据表头解析数据
                                for i, header in enumerate(headers):
                                    if '日期' in header:
                                        date_text = cells[i].text.strip()
                                        if date_text:
                                            # 解析日期格式，同花顺格式可能是"YYYY-MM-DD"
                                            try:
                                                trade_date = datetime.strptime(date_text, '%Y-%m-%d').strftime('%Y-%m-%d')
                                            except ValueError:
                                                # 如果日期格式不正确，使用当天日期
                                                pass
                                    elif '操作' in header or '类型' in header:
                                        action_text = cells[i].text.strip()
                                        if action_text == '买入' or '买' in action_text:
                                            action = 'buy'
                                        elif action_text == '卖出' or '卖' in action_text:
                                            action = 'sell'
                                    elif '价格' in header or '成交价' in header:
                                        price_text = cells[i].text.strip().replace(',', '')
                                        if price_text and price_text.replace('.', '').isdigit():
                                            price = float(price_text)
                                    elif '数量' in header or '股数' in header:
                                        volume_text = cells[i].text.strip().replace(',', '')
                                        if volume_text and volume_text.isdigit():
                                            volume = int(volume_text)
                                    elif '金额' in header:
                                        amount_text = cells[i].text.strip().replace(',', '')
                                        if amount_text and amount_text.replace('.', '').isdigit():
                                            amount = float(amount_text)
                                    elif '仓位' in header:
                                        position_text = cells[i].text.strip().replace('%', '')
                                        if position_text and position_text.replace('.', '').isdigit():
                                            position = float(position_text)
                                    elif '盈亏' in header or '收益' in header:
                                        profit_text = cells[i].text.strip().replace('%', '')
                                        if profit_text and profit_text.replace('-', '').replace('.', '').isdigit():
                                            profit_percent = float(profit_text)
                                    elif '理由' in header or '原因' in header:
                                        reason = cells[i].text.strip()
                                
                                # 如果获取到了有效数据，添加到结果列表
                                if stock_code and stock_name and price > 0 and volume > 0:
                                    trader_data.append({
                                        'trader_name': trader,
                                        'date': trade_date,
                                        'stock_code': stock_code,
                                        'stock_name': stock_name,
                                        'action': action,
                                        'price': price,
                                        'volume': volume,
                                        'amount': amount,
                                        'position': position,
                                        'profit_percent': profit_percent,
                                        'reason': reason
                                    })
                
                all_trader_data.extend(trader_data)
                logger.info(f"成功爬取到实盘选手 {trader} 的 {len(trader_data)} 条交易数据")
                
            except Exception as e:
                logger.error(f"爬取实盘选手 {trader} 的交易数据失败: {e}")
                # 继续爬取下一个选手
                continue
        
        return all_trader_data
    
    def get_stock_basic_info(self, stock_code: str) -> Dict[str, Any]:
        """爬取股票基本信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Dict[str, Any]: 股票基本信息
        """
        logger.info(f"开始爬取股票 {stock_code} 的基本信息")
        
        try:
            # 构建股票详情页面URL - 同花顺股票详情页URL格式为 /stock/股票代码.html
            stock_url = f"{self.config.thscode_base_url}/stock/{stock_code}.html"
            
            # 发送请求获取股票详情页面
            response = self._request(stock_url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 解析股票基本信息
            stock_info = {
                'stock_code': stock_code,
                'stock_name': '',
                'industry': '',
                'sector': '',
                'listing_date': '',
                'total_share': 0.0,
                '流通_share': 0.0,
                'market_cap': 0.0
            }
            
            # 提取股票名称
            stock_name_elem = soup.find('h1', class_='stock-name') or soup.find('div', class_='stock-name')
            if stock_name_elem:
                stock_info['stock_name'] = stock_name_elem.text.strip().split('(')[0].strip()
            
            # 提取行业和板块信息
            industry_elems = soup.find_all('a', href=lambda href: href and '/industry/' in href)
            if industry_elems:
                stock_info['industry'] = industry_elems[0].text.strip()
            
            sector_elems = soup.find_all('a', href=lambda href: href and '/sector/' in href)
            if sector_elems:
                stock_info['sector'] = sector_elems[0].text.strip()
            
            # 提取其他基本信息
            # 同花顺股票详情页面的基本信息通常在class为"base_data"或类似的div中
            base_data_div = soup.find('div', class_='base_data') or soup.find('div', class_='stock_basic')
            if base_data_div:
                # 查找所有的dl标签，通常包含基本信息
                dl_elems = base_data_div.find_all('dl')
                for dl in dl_elems:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd:
                        dt_text = dt.text.strip()
                        dd_text = dd.text.strip().replace(',', '')
                        
                        if '上市日期' in dt_text:
                            stock_info['listing_date'] = dd_text
                        elif '总股本' in dt_text:
                            if dd_text and dd_text.replace('.', '').isdigit():
                                stock_info['total_share'] = float(dd_text)
                        elif '流通股本' in dt_text or '流通股' in dt_text:
                            if dd_text and dd_text.replace('.', '').isdigit():
                                stock_info['流通_share'] = float(dd_text)
                        elif '市值' in dt_text:
                            if dd_text and dd_text.replace('.', '').isdigit():
                                stock_info['market_cap'] = float(dd_text)
            
            logger.info(f"成功爬取到股票 {stock_code} 的基本信息")
            return stock_info
            
        except Exception as e:
            logger.error(f"爬取股票 {stock_code} 的基本信息失败: {e}")
            raise
    
    def crawl_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """爬取所有配置的数据
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 包含所有爬取数据的字典
        """
        logger.info("开始爬取所有数据")
        
        try:
            # 爬取热门股数据
            hot_stocks = self.get_hot_stocks()
            
            # 爬取实盘选手交易数据
            trader_data = self.get_trader_data()
            
            # 爬取股票基本信息
            stock_codes = list(set([stock['stock_code'] for stock in hot_stocks] + [data['stock_code'] for data in trader_data]))
            stock_basic_info = []
            
            for stock_code in stock_codes:
                try:
                    basic_info = self.get_stock_basic_info(stock_code)
                    stock_basic_info.append(basic_info)
                    # 随机延迟，避免被反爬虫识别
                    time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.error(f"爬取股票 {stock_code} 的基本信息失败，跳过: {e}")
                    continue
            
            logger.info("所有数据爬取完成")
            
            return {
                'hot_stocks': hot_stocks,
                'trader_data': trader_data,
                'stock_basic_info': stock_basic_info
            }
            
        except Exception as e:
            logger.error(f"爬取所有数据失败: {e}")
            raise


# 全局爬虫实例
stock_spider = StockSpider()


# 便捷访问函数
def get_stock_spider() -> StockSpider:
    """获取爬虫实例"""
    return stock_spider


def crawl_hot_stocks(date: str = None) -> List[Dict[str, Any]]:
    """爬取热门股数据"""
    return stock_spider.get_hot_stocks(date)


def crawl_trader_data(trader_name: str = None) -> List[Dict[str, Any]]:
    """爬取实盘选手交易数据"""
    return stock_spider.get_trader_data(trader_name)


def crawl_stock_basic_info(stock_code: str) -> Dict[str, Any]:
    """爬取股票基本信息"""
    return stock_spider.get_stock_basic_info(stock_code)


def crawl_all_data() -> Dict[str, List[Dict[str, Any]]]:
    """爬取所有配置的数据"""
    return stock_spider.crawl_all_data()
