from binance import Client
import pandas as pd
import os

def setup_Api(test):
    if test:
        #Test
        print("TESTRUN")
        api_key = "insert_test_key_here"
        api_secret = "insert_secret_key_here"
        #config_logging(logging, logging.DEBUG)
        #Test
        client = Client(api_key, api_secret,base_url="https://testnet.binance.vision")
    else:
        #config_logging(logging, logging.DEBUG)
        #config_logging(logging)
        api_key = "insert_real_key_here"
        api_secret = "insert_real_secret_key_here"
        client = Client(api_key, api_secret)
    return client



def changepos(curr, buy=True):
    if buy:
        posframe.loc[posframe.Currency == curr, 'position'] = 1
    else:
        posframe.loc[posframe.Currency == curr, 'position'] = 0
    posframe.to_csv('position', index=False)

def gethourlydata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                    '1h',
                                                    '25 hours ago UTC'))
    frame = frame.iloc[:,:5]
    frame.columns = ['Time','Open','High','Low','Close']
    frame[['Time','Open','High','Low','Close']] = frame[['Time','Open','High','Low','Close']].astype(float)
    frame.Time = pd.to_datetime(frame.Time, unit='ms')
    return frame

def applytechnicals(df):
    df['FastSMA'] = df.Close.rolling(7).mean()
    df['SlowSMA'] = df.Close.rolling(25).mean()

def sell_quantity(symbol,client):
    info = client.get_symbol_info(symbol=symbol)
    symbolold = symbol
    Lotsize = float([i for i in info['filters'] if i ['filterType'] == 'LOT_SIZE'][0]['minQty'])
    balances = client.get_account()['balances']
    inv_amt = 0
    symbol = symbol.replace("USDT","")
    #print(symbol)
    for balance in balances:
        ##print(balance)
        if balance['asset'] == str(symbol):
            #print(balance)
            #print(balance['locked'])
            #print(balance['asset'])
            #print(balance['free'])
            inv_amt = float(balance['free'])
            #print(inv_amt)
            if float(Lotsize) == 1.0:
                #print("LOTSIZE == 1------------------------------------------------")
                inv_amt = inv_amt - 1
                #print("sell_Quantity", inv_amt)
            else:
                #print("LOTSIZE != 1------------------------------------------------")
                fee = client.get_trade_fee(symbol=symbolold)
                inv_amt = inv_amt - (inv_amt*float((fee)[0]['takerCommission']))
                #print("SELL QUANTITY with free",inv_amt)
                find_dot = str(inv_amt).find(".")
                #print("find_dot",find_dot)
                #find_lotValue = str(buy_quantity).find("1"
                LotsizeStr = str(Lotsize)
                #print("LotsizeStr",LotsizeStr)
                indexEnd = LotsizeStr.find("1")
                #print(str(inv_amt)[0:find_dot])
                #print(str(inv_amt)[find_dot+1:indexEnd+find_dot])
                buy_quantityStr = str(inv_amt)[0:find_dot] + "." + str(inv_amt)[find_dot+1:indexEnd+find_dot]
                #print("buy_quantityStr",buy_quantityStr)
                inv_amt = float(buy_quantityStr)
                #print("SELL QUANTITY with free",inv_amt)
            return inv_amt

def trader(curr):
    qty = posframe[posframe.Currency == curr].quantity.values[0]
    df = gethourlydata(curr)
    applytechnicals(df)
    lastrow = df.iloc[-1]
    if not posframe[posframe.Currency == curr].position.values[0]: 
        if not float([i for i in client.get_account()['balances'] if i['asset'] == 'USDT'][0]['free']) < 20:
            traderBuy(lastrow,curr,qty)
        else:
            print(f'No money free for position {curr}')

        
    else:
        inv = sell_quantity(curr, client)
        print(inv)
        traderSell(lastrow,curr,inv)

def traderBuy(lastrow,curr,qty):
    if lastrow.FastSMA > lastrow.SlowSMA:
        order = client.create_order(symbol=curr,
                                    side='BUY',
                                    type='MARKET',
                                    quantity=qty)
        print(order)
        changepos(curr, buy=True)
    else:
        print(f'Not in position {curr} but Condition not fullfilled')

def traderSell(lastrow, curr, qty):
    print(f'Already in {curr} position')
    if lastrow.SlowSMA > lastrow.FastSMA:
        print("Sellorder init")
        order = client.create_order(symbol=curr,
                                    side='SELL',
                                    type='MARKET',
                                    quantity=qty)
        changepos(curr,buy=False)
        print(order)
    else:
        print("No Sell")

client = setup_Api(0)
print(os.getcwd())

posframe = pd.read_csv('position')

for coin in posframe.Currency:
    print(coin)
    trader(coin)
# df = gethourlydata('BTCUSDT')
# applytechnicals(df)
# df


