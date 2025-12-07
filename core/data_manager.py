# -*- coding: utf-8 -*-
"""
A股短线选股应用数据管理模块
提供数据库连接、表创建、数据插入、查询等功能
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .config import get_config

def get_database_config():
    return get_config().database

# 获取日志记录器
logger = logging.getLogger(__name__)


class DataManager:
    """数据管理器类"""
    
    def __init__(self):
        """初始化数据管理器"""
        self.db_config = get_database_config()
        self.db_path = self.db_config.db_path
        self._ensure_database_exists()
        self._create_tables()
    
    def _ensure_database_exists(self) -> None:
        """确保数据库文件和目录存在"""
        # 创建数据目录
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"创建数据库目录: {db_dir}")
        
        # 确保数据库文件存在
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            conn.close()
            logger.info(f"创建数据库文件: {self.db_path}")
    
    def _create_tables(self) -> None:
        """创建数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 创建股票基本信息表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.db_config.stock_basic_table} (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT NOT NULL,
                    industry TEXT,
                    sector TEXT,
                    listing_date TEXT,
                    total_share FLOAT,
                   流通_share FLOAT,
                    market_cap FLOAT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建热门股表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.db_config.hot_stocks_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    price FLOAT NOT NULL,
                    change_percent FLOAT NOT NULL,
                    change_amount FLOAT NOT NULL,
                    volume INTEGER NOT NULL,
                    turnover FLOAT NOT NULL,
                    market_cap FLOAT,
                    pe FLOAT,
                    pb FLOAT,
                    rank INTEGER,
                    hot_degree INTEGER,
                    sector TEXT,
                    industry TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_code) REFERENCES {self.db_config.stock_basic_table}(stock_code),
                    UNIQUE(stock_code, date)
                )
            """)
            
            # 创建实盘选手数据表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.db_config.trader_data_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trader_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    action TEXT NOT NULL,  -- buy/sell
                    price FLOAT NOT NULL,
                    volume INTEGER NOT NULL,
                    amount FLOAT NOT NULL,
                    position FLOAT,
                    profit_percent FLOAT,
                    reason TEXT,
                    market_environment TEXT,
                    sector TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_code) REFERENCES {self.db_config.stock_basic_table}(stock_code),
                    UNIQUE(trader_name, date, stock_code, action)
                )
            """)
            
            conn.commit()
            logger.info("数据库表创建完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"创建数据库表失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def _connect(self) -> sqlite3.Connection:
        """建立数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def insert_stock_basic(self, stock_data: List[Dict[str, Any]]) -> int:
        """插入股票基本信息
        
        Args:
            stock_data: 股票基本信息列表，每个元素是包含股票信息的字典
            
        Returns:
            int: 插入的记录数
        """
        if not stock_data:
            return 0
        
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            inserted = 0
            for stock in stock_data:
                # 确保所有必要字段存在
                stock.setdefault('stock_code', '')
                stock.setdefault('stock_name', '')
                stock.setdefault('industry', '')
                stock.setdefault('sector', '')
                stock.setdefault('listing_date', '')
                stock.setdefault('total_share', 0.0)
                stock.setdefault('流通_share', 0.0)
                stock.setdefault('market_cap', 0.0)
                
                # 使用REPLACE INTO处理重复数据
                cursor.execute(f"""
                    REPLACE INTO {self.db_config.stock_basic_table} 
                    (stock_code, stock_name, industry, sector, listing_date, total_share, 流通_share, market_cap, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock['stock_code'],
                    stock['stock_name'],
                    stock['industry'],
                    stock['sector'],
                    stock['listing_date'],
                    stock['total_share'],
                    stock['流通_share'],
                    stock['market_cap'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                inserted += 1
            
            conn.commit()
            logger.info(f"插入了 {inserted} 条股票基本信息")
            return inserted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"插入股票基本信息失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def insert_hot_stocks(self, hot_stocks: List[Dict[str, Any]]) -> int:
        """插入热门股数据
        
        Args:
            hot_stocks: 热门股数据列表
            
        Returns:
            int: 插入的记录数
        """
        if not hot_stocks:
            return 0
        
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            inserted = 0
            for stock in hot_stocks:
                # 确保所有必要字段存在
                stock.setdefault('stock_code', '')
                stock.setdefault('stock_name', '')
                stock.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
                stock.setdefault('price', 0.0)
                stock.setdefault('change_percent', 0.0)
                stock.setdefault('change_amount', 0.0)
                stock.setdefault('volume', 0)
                stock.setdefault('turnover', 0.0)
                stock.setdefault('market_cap', 0.0)
                stock.setdefault('pe', 0.0)
                stock.setdefault('pb', 0.0)
                stock.setdefault('rank', 0)
                stock.setdefault('hot_degree', 0)
                stock.setdefault('sector', '')
                stock.setdefault('industry', '')
                
                # 使用INSERT OR IGNORE处理重复数据
                cursor.execute(f"""
                    INSERT OR IGNORE INTO {self.db_config.hot_stocks_table} 
                    (stock_code, stock_name, date, price, change_percent, change_amount, 
                     volume, turnover, market_cap, pe, pb, rank, hot_degree, sector, industry)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock['stock_code'],
                    stock['stock_name'],
                    stock['date'],
                    stock['price'],
                    stock['change_percent'],
                    stock['change_amount'],
                    stock['volume'],
                    stock['turnover'],
                    stock['market_cap'],
                    stock['pe'],
                    stock['pb'],
                    stock['rank'],
                    stock['hot_degree'],
                    stock['sector'],
                    stock['industry']
                ))
                inserted += cursor.rowcount
            
            conn.commit()
            logger.info(f"插入了 {inserted} 条热门股数据")
            return inserted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"插入热门股数据失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def insert_trader_data(self, trader_data: List[Dict[str, Any]]) -> int:
        """插入实盘选手交易数据
        
        Args:
            trader_data: 实盘选手交易数据列表
            
        Returns:
            int: 插入的记录数
        """
        if not trader_data:
            return 0
        
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            inserted = 0
            for data in trader_data:
                # 确保所有必要字段存在
                data.setdefault('trader_name', '')
                data.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
                data.setdefault('stock_code', '')
                data.setdefault('stock_name', '')
                data.setdefault('action', '')
                data.setdefault('price', 0.0)
                data.setdefault('volume', 0)
                data.setdefault('amount', 0.0)
                data.setdefault('position', 0.0)
                data.setdefault('profit_percent', 0.0)
                data.setdefault('reason', '')
                data.setdefault('market_environment', '')
                data.setdefault('sector', '')
                
                # 使用INSERT OR IGNORE处理重复数据
                cursor.execute(f"""
                    INSERT OR IGNORE INTO {self.db_config.trader_data_table} 
                    (trader_name, date, stock_code, stock_name, action, price, volume, 
                     amount, position, profit_percent, reason, market_environment, sector)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['trader_name'],
                    data['date'],
                    data['stock_code'],
                    data['stock_name'],
                    data['action'],
                    data['price'],
                    data['volume'],
                    data['amount'],
                    data['position'],
                    data['profit_percent'],
                    data['reason'],
                    data['market_environment'],
                    data['sector']
                ))
                inserted += cursor.rowcount
            
            conn.commit()
            logger.info(f"插入了 {inserted} 条实盘选手交易数据")
            return inserted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"插入实盘选手交易数据失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_hot_stocks(self, date: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取热门股数据
        
        Args:
            date: 日期，格式为YYYY-MM-DD，默认为最新日期
            limit: 返回的记录数
            
        Returns:
            List[Dict[str, Any]]: 热门股数据列表
        """
        conn = self._connect()
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        cursor = conn.cursor()
        
        try:
            if date:
                # 获取指定日期的热门股
                cursor.execute(f"""
                    SELECT * FROM {self.db_config.hot_stocks_table} 
                    WHERE date = ? 
                    ORDER BY rank LIMIT ?
                """, (date, limit))
            else:
                # 获取最新日期的热门股
                # 首先获取最新的日期
                cursor.execute(f"""
                    SELECT MAX(date) as latest_date FROM {self.db_config.hot_stocks_table}
                """)
                latest_date = cursor.fetchone()['latest_date']
                
                if latest_date:
                    # 获取最新日期的热门股，按rank排序
                    cursor.execute(f"""
                        SELECT * FROM {self.db_config.hot_stocks_table} 
                        WHERE date = ? 
                        ORDER BY rank LIMIT ?
                    """, (latest_date, limit))
                else:
                    # 如果没有数据，返回空列表
                    cursor.execute(f"""
                        SELECT * FROM {self.db_config.hot_stocks_table} 
                        ORDER BY rank LIMIT ?
                    """, (limit,))
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            logger.info(f"获取了 {len(result)} 条热门股数据")
            return result
            
        except Exception as e:
            logger.error(f"获取热门股数据失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_trader_data(self, trader_name: str = None, date: str = None, 
                       stock_code: str = None, action: str = None) -> List[Dict[str, Any]]:
        """获取实盘选手交易数据
        
        Args:
            trader_name: 实盘选手名称
            date: 日期，格式为YYYY-MM-DD
            stock_code: 股票代码
            action: 操作类型，buy/sell
            
        Returns:
            List[Dict[str, Any]]: 实盘选手交易数据列表
        """
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            if trader_name:
                conditions.append("trader_name = ?")
                params.append(trader_name)
            if date:
                conditions.append("date = ?")
                params.append(date)
            if stock_code:
                conditions.append("stock_code = ?")
                params.append(stock_code)
            if action:
                conditions.append("action = ?")
                params.append(action)
            
            # 构建查询语句
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor.execute(f"""
                SELECT * FROM {self.db_config.trader_data_table} 
                WHERE {where_clause} 
                ORDER BY date DESC, id DESC
            """, params)
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            logger.info(f"获取了 {len(result)} 条实盘选手交易数据")
            return result
            
        except Exception as e:
            logger.error(f"获取实盘选手交易数据失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_stock_basic(self, stock_code: str = None) -> List[Dict[str, Any]]:
        """获取股票基本信息
        
        Args:
            stock_code: 股票代码，不指定则返回所有
            
        Returns:
            List[Dict[str, Any]]: 股票基本信息列表
        """
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if stock_code:
                cursor.execute(f"""
                    SELECT * FROM {self.db_config.stock_basic_table} 
                    WHERE stock_code = ?
                """, (stock_code,))
            else:
                cursor.execute(f"""
                    SELECT * FROM {self.db_config.stock_basic_table}
                """)
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            logger.info(f"获取了 {len(result)} 条股票基本信息")
            return result
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def delete_old_data(self, table_name: str, days: int = 30) -> int:
        """删除指定天数前的旧数据
        
        Args:
            table_name: 表名
            days: 保留最近多少天的数据
            
        Returns:
            int: 删除的记录数
        """
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            # 计算截止日期
            cutoff_date = datetime.now().strftime('%Y-%m-%d')
            # SQLite不支持DATE_SUB，所以我们使用Python计算
            import datetime as dt
            cutoff_date = (dt.datetime.now() - dt.timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute(f"""
                DELETE FROM {table_name} WHERE date < ?
            """, (cutoff_date,))
            
            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"从 {table_name} 删除了 {deleted} 条旧数据")
            return deleted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"删除旧数据失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行自定义SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            logger.info(f"执行自定义查询，获取了 {len(result)} 条数据")
            return result
            
        except Exception as e:
            logger.error(f"执行自定义查询失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


# 全局数据管理器实例
data_manager = DataManager()


# 便捷访问函数
def get_data_manager() -> DataManager:
    """获取数据管理器实例"""
    return data_manager


def insert_stock_basic_data(stock_data: List[Dict[str, Any]]) -> int:
    """插入股票基本信息"""
    return data_manager.insert_stock_basic(stock_data)


def insert_hot_stocks_data(hot_stocks: List[Dict[str, Any]]) -> int:
    """插入热门股数据"""
    return data_manager.insert_hot_stocks(hot_stocks)


def insert_trader_data_data(trader_data: List[Dict[str, Any]]) -> int:
    """插入实盘选手交易数据"""
    return data_manager.insert_trader_data(trader_data)


def get_hot_stocks_data(date: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """获取热门股数据"""
    return data_manager.get_hot_stocks(date, limit)


def get_trader_data_data(trader_name: str = None, date: str = None, 
                       stock_code: str = None, action: str = None) -> List[Dict[str, Any]]:
    """获取实盘选手交易数据"""
    return data_manager.get_trader_data(trader_name, date, stock_code, action)


def get_stock_basic_data(stock_code: str = None) -> List[Dict[str, Any]]:
    """获取股票基本信息"""
    return data_manager.get_stock_basic(stock_code)


def delete_old_stock_data(table_name: str, days: int = 30) -> int:
    """删除旧数据"""
    return data_manager.delete_old_data(table_name, days)


def execute_custom_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """执行自定义查询"""
    return data_manager.execute_query(query, params)
