import sys
sys.path.insert(0, '.')
from core.spider import get_stock_spider
from bs4 import BeautifulSoup

spider = get_stock_spider()

# 访问同花顺数据中心
response = spider._request('https://data.10jqka.com.cn/')
response.encoding = 'gbk'  # 同花顺使用gbk编码

# 解析HTML
soup = BeautifulSoup(response.text, 'lxml')

# 查找所有表格
print("页面中所有表格标题:")
tables = soup.find_all('table')
for i, table in enumerate(tables):
    # 查找表格标题
    caption = table.find('caption')
    if caption:
        print(f"表格 {i+1}: {caption.text.strip()}")
    
    # 查找表格前的标题
    prev_elem = table.find_previous(['h1', 'h2', 'h3', 'h4', 'div', 'span'])
    if prev_elem and prev_elem.text.strip():
        print(f"表格 {i+1} 前的标题: {prev_elem.text.strip()}")
    
    print(f"表格 {i+1} 行数: {len(table.find_all('tr'))}")
    print("-" * 50)

# 查找所有包含"热门"或"rank"的元素
print("\n包含'热门'或'排行榜'的元素:")
hot_elements = soup.find_all(text=lambda text: text and ('热门' in text or '排行榜' in text or 'rank' in text.lower()))
for elem in hot_elements[:10]:
    print(elem.strip())

# 查找所有带有class或id包含hot的元素
print("\n带有hot相关class或id的元素:")
hot_class_elements = soup.find_all(class_=lambda cls: cls and 'hot' in cls.lower())
hot_id_elements = soup.find_all(id=lambda id: id and 'hot' in id.lower())
for elem in hot_class_elements[:5] + hot_id_elements[:5]:
    print(f"元素: {elem.name}, class: {elem.get('class')}, id: {elem.get('id')}, 文本: {elem.text.strip()[:100]}")
