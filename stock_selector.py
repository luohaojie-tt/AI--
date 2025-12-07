# -*- coding: utf-8 -*-
"""
A股短线选股应用主程序
用于启动数据获取、选股策略执行等功能
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from core.config import config_manager
from core.spider import crawl_all_data, crawl_hot_stocks, crawl_trader_data, crawl_stock_basic_info
from core.data_manager import (
    insert_stock_basic_data,
    insert_hot_stocks_data,
    insert_trader_data_data,
    get_hot_stocks_data,
    get_trader_data_data
)

# 获取日志记录器
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='A股短线选股应用')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', required=True, help='命令名称')
    
    # 数据爬取命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取数据')
    crawl_parser.add_argument('--all', action='store_true', help='爬取所有数据')
    crawl_parser.add_argument('--hot', action='store_true', help='仅爬取热门股数据')
    crawl_parser.add_argument('--trader', type=str, help='爬取指定实盘选手数据')
    crawl_parser.add_argument('--basic', type=str, help='爬取指定股票基本信息')
    crawl_parser.add_argument('--date', type=str, help='指定爬取日期，格式：YYYY-MM-DD')
    
    # 数据查询命令
    query_parser = subparsers.add_parser('query', help='查询数据')
    query_parser.add_argument('--hot', action='store_true', help='查询热门股数据')
    query_parser.add_argument('--trader', type=str, help='查询指定实盘选手数据')
    query_parser.add_argument('--date', type=str, help='指定查询日期，格式：YYYY-MM-DD')
    query_parser.add_argument('--limit', type=int, default=100, help='查询结果数量限制')
    query_parser.add_argument('--detailed', action='store_true', help='显示详细数据内容')
    
    # 系统管理命令
    manage_parser = subparsers.add_parser('manage', help='系统管理')
    manage_parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    manage_parser.add_argument('--clear-old', type=int, help='清理指定天数前的旧数据')
    manage_parser.add_argument('--show-config', action='store_true', help='显示当前配置')
    
    return parser.parse_args()


def crawl_all() -> None:
    """爬取所有数据"""
    logger.info("开始爬取所有数据...")
    
    try:
        # 爬取所有数据
        data = crawl_all_data()
        
        # 插入数据到数据库
        if data.get('stock_basic_info'):
            insert_stock_basic_data(data['stock_basic_info'])
        
        if data.get('hot_stocks'):
            insert_hot_stocks_data(data['hot_stocks'])
        
        if data.get('trader_data'):
            insert_trader_data_data(data['trader_data'])
        
        logger.info("所有数据爬取和存储完成")
        
    except Exception as e:
        logger.error(f"爬取所有数据失败: {e}")
        raise


def crawl_hot(date: str = None) -> None:
    """爬取热门股数据"""
    logger.info(f"开始爬取热门股数据...")
    
    try:
        # 爬取热门股数据
        hot_stocks = crawl_hot_stocks(date)
        
        # 插入数据到数据库
        if hot_stocks:
            insert_hot_stocks_data(hot_stocks)
            logger.info(f"热门股数据爬取和存储完成，共 {len(hot_stocks)} 条数据")
        else:
            logger.warning("未爬取到热门股数据")
            
    except Exception as e:
        logger.error(f"爬取热门股数据失败: {e}")
        raise


def crawl_trader(trader_name: str = None) -> None:
    """爬取实盘选手交易数据"""
    logger.info(f"开始爬取实盘选手交易数据...")
    
    try:
        # 爬取实盘选手交易数据
        trader_data = crawl_trader_data(trader_name)
        
        # 插入数据到数据库
        if trader_data:
            insert_trader_data_data(trader_data)
            logger.info(f"实盘选手交易数据爬取和存储完成，共 {len(trader_data)} 条数据")
        else:
            logger.warning("未爬取到实盘选手交易数据")
            
    except Exception as e:
        logger.error(f"爬取实盘选手交易数据失败: {e}")
        raise


def crawl_stock(stock_code: str) -> None:
    """爬取股票基本信息"""
    logger.info(f"开始爬取股票 {stock_code} 的基本信息...")
    
    try:
        # 爬取股票基本信息
        stock_info = crawl_stock_basic_info(stock_code)
        
        # 插入数据到数据库
        if stock_info:
            insert_stock_basic_data([stock_info])
            logger.info(f"股票 {stock_code} 的基本信息爬取和存储完成")
        else:
            logger.warning(f"未爬取到股票 {stock_code} 的基本信息")
            
    except Exception as e:
        logger.error(f"爬取股票 {stock_code} 的基本信息失败: {e}")
        raise


def query_hot(date: str = None, limit: int = 100, detailed: bool = False) -> None:
    """查询热门股数据"""
    logger.info(f"查询热门股数据...")
    
    try:
        # 查询热门股数据
        hot_stocks = get_hot_stocks_data(date, limit)
        
        # 打印结果
        if hot_stocks:
            logger.info(f"查询到 {len(hot_stocks)} 条热门股数据")
            if detailed:
                # 显示详细数据
                logger.info("详细数据:")
                for stock in hot_stocks:
                    logger.info(f"股票代码: {stock['stock_code']}")
                    logger.info(f"股票名称: {stock['stock_name']}")
                    logger.info(f"日期: {stock['date']}")
                    logger.info(f"价格: {stock['price']}")
                    logger.info(f"涨跌幅: {stock['change_percent']}%")
                    logger.info(f"涨跌额: {stock['change_amount']}")
                    logger.info(f"成交量: {stock['volume']}")
                    logger.info(f"成交额: {stock['turnover']}")
                    logger.info(f"排名: {stock['rank']}")
                    logger.info("-" * 50)
            else:
                # 显示简洁数据
                for stock in hot_stocks:
                    logger.info(f"{stock['stock_code']} {stock['stock_name']} - 价格: {stock['price']} 涨跌幅: {stock['change_percent']}% 成交量: {stock['volume']} 成交额: {stock['turnover']}")
        else:
            logger.warning("未查询到热门股数据")
            
    except Exception as e:
        logger.error(f"查询热门股数据失败: {e}")
        raise


def query_trader(trader_name: str = None, date: str = None) -> None:
    """查询实盘选手交易数据"""
    logger.info(f"查询实盘选手交易数据...")
    
    try:
        # 查询实盘选手交易数据
        trader_data = get_trader_data_data(trader_name, date)
        
        # 打印结果
        if trader_data:
            logger.info(f"查询到 {len(trader_data)} 条实盘选手交易数据")
            for data in trader_data:
                logger.info(f"{data['trader_name']} - {data['date']} {data['stock_code']} {data['stock_name']} {data['action']} - 价格: {data['price']} 数量: {data['volume']}")
        else:
            logger.warning("未查询到实盘选手交易数据")
            
    except Exception as e:
        logger.error(f"查询实盘选手交易数据失败: {e}")
        raise


def show_config() -> None:
    """显示当前配置"""
    logger.info("当前配置:")
    logger.info(f"爬虫配置: {config_manager.spider}")
    logger.info(f"数据库配置: {config_manager.database}")
    logger.info(f"选股策略配置: {config_manager.strategy}")
    logger.info(f"日志配置: {config_manager.log}")


def main() -> None:
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 根据命令执行相应操作
        if args.command == 'crawl':
            if args.all:
                crawl_all()
            elif args.hot:
                crawl_hot(args.date)
            elif args.trader:
                crawl_trader(args.trader)
            elif args.basic:
                crawl_stock(args.basic)
            else:
                logger.error("请指定爬取类型: --all, --hot, --trader, --basic")
        
        elif args.command == 'query':
            if args.hot:
                query_hot(args.date, args.limit, args.detailed)
            elif args.trader:
                query_trader(args.trader, args.date)
            else:
                logger.error("请指定查询类型: --hot, --trader")
        
        elif args.command == 'manage':
            if args.init_db:
                logger.info("数据库初始化完成")
            elif args.clear_old:
                logger.info(f"清理 {args.clear_old} 天前的旧数据")
            elif args.show_config:
                show_config()
            else:
                logger.error("请指定管理操作: --init-db, --clear-old, --show-config")
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 启动主程序
    main()
