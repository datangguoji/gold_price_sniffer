from flask import Flask, jsonify, render_template
import random
import time
import math
import requests
import re
from datetime import datetime, timedelta
import threading
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)

# 配置外部API
GOLD_DATA_URL = 'https://www.5huangjin.com/data/jin.js'  # 黄金价格数据源
USE_REAL_DATA = True  # 是否使用真实数据

# 初始化黄金数据 - 支持三大市场
gold_data = {
    'london': {
        'open_price': 4042.98,  # 伦敦金初始价格 (现货黄金)
        'current_price': 4042.98,
        'high_price': 4112.82,
        'low_price': 4023.82,
        'avg_price': 4074.34,
        'history': []
    },
    'newyork': {
        'open_price': 4054.72,  # 纽约黄金初始价格
        'current_price': 4054.72,
        'high_price': 4123.80,
        'low_price': 4034.20,
        'avg_price': 4103.20,
        'history': []
    },
    'shanghai': {
        'open_price': 930.20,  # 上海黄金初始价格 (黄金延期)
        'current_price': 930.20,
        'high_price': 946.50,
        'low_price': 928.00,
        'avg_price': 931.88,
        'history': []
    },
    'last_update': datetime.now()
}

# 解析从5huangjin.com获取的JavaScript格式的黄金价格数据
def parse_jin_js_data(data):
    """
    解析从5huangjin.com获取的JavaScript格式的黄金价格数据
    返回包含三大市场详细价格信息的字典
    """
    try:
        result = {}
        
        # 提取伦敦金（现货黄金）价格数据
        # 格式: "4042.98,4112.820,4042.98,4043.34,4108.92,4023.82,18:15:00,4112.82,4074.34,0,0,0,2025-10-27,伦敦金（现货黄金）"
        london_gold_match = re.search(r'var hq_str_hf_XAU="([^"]+)"', data)
        if london_gold_match:
            london_gold_data = london_gold_match.group(1).split(',')
            result['london'] = {
                'current_price': float(london_gold_data[0]),  # 当前价格
                'open_price': float(london_gold_data[7]),     # 开盘价
                'high_price': float(london_gold_data[4]),     # 最高价
                'low_price': float(london_gold_data[5]),      # 最低价
                'avg_price': float(london_gold_data[8])       # 平均价
            }
        
        # 提取纽约黄金价格数据
        # 格式: "4054.720,,4056.900,4057.300,4123.800,4034.200,18:15:16,4137.800,4103.200,0,3,1,2025-10-27,纽约黄金,0"
        newyork_gold_match = re.search(r'var hq_str_hf_GC="([^"]+)"', data)
        if newyork_gold_match:
            newyork_gold_data = newyork_gold_match.group(1).split(',')
            result['newyork'] = {
                'current_price': float(newyork_gold_data[0]),  # 当前价格
                'open_price': float(newyork_gold_data[7]),     # 开盘价
                'high_price': float(newyork_gold_data[4]),     # 最高价
                'low_price': float(newyork_gold_data[5]),      # 最低价
                'avg_price': float(newyork_gold_data[8])       # 平均价
            }
        
        # 提取上海黄金价格数据（黄金延期）
        # 格式: "930.20,0,930.20,930.80,946.50,928.00,15:29:57,935.33,931.88,55720,3.00,10.00,2025-10-27,黄金延期"
        shanghai_gold_match = re.search(r'var hq_str_gds_AUTD="([^"]+)"', data)
        if shanghai_gold_match:
            shanghai_gold_data = shanghai_gold_match.group(1).split(',')
            result['shanghai'] = {
                'current_price': float(shanghai_gold_data[0]),  # 当前价格
                'open_price': float(shanghai_gold_data[7]),     # 开盘价
                'high_price': float(shanghai_gold_data[4]),     # 最高价
                'low_price': float(shanghai_gold_data[5]),      # 最低价
                'avg_price': float(shanghai_gold_data[8])       # 平均价
            }
        
        return result if len(result) > 0 else None
    except Exception as e:
        print(f"解析黄金价格数据失败: {e}")
        return None

