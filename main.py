import json
import openai as op
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf
import os
from dotenv import load_dotenv


def configure():
    load_dotenv()
    op.api_key = os.getenv("API_KEY")
    #op.api_key = open('.env', 'r').read()
configure()

# Getting Stock Price
def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)

# Calculating Simple Moving Average (SMA)
def calculate_sma(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

# Calculating Exponential Moving Average (EMA)
def calculate_ema(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

# Calculating Relative Strength Index (RSI)
def calculate_rsi(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14-1, adjust=False).mean()
    ema_down = down.ewm(com=14-1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100 -(100 / (1+rs)).iloc[-1])

#Calculating Moving Average Convergence Divergence
def calculate_macd(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_ema = data.ewm(span=12, adjust=False).mean()
    long_ema = data.ewm(span=26, adjust=False).mean()

    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_histogram = macd - signal

    return f'{macd[-1]}, {signal[-1]}, {macd_histogram[-1]}'

# Plotting Stock Price
def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    plt.figure(figsize=(10, 5))
    plt.plot(data.index,data.Close)
    plt.title('{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()


functions = [
    {
        'name' : 'get_stock_price',
        'description' : 'Get the latest stock price given on the ticker symbol of a company',
        'parameters': {
            'type' : 'object',
            'properties' : {
                'ticker' : {
                    'type' : 'string',
                    'description' : 'The stock ticker symbol for a company (e.g: AAPL for apple).'
                }
            },
            'required' : ['ticker']
        }
    },
    {
        'name' : 'calculate_sma',
        'description' : 'Calculate the Simple Moving Average for a given stock ticker and a window',
        'parameters': {
            'type' : 'object',
            'properties' : {
                'ticker' : {
                    'type' : 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL for apple).',
                },
                'window' : {
                    'type' : 'integer',
                    'description' : 'The timeframe to consider when calculating the sma',
                }
            },
            'required' : ['ticker', 'window'],
        }
    },
    {
        'name' : 'calculate_ema',
        'description' : 'Calculate the Exponential Moving Average for a given stock ticker and a window',
        'parameters': {
            'type' : 'object',
            'properties' : {
                'ticker' : {
                    'type' : 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL for apple).',
                },
                'window' : {
                    'type' : 'integer',
                    'description' : 'The timeframe to consider when calculating the ema',
                }
            },
            'required' : ['ticker', 'window'],
        }
    },
    {
        'name' : 'calculate_rsi',
        'description' : 'Calculate the RSI for a given stock ticker',
        'parameters': {
            'type' : 'object',
            'properties' : {
                'ticker' : {
                    'type' : 'string',
                    'description' : 'The stock ticker symbol for a company (e.g: AAPL for apple).',
                },
            },
            'required' : ['ticker'],
        }
    },
    {
        'name' : 'calculate_macd',
        'description' : 'Calculate the macd for a given stock ticker',
        'parameters': {
            'type' : 'object',
            'properties' : {
                'ticker' : {
                    'type' : 'string',
                    'description' : 'The stock ticker symbol for a company (e.g: AAPL for apple).',
                },
            },
            'required' : ['ticker'],
        }
    },
    {
        'name' : 'plot_stock_price',
        'description' : 'Plot the stock price for the last year given the ticker symbol of a company ',
        'parameters': {
            'type' : 'object',
            'properties' : {
                'ticker' : {
                    'type' : 'string',
                    'description' : 'The stock ticker symbol for a company (e.g: AAPL for apple).',
                },
            },
            'required' : ['ticker'],
        }
    }
]

available_functions = {
    'get_stock_price': get_stock_price,
    'calculate_sma': calculate_sma,
    'calculate_ema': calculate_ema,
    'calculate_rsi': calculate_rsi,
    'calculate_macd': calculate_macd,
    'plot_stock_price': plot_stock_price
}

if 'messages' not in st.session_state:
    st.session_state.messages = []

st.title('Stock Analysis Chatbot Assistant')

user_input = st.text_input('Your Input:')

if user_input:
    try:
        st.session_state['messages'].append({'role' : 'user', 'content' : f'{user_input}'})

        response = op.ChatCompletion.create(
            model = 'gpt-3.5-turbo',
            messages = st.session_state['messages'],
            functions = functions,
            function_call = 'auto'
        )

        response_msg = response['choices'][0]['message']

        if response_msg.get('function_call'):
            function_name = response_msg['function_call']['name']
            function_arg = json.loads(response_msg['function_call']['arguments'])
            if function_name in ['get_stock_price', 'calculate_rsi', 'calculate_macd', 'plot_stock_price']:
                args_dict = {'ticker' : function_arg.get('ticker')}
            elif function_name in ['calculate_ema', 'calculate_sma']:
                args_dict = {'ticker' : function_arg.get('ticker'), 'window' : function_arg.get('window')}

            funtion_to_call = available_functions[function_name]
            function_response = funtion_to_call(**args_dict)

            if function_name == 'plot_stock_price':
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_msg)
                st.session_state['messages'].append(
                    {
                        'role' : 'function',
                        'name' : function_name,
                        'content' : function_response,
                    }
                )

                second_response = op.ChatCompletion.create(
                    model = 'gpt-3.5-turbo',
                    messages = st.session_state['messages'],
                )

                st.text(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response['choices'][0]['message']['content']})
        else:
            st.text(response_msg['content'])
            st.session_state['messages'].append({'role': 'assistant', 'content' : response_msg['content']})
    except Exception as e:
        raise e