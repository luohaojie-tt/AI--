# -*- coding: utf-8 -*-
"""
A股短线选股应用配置管理模块
提供爬虫配置、数据库配置、选股策略配置等功能
"""

import os
from typing import Dict, Any, Optional
import json
from dataclasses import dataclass, asdict
import logging
from logging.handlers import RotatingFileHandler


@dataclass
class SpiderConfig:
    """爬虫配置类"""
    # 同花顺数据获取配置
    thscode_base_url: str = "https://www.10jqka.com.cn"
    hot_stocks_url: str = "https://www.10jqka.com.cn/"
    trader_data_url: str = "https://www.10jqka.com.cn/trader/"
    
    # 请求配置
    request_headers: Dict[str, str] = None
    request_timeout: int = 10
    request_interval: int = 5  # 请求间隔（秒）
    max_retries: int = 3
    
    # 反爬虫配置
    use_proxy: bool = False
    proxy_list: list = None
    use_cookie: bool = True
    cookie_file: str = ".cookie.txt"
    
    def __post_init__(self):
        if self.request_headers is None:
            self.request_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        
        if self.proxy_list is None:
            self.proxy_list = []


@dataclass
class DatabaseConfig:
    """数据库配置类"""
    # SQLite数据库配置
    db_type: str = "sqlite"
    db_path: str = "data/stock_data.db"
    
    # 数据库表名
    hot_stocks_table: str = "hot_stocks"
    trader_data_table: str = "trader_data"
    stock_basic_table: str = "stock_basic"


@dataclass
class StrategyConfig:
    """选股策略配置类"""
    # 选股策略基础配置
    selected_traders: list = None
    max_stocks_per_day: int = 20
    backtest_days: int = 30
    
    # 热门股筛选条件
    min_volume: int = 1000000  # 最小成交量（手）
    min_price_change: float = 5.0  # 最小涨跌幅（%）
    max_price: float = 100.0  # 最大股价
    min_price: float = 5.0  # 最小股价
    
    def __post_init__(self):
        if self.selected_traders is None:
            self.selected_traders = [
                "只核大学生",
                "A拉神灯",
                "请叫我小莽夫",
                "作手奇衡三",
                "这股有毒",
                "低调科科员",
                "二池",
                "青铜交易员",
                "不颜不语"
            ]


@dataclass
class LogConfig:
    """日志配置类"""
    log_level: str = "INFO"
    log_file: str = "logs/stock_selector.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


class ConfigManager:
    """配置管理器"""
    def __init__(self, config_file: str = "app_config.json"):
        self.config_file = config_file
        self.spider = SpiderConfig()
        self.database = DatabaseConfig()
        self.strategy = StrategyConfig()
        self.log = LogConfig()
        self._load_config()
        self._setup_logging()
    
    def _load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新爬虫配置
                if 'spider' in config_data:
                    for key, value in config_data['spider'].items():
                        if hasattr(self.spider, key):
                            setattr(self.spider, key, value)
                
                # 更新数据库配置
                if 'database' in config_data:
                    for key, value in config_data['database'].items():
                        if hasattr(self.database, key):
                            setattr(self.database, key, value)
                
                # 更新策略配置
                if 'strategy' in config_data:
                    for key, value in config_data['strategy'].items():
                        if hasattr(self.strategy, key):
                            setattr(self.strategy, key, value)
                
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = os.path.dirname(self.log.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 获取日志级别
        log_level = getattr(logging, self.log.log_level.upper(), logging.INFO)
        
        # 创建日志格式
        formatter = logging.Formatter(self.log.log_format)
        
        # 创建旋转文件处理器
        file_handler = RotatingFileHandler(
            self.log.log_file,
            maxBytes=self.log.max_bytes,
            backupCount=self.log.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        
        # 获取根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def save_config(self):
        """保存配置到文件"""
        config_data = {
            'spider': asdict(self.spider),
            'database': asdict(self.database),
            'strategy': asdict(self.strategy),
            'log': asdict(self.log)
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)


# 全局配置实例
config_manager = ConfigManager()


# 便捷访问函数
def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager


def update_config(config_dict: Dict[str, Any]) -> None:
    """更新配置"""
    # 更新爬虫配置
    if 'spider' in config_dict:
        for key, value in config_dict['spider'].items():
            if hasattr(config_manager.spider, key):
                setattr(config_manager.spider, key, value)
    # 更新数据库配置
    if 'database' in config_dict:
        for key, value in config_dict['database'].items():
            if hasattr(config_manager.database, key):
                setattr(config_manager.database, key, value)
    # 更新策略配置
    if 'strategy' in config_dict:
        for key, value in config_dict['strategy'].items():
            if hasattr(config_manager.strategy, key):
                setattr(config_manager.strategy, key, value)
    # 保存配置
    config_manager.save_config()


def reset_config() -> ConfigManager:
    """重置配置"""
    global config_manager
    config_manager = ConfigManager()
    return config_manager