# 获取真实的国际黄金价格（三大市场）
def fetch_real_gold_price():
    try:
        # 从5huangjin.com获取黄金价格数据
        response = requests.get(GOLD_DATA_URL, timeout=5)
        response.encoding = 'utf-8'
        
        # 解析JavaScript格式的数据
        market_data = parse_jin_js_data(response.text)
        if market_data:
            # 更新所有市场的黄金价格和详细信息
            for market, data in market_data.items():
                if market in gold_data:
                    gold_data[market]['current_price'] = round(data['current_price'], 2)
                    # 只在首次运行或数据缺失时更新开盘价
                    if gold_data[market]['open_price'] == 0 or not gold_data[market]['history']:
                        gold_data[market]['open_price'] = round(data['open_price'], 2)
                    gold_data[market]['high_price'] = round(data['high_price'], 2)
                    gold_data[market]['low_price'] = round(data['low_price'], 2)
                    gold_data[market]['avg_price'] = round(data['avg_price'], 2)
                    print(f"成功获取{market}市场真实黄金价格: ${data['current_price']}")
            return True
        else:
            print("API返回的数据格式不正确，使用模拟数据")
            return False
    except Exception as e:
        print(f"获取真实黄金价格失败: {e}")
        return False

# 获取历史黄金价格（我们现在只生成模拟历史数据）
def fetch_gold_historical_data():
    # 由于新的数据源不提供历史数据API，我们跳过这一步，直接使用模拟历史数据
    print("跳过历史数据API获取，将使用模拟数据")
    return False

# 生成模拟历史数据
def generate_initial_history():
    # 首先尝试获取真实价格
    if USE_REAL_DATA:
        fetch_real_gold_price()  # 尝试获取最新的真实价格
    
    # 为每个市场生成模拟历史数据
    now = datetime.now()
    
    for market in ['london', 'newyork', 'shanghai']:
        history = []
        # 生成过去24小时的数据，每5分钟一个点，总共288个点
        for i in range(288):
            timestamp = now - timedelta(minutes=5 * i)
            # 模拟价格波动，围绕开盘价上下浮动，逐渐趋近于当前价格
            progress = i / 288  # 0到1，表示从24小时前到现在的进度
            # 计算波动范围，随着时间接近现在，波动范围逐渐减小
            max_deviation = 0.02 * (1 - progress) + 0.005 * progress
            # 根据进度调整价格，使它逐渐趋近于当前价格
            target_price = gold_data[market]['open_price'] + progress * (gold_data[market]['current_price'] - gold_data[market]['open_price'])
            price = target_price * (1 + random.uniform(-max_deviation, max_deviation))
            history.append({
                'timestamp': timestamp.isoformat(),
                'price': round(price, 2)
            })
        # 反转列表，使数据按时间正序排列
        gold_data[market]['history'] = history[::-1]

