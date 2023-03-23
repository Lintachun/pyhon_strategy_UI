import pandas as pd
import numpy as np
import gradio as gr
import backtrader as bt
import pandas as pd
import ssl
import yfinance as yf
year = []
month  = []
day =[]
class bandStrategy(bt.Strategy):

    def __init__(self):
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=20)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=50)
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()
class OpenBuyCloseSellStrategy(bt.Strategy):
    def __init__(self):
        self.data_close = self.datas[0].close

    def next(self):
        self.buy()
        self.sell(exectype=bt.Order.Stop, price=self.data_close[0])

class OpenCloseStrategy(bt.Strategy):
    params = (
        ('short_period', 20),
        ('long_period', 50),
    )

    def __init__(self):
        self.data_close = self.datas[0].close
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data_close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data_close, period=self.params.long_period)

    def next(self):
        if not self.position and self.short_ma[0] > self.long_ma[0] and self.short_ma[-1] < self.long_ma[-1]:
            self.buy(size=1)

        elif self.position and self.short_ma[0] < self.long_ma[0] and self.short_ma[-1] > self.long_ma[-1]:
            self.sell(size=1)
class RsiStrategy(bt.Strategy):
    
    params = (
        ('rsi_period', 14),
        ('rsi_high', 85),
        ('rsi_low', 25),
        ('printlog', False)
    )
    
    def __init__(self):
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.params.rsi_period)
        self.unit = None
        
    def next(self):
        if self.unit is None:
            self.unit = self.broker.cash / self.data.close[0]
        if self.rsi[0] > self.params.rsi_high and self.position.size > 0:
            if self.params.printlog:
                print(f'Sell {abs(self.position.size):.2f} units at {self.data.close[0]:.2f} (RSI: {self.rsi[0]:.2f})')
            self.sell(size=self.unit)
        elif self.rsi[0] < self.params.rsi_low and self.position.size == 0:
            if self.params.printlog:
                print(f'Buy {self.unit:.2f} units at {self.data.close[0]:.2f} (RSI: {self.rsi[0]:.2f})')
            self.buy(size=self.unit)
                
    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date()
            print(f'{dt.isoformat()} {txt}')

for i in range(2000,2023):
    year.append(str(i))
for i in range(1,13):
    if(i <10):
        month.append("0"+str(i))   
    else:
        month.append(str(i))  
for i in range (1,32):
    if(i <10):
        day.append("0"+str(i))   
    else:
        day.append(str(i))  
demo = gr.Blocks()
def combine(a):
    if(a == "開盤買進,收盤賣出"):
        a=1
    return a
def cerbro_show(text,startday,endday,strategy):
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=yf.download(text, startday, endday, auto_adjust=True))

    cerebro.adddata(data)
           # 設置交易參數
    cerebro.broker.set_cash(10000)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addstrategy(strategy)
    cerebro.run()
    cerebro.plot()
    # 獲取回測結果
    portvalue = cerebro.broker.getvalue()
    pnl = portvalue - 10000
    return(f'獲利: {pnl:.2f} USD ({pnl / 100000:.2%})')
def check_Strategy(dropdown_strategy,start_year_downInput,start_month_downInput,start_day_downInput,end_year_downInput,end_month_downInput,end_day_downInput,text):
    startday = start_year_downInput + "-" + start_month_downInput + "-" +start_day_downInput
    endday =end_year_downInput + "-" + end_month_downInput + "-" +end_day_downInput
    try:
        if(dropdown_strategy == "開盤買進,收盤賣出"):
            Strategy=OpenBuyCloseSellStrategy 
            return (cerbro_show(text,startday,endday,Strategy))
        elif(dropdown_strategy == "簡單移動平均交叉策略"):
            Strategy=OpenCloseStrategy
            return (cerbro_show(text,startday,endday,Strategy))
        elif(dropdown_strategy == "RSI大於85賣出,RSI小於25買進的策略"):
            Strategy=RsiStrategy
            return (cerbro_show(text,startday,endday,Strategy))
        elif(dropdown_strategy == "波段交易"):
            Strategy=bandStrategy
            return (cerbro_show(text,startday,endday,Strategy))
    except:
        return("數值有誤")

with demo:
    gr.Markdown(
        r"股票"
    )
    with gr.Row():
        text =gr.Textbox(label="股票代碼",max_width=100)
        dropdownOptions = ["開盤買進,收盤賣出", "簡單移動平均交叉策略", "RSI大於85賣出,RSI小於25買進的策略","波段交易"]
        dropdownInput = gr.inputs.Dropdown(dropdownOptions, label="選擇策略")
    with gr.Row():    
        with gr.Accordion("選擇起始時間"):
            with gr.Row():
                start_year_downOptions = year
                start_year_downInput = gr.inputs.Dropdown(start_year_downOptions, label="年",default=year[0])
                start_month_downOptions = month
                start_month_downInput = gr.inputs.Dropdown(start_month_downOptions, label="月",default=month[0])
                start_day_downOptions = day
                start_day_downInput = gr.inputs.Dropdown(start_day_downOptions, label="日",default=day[0])
        with gr.Accordion("選擇結束時間"):
            with gr.Row():
                end_year_downOptions = year
                end_year_downInput = gr.inputs.Dropdown(end_year_downOptions, label="年",default=year[len(year)-1])
                end_month_downOptions = month
                end_month_downInput = gr.inputs.Dropdown(end_month_downOptions, label="月",default=month[0])
                end_day_downOptions = day
                end_day_downInput = gr.inputs.Dropdown(end_day_downOptions, label="日",default=day[0])

    btn = gr.Button(value="Run")
    txt_3 = gr.Textbox(value="", label="Output")
    btn.click(check_Strategy, inputs=[dropdownInput,start_year_downInput,start_month_downInput,start_day_downInput,end_year_downInput,end_month_downInput,end_day_downInput,text], outputs=[txt_3])

if __name__ == "__main__":
    demo.launch()

    

