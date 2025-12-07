import sys
import re
sys.path.insert(0, '.')
from core.spider import get_stock_spider

spider = get_stock_spider()
response = spider._request('https://www.10jqka.com.cn/')
text = response.text

# 查找所有链接
links = re.findall(r'href=[\"\'](https?://[^\"\']*)[\"\']', text)

# 筛选热门相关链接
hot_links = [link for link in links if 'hot' in link.lower() or 'rank' in link.lower()]
print("热门相关链接:")
for link in hot_links[:10]:
    print(link)

# 查找所有A股相关链接
a_share_links = [link for link in links if 'hs_a' in link.lower() or 'stock' in link.lower()]
print("\nA股相关链接:")
for link in a_share_links[:10]:
    print(link)