# 实时价格更新（结合真实数据和模拟）
def update_price():
    update_count = 0
    while True:
        try:
            # 每30秒尝试获取一次真实价格（避免API调用过于频繁）
            if USE_REAL_DATA and update_count % 6 == 0:  # 每6次更新（30秒）尝试一次
                if fetch_real_gold_price():
                    print(f"已更新真实黄金价格数据")
                else:
                    # 真实数据获取失败，使用模拟波动
                    for market in ['london', 'newyork', 'shanghai']:
                        change_percent = random.uniform(-0.002, 0.002)  # 0.2% 以内的波动
                        new_price = gold_data[market]['current_price'] * (1 + change_percent)
                        gold_data[market]['current_price'] = round(new_price, 2)
                        # 更新高低点
                        if new_price > gold_data[market]['high_price']:
                            gold_data[market]['high_price'] = round(new_price, 2)
                        if new_price < gold_data[market]['low_price']:
                            gold_data[market]['low_price'] = round(new_price, 2)
            else:
                # 其他时间使用模拟波动
                for market in ['london', 'newyork', 'shanghai']:
                    change_percent = random.uniform(-0.002, 0.002)  # 0.2% 以内的波动
                    new_price = gold_data[market]['current_price'] * (1 + change_percent)
                    gold_data[market]['current_price'] = round(new_price, 2)
                    # 更新高低点
                    if new_price > gold_data[market]['high_price']:
                        gold_data[market]['high_price'] = round(new_price, 2)
                    if new_price < gold_data[market]['low_price']:
                        gold_data[market]['low_price'] = round(new_price, 2)
            
            # 添加新数据点到各市场的历史记录
            now = datetime.now()
            for market in ['london', 'newyork', 'shanghai']:
                gold_data[market]['history'].append({
                    'timestamp': now.isoformat(),
                    'price': gold_data[market]['current_price']
                })
                
                # 只保留最近的数据点
                max_history_points = 288  # 24小时 * 12个5分钟点
                if len(gold_data[market]['history']) > max_history_points:
                    gold_data[market]['history'] = gold_data[market]['history'][-max_history_points:]
            
            gold_data['last_update'] = now
            update_count += 1
        except Exception as e:
            print(f"更新价格时出错: {e}")
        
        time.sleep(5)  # 每5秒更新一次

# AI分析投资建议（基于三大市场数据）
def generate_investment_advice():
    # 综合分析三大市场的数据
    markets = ['london', 'newyork', 'shanghai']
    valid_markets = [m for m in markets if m in gold_data and len(gold_data[m]['history']) >= 3]
    
    if not valid_markets:
        return "数据不足，无法生成建议"
    
    # 计算各市场的平均涨幅
    avg_changes = []
    for market in valid_markets:
        if len(gold_data[market]['history']) >= 2:
            # 计算最近5个数据点的平均变化率
            recent_prices = [item['price'] for item in gold_data[market]['history'][-5:]]
            changes = [(recent_prices[i] - recent_prices[i-1])/recent_prices[i-1] for i in range(1, len(recent_prices))]
            avg_changes.append(sum(changes) / len(changes))
    
    # 计算整体市场趋势
    overall_trend = sum(avg_changes) / len(avg_changes) if avg_changes else 0
    
    # 以伦敦金为主要参考市场进行深度分析
    primary_market = 'london' if 'london' in valid_markets else valid_markets[0]
    prices = [item['price'] for item in gold_data[primary_market]['history']]
    
    # 计算简单移动平均线
    short_window = min(15, len(prices))  # 缩短窗口以更灵敏地反映近期趋势
    long_window = min(60, len(prices))
    short_ma = sum(prices[-short_window:]) / short_window  # 短期均线
    long_ma = sum(prices[-long_window:]) / long_window     # 长期均线
    
    # 计算波动率（标准差）
    mean_price = sum(prices[-30:]) / min(30, len(prices))  # 最近30个点的平均价
    variance = sum((p - mean_price) ** 2 for p in prices[-30:]) / min(30, len(prices))
    volatility = math.sqrt(variance)
    
    # 计算相对强弱（与开盘价比较）
    price_vs_open = (gold_data[primary_market]['current_price'] - gold_data[primary_market]['open_price']) / gold_data[primary_market]['open_price'] * 100
    
    # 基于综合指标生成建议
    advice = "根据三大黄金交易市场数据分析，"
    
    # 趋势判断
    if overall_trend > 0.001 and short_ma > long_ma:  # 强劲上升趋势
        advice += "当前黄金市场呈现强劲上升趋势，"
        if price_vs_open > 1:  # 已上涨超过1%
            advice += f"今日涨幅已达{price_vs_open:.2f}%，短期内可能面临回调，"
            if volatility > 15:
                advice += "市场波动较大，建议投资者保持谨慎，避免追高，可考虑在回调时择机买入。"
            else:
                advice += "市场波动相对稳定，可考虑分批买入策略。"
        else:
            advice += "涨幅仍在合理范围内，可考虑适量配置。"
    elif overall_trend < -0.001 and short_ma < long_ma:  # 明显下跌趋势
        advice += "当前黄金市场呈现明显下跌趋势，"
        if price_vs_open < -1:  # 已下跌超过1%
            advice += f"今日跌幅已达{abs(price_vs_open):.2f}%，可能存在超卖情况，"
            if volatility > 15:
                advice += "市场波动剧烈，建议保持观望，等待企稳信号出现。"
            else:
                advice += "市场情绪较为平稳，激进投资者可考虑小仓位试探性买入。"
        else:
            advice += "跌幅有限，可关注支撑位表现。"
    else:  # 震荡趋势
        advice += "当前黄金市场处于震荡整理阶段，"
        if abs(overall_trend) < 0.0005 and abs(short_ma - long_ma) / long_ma < 0.005:
            advice += "多空力量相对均衡，短期内突破方向不明确，建议保持观望为主。"
        elif overall_trend > 0:  # 震荡偏强
            advice += "整体略偏强势，可在支撑位附近小幅布局。"
        else:  # 震荡偏弱
            advice += "整体略偏弱，可在压力位附近减仓。"
    
    # 添加各市场最新价格和差异分析
    price_diff_london_newyork = abs(gold_data['london']['current_price'] - gold_data['newyork']['current_price'])
    advice += f" 截至最新数据，"
    advice += f"伦敦金报${gold_data['london']['current_price']:.2f}，"
    advice += f"纽约黄金报${gold_data['newyork']['current_price']:.2f}，"
    advice += f"上海黄金延期报${gold_data['shanghai']['current_price']:.2f}。"
    
    # 跨市场套利提示
    if price_diff_london_newyork > 20:  # 价差超过20美元
        advice += " 伦敦和纽约市场存在一定价差，投资者可关注跨市场套利机会。"
    
    # 风险提示
    advice += " 请注意，黄金价格受多种因素影响，投资有风险，请根据个人风险承受能力制定投资策略。"
    
    return advice

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/gold-price')
def get_gold_price():
    # 准备每个市场的数据
    market_data = {}
    for market in ['london', 'newyork', 'shanghai']:
        # 计算涨幅
        change_percent = ((gold_data[market]['current_price'] - gold_data[market]['open_price']) / gold_data[market]['open_price']) * 100
        
        market_data[market] = {
            'current_price': gold_data[market]['current_price'],
            'open_price': gold_data[market]['open_price'],
            'high_price': gold_data[market]['high_price'],
            'low_price': gold_data[market]['low_price'],
            'avg_price': gold_data[market]['avg_price'],
            'change_percent': round(change_percent, 2),
            'history': gold_data[market]['history']
        }
    
    # 按用户需求，将伦敦金作为默认显示的主要价格
    primary_market = 'london'
    return jsonify({
        'current_price': gold_data[primary_market]['current_price'],
        'open_price': gold_data[primary_market]['open_price'],
        'high_price': gold_data[primary_market]['high_price'],
        'low_price': gold_data[primary_market]['low_price'],
        'change_percent': round(((gold_data[primary_market]['current_price'] - gold_data[primary_market]['open_price']) / gold_data[primary_market]['open_price']) * 100, 2),
        'history': gold_data[primary_market]['history'],
        'markets': market_data,
        'last_update': gold_data['last_update'].isoformat()
    })

@app.route('/api/investment-advice')
def get_investment_advice():
    advice = generate_investment_advice()
    return jsonify({'advice': advice})

if __name__ == '__main__':
    # 初始化历史数据
    generate_initial_history()
    
    # 启动价格更新线程
    price_thread = threading.Thread(target=update_price)
    price_thread.daemon = True
    price_thread.start()
    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True)