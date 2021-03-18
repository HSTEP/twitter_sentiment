import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import kody
from dash_table.Format import Format, Scheme, Sign, Symbol
from datetime import datetime as dt
from dash.dependencies import Input, Output
import datetime
import yfinance as yf
import numpy as np
import time
from dateutil.relativedelta import relativedelta
from layouts import portfolio
import mysql.connector

app = dash.Dash(__name__, suppress_callback_exceptions=True) #jinak callback nefunguje u multipage apps
server = app.server
app.title = "StepanH"

colors = {
    "background": "black",
    "text": "#ff8000",
    "button_background" : "#663300",
    "button_text" : "#01ff70",
    "button_border" : "1px solid #ff8000",
}

def get_data_news(table_name):
    cnx = mysql.connector.connect(user=kody.mysql_username, password=kody.mysql_password,
                                  host='localhost',
                                  database='twitter',
                                  charset = 'utf8')
    #Order by musí být ASC, jinak nejsou klouzavé průměry až do konce:
    df = pd.read_sql('SELECT source, published, title, url, sentiment, sentiment_vader FROM '+ table_name +' ORDER BY published ASC', con=cnx)
    df = df.set_index(['published'])
    df["ma_short"] = df.sentiment.rolling(window=10).mean()
    df["ma_long"] = df.sentiment.rolling(window=30).mean()
    df["vader_ma_short"] = df.sentiment_vader.rolling(window=10).mean()
    df["vader_ma_long"] = df.sentiment_vader.rolling(window=30).mean()
    df['epoch'] = df.index.astype(np.int64)
    df["volume"] = 1
    links = df['url'].to_list()
    rows = []
    for x in links:
        link = '[link](' +str(x) + ')'
        rows.append(link)#
    df['url'] = rows
    return df

def get_data_reddit(table_name):
    cnx = mysql.connector.connect(user=kody.mysql_username, password=kody.mysql_password,
                                  host='localhost',
                                  database='twitter',
                                  charset = 'utf8')
    df= pd.read_sql('SELECT time, subreddit, post, username, karma_post, ups, topic_comment, sentiment_textblob, sentiment_vader, url FROM '+ table_name +' ORDER BY time ASC', con=cnx)
    df= df.set_index(['time'])
    df["ma_short"] = df.sentiment_textblob.rolling(window=10).mean()
    df["ma_long"] = df.sentiment_textblob.rolling(window=30).mean()
    df["vader_ma_short"] = df.sentiment_vader.rolling(window=10).mean()
    df["vader_ma_long"] = df.sentiment_vader.rolling(window=30).mean()
    df['epoch'] = df.index.astype(np.int64)
    df["volume"] = 1
    links = df['url'].to_list()
    rows = []
    for x in links:
        link = '[link](' +str(x) + ')'
        rows.append(link)#
    df['url'] = rows
    return df

def get_data_reddit_volume(table_name):
    df_volume = get_data_reddit(table_name).resample('720min').agg({'volume': np.sum, 'sentiment_textblob': np.mean,'sentiment_vader': np.mean})
    df_volume["epoch"] =  df_volume.index.astype(np.int64)
    df_volume["MA"] = df_volume.volume.rolling(window=10).mean()
    return df_volume

#def get_data(table_name):
#    data_frame = pd.read_sql('SELECT time, username, tweet, followers,  sentiment, sentiment_vader FROM '+ table_name +' ORDER BY time ASC', con=kody.cnx)
#    data_frame["ma_short"] = data_frame.sentiment.rolling(window=1000).mean()
#    data_frame["ma_long"] = data_frame.sentiment.rolling(window=10000).mean()
#    data_frame["vader_ma_short"] = data_frame.sentiment_vader.rolling(window=10).mean()
#    data_frame["vader_ma_long"] = data_frame.sentiment_vader.rolling(window=100).mean()    
#    data_frame['epoch'] = data_frame['time'].astype(np.int64)
#    data_frame = data_frame.iloc[::100] #zobrazí každý n-tý bod v data-framu
#    print("Get data called on ", table_name, " at: ", time.time())
#    return data_frame
#print("dataframetweetTable",get_data("tweetTable")["time"])

#gild = yf.download("GILD")
#data_gild = pd.DataFrame(data=gild)
#
#fig_gild = px.scatter(render_mode="webgl")
#fig_gild.add_scatter(y=data_gild["Close"], mode="lines", name="Gild closing price")
#fig_gild.update_layout(title_text="GILD stock price",
#                    title_x=0.5,
#                    template="plotly_dark", 
#                    legend_title_text="", 
#                    legend_orientation="h", 
#                    legend=dict(x=0, y=1))

now_minus_one_hour = dt.now() - relativedelta(hours=1)
data_frame_is_it_running = pd.read_sql('SELECT script, time FROM running_scripts ORDER BY time ASC', con=kody.cnx)
data_frame_is_it_running["status"] = np.where(data_frame_is_it_running["time"] > now_minus_one_hour, "YES","NO")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

index = html.Div(style={"backgroundColor": "black"},children=[
    html.Button(dcc.Link('Twitter sentiment', href='/twitter_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('News Sentiment', href='/news_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Reddit Sentiment', href='/reddit_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Running Scripts', href='/running_scripts',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"], "float":"right"}),
    html.H1(
    children='index',
    style={
        "color": colors["text"],
        "textAlign": "center"
        }),
    html.Button(html.A('GitHub Code', href='https://github.com/HSTEP/twitter_sentiment', target='_blank'), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
])

twitter_sentiment = html.Div(style={"backgroundColor": colors["background"]}, children=[
    
    html.Div(id='page-1-content'),
    html.Button(dcc.Link('Index', href='/',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('News Sentiment', href='/news_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Reddit Sentiment', href='/reddit_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Running Scripts', href='/running_scripts',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"], "float":"right"}),
    html.H1(
        children='Twitter sentiment',
        style={
            "color": colors["text"],
            "textAlign": "center"
            }
        ),
    
    html.Div(
        [
            dcc.Dropdown(
                id='twitter-dropdown',
                options=[
                    {'label': 'Ripple or XRP', 'value': 'tweetTable_resampled_5m'},
                    {'label': 'Cloudflare', 'value': 'tweetTable_AR_NET_rt'},
                    {'label': 'Oracle OR ORCL', 'value': 'tweetTable_AR_ORCL_rt'},
                    {'label': 'Pritzer OR PFE', 'value': 'tweetTable_AR_PFE_rt'},
                    {'label': 'Ferrari', 'value': 'tweetTable_AR_RACE_rt'}
                ],
                value='tweetTable_resampled_5m',
                clearable=False,
                style = {
                        'width': '300px',
                        #'padding-left' : '100px',
                        #'color' : colors["button_text"],
                        #'background-color' : colors["button_background"],
                        },
            ),
        ]),  
    html.Div(
        [
            dcc.Checklist(
                id = 'sentiment_ma',
                options = [
                    {"label" : "Long MA TextBlob", "value" : "long_ma"},
                    {"label" : "Short MA TextBlob", "value" : "short_ma"},
                    {"label" : "Long MA Vader", "value" : "vader_ma_long"},
                    {"label" : "Short MA Vader", "value" : "vader_ma_short"}
                ],
                value = ["vader_ma_short"],
                labelStyle = {"display" : "inline-block", "background-color": colors["button_background"], "color" : colors["button_text"], "border" : "black"}
            ),
        ],
    ),

    dcc.Loading(id='load-component-tweetGraph', color=colors["button_text"], children=[
        html.Div([
            dcc.Graph(id='chart-with-slider-tweetTable'),
            ])
        ]),
    html.Div([
        dcc.Slider(
        id='year-slider-tweetTable',
        min=1593560870000000000,
        max=time.time()*10**9,
        value=time.time()*10**9 - 259200*10**9,
        step=86400*10**9,
        #updatemode="mouseup",
        ),
        html.Div(id="year-slider-value-tweetTable", style={
            "color": colors["text"],
            "textAlign": "center"
            }),
        ]),
    dcc.Interval(
        id='interval-component-chart',
        interval=30*1000, # in milliseconds
        n_intervals=0
        ),
    html.Div([html.P(id = "count-tweetTable",
                    style={
                        "color": colors["text"]
                        }
                    ),
                dcc.Interval(id='interval-component-count-tweetTable',
                        interval=10*1000, # in milliseconds
                        n_intervals=0)
        ]),
    html.Div(
        [
            dcc.RadioItems(
                id = 'table_checklist',
                options = [
                    {"label" : "Textblob Top", "value" : "tweetTable_resampled_sentiment"},
                    {"label" : "Last Day", "value" : "last_day"},
                    {"label" : "All Tweets", "value" : "all_tweets"},
                ],
                value = "last_day",
                labelStyle = {"display" : "inline-block", "background-color": colors["button_background"], "color" : colors["button_text"], "border" : "black"}
            ),
        ],
    ),

    dcc.Loading(id='load-component-tweetTable', color=colors["button_text"], children=[
        html.Div(dash_table.DataTable(
            id="table",
            columns=[{
                "id" : "username",
                "name" : "Username",
                "type" : "text"
                },{
                "id" : "followers_count",
                "name" : "Followers",
                "type" : "text"
                },{
                "id" : "created_at",
                "name" : "Time",
                "type" : "datetime"
                },{
                "id" : "tweet",
                "name" : "Tweet",
                "type" : "text"
                },{
                "id" : "sentiment_textblob",
                "name" : "TextBlob",
                "type" : "numeric",
                "format" : Format(
                    precision = 5,
                ),
                }],

            filter_action='native',
            css=[{'selector': '.dash-filter > input', 'rule': 'color: #01ff70; text-align : left'}],
            style_filter={"backgroundColor" : "#663300"}, #styly filtrů fungujou divně proto je zbytek přímo v css
            fixed_rows={ 'headers': True, 'data': 0 },
            sort_action="native",
            page_size= 10,
            style_header={
                "fontWeight" : "bold",
                "textAlign" : "center"
            },
            style_cell={
                "textAlign" : "left",
                "backgroundColor" : colors["background"],
                "color" : colors["text"],

            },
            style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            'maxWidth': '500px',
            'minWidth': '50px',
            },
            style_cell_conditional=[
                {
                'if': {'column_id': 'followers'},
                'width': '90px'
                },
                {
                'if': {'column_id': 'time'},
                'width': '90px'
                },
            ],
            style_as_list_view=True,
            virtualization=True,
            page_action="none"
            ),style={
                #"width": "48%",
                #"align": "right",
                #"display": "inline-block"
                }),

        #html.Div(dcc.Graph(id="chart_gild",figure=fig_gild)),

        dcc.Interval(
            id="interval-component",
            interval=30*1000
        ),],),

        # html.Iframe(srcDoc='''
        # <div class="tradingview-widget-container">
        # <div id="tradingview_20db9"></div>
        # <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/symbols/NASDAQ-AAPL/" rel="noopener" #target="_blank"><span class="blue-text">AAPL Chart</span></a> by TradingView</div>
        # <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        # <script type="text/javascript">
        # new TradingView.widget(
        # {
        # "height": 700,
        # "width" : 900,
        # "symbol": "NASDAQ:GILD",
        # "interval": "D",
        # "timezone": "Etc/UTC",
        # "theme": "dark",
        # "style": "1",
        # "locale": "en",
        # "toolbar_bg": "#f1f3f6",
        # "enable_publishing": false,
        # "allow_symbol_change": true,
        # "container_id": "tradingview_20db9"               source, published, title, url, sentiment
        # }
        # );
        # </script>''', style={
        #                 "height": 700,
        #                 "width" : 900
        #                 })
])

GILD_sentiment = html.Div(style={"backgroundColor": "black"},children=[
    html.Div(id='page-2-content'),
    html.Button(dcc.Link('index', href='/',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Twitter sentiment', href='/twitter_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Reddit Sentiment', href='/reddit_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Running Scripts', href='/running_scripts',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"], "float":"right"}),
    html.H1(children='News Sentiment',
        style=
        {
        "color": colors["text"],
        "textAlign": "center"
        }),
    html.Div(
        [
            dcc.Dropdown(
                id='news-dropdown',
                options=[
                    {'label': 'GILD or Gilead or Remdesivir', 'value': 'newsGILD'},
                    {'label': 'Airbus', 'value': 'newsAIRBUS'},
                    {'label': 'Boeing', 'value': 'newsBOEING'},
                    {'label': 'Ford', 'value': 'newsF'},
                    {'label': 'Ferrari', 'value': 'newsRACE'},
                    {'label': 'Toyota', 'value': 'newsTOYOF'},
                    {'label': 'Oracle or ORCL', 'value': 'newsORCL'},
                    {'label': 'AZN', 'value': 'newsAZN'}
                ],
                value='newsGILD',
                clearable=False,
                style = {
                        'width': '300px',
                        #'padding-left' : '100px',
                        #'color' : colors["button_text"],
                        #'background-color' : colors["button_background"],
                        },
            ),
        ]),
    html.Div(
        [
            dcc.Checklist(
                id = 'checklist_gild',
                options = [
                    {"label" : "Long MA TextBlob", "value" : "long_ma"},
                    {"label" : "Short MA TextBlob", "value" : "short_ma"},
                    {"label" : "Long MA Vader", "value" : "vader_ma_long"},
                    {"label" : "Short MA Vader", "value" : "vader_ma_short"},
                    {"label" : "Scatter TextBlob", "value" : "sentiment_textblob"},
                    {"label" : "Scatter Vader", "value" : "sentiment_vader"}
                ],
                value = ["sentiment_textblob"],
                labelStyle = {"display" : "inline-block", "background-color": colors["button_background"], "color" : colors["button_text"], "border" : "black"},
                inputStyle={"margin-left": "8px"}
            ),
        ],
    ),
    html.Div(dcc.Loading(id='load-component-tweetGraph', color=colors["button_text"], children=[
        dcc.Graph(id='chart-with-slider-news')]),
        style = {
            'width': '69%',
            'text-align' : 'left',
            'display' : 'inline-block'
            }
        ),
    html.Div(html.Img(
        id = "wordcloud_news",
        src = app.get_asset_url('wordcloud_news_gild.svg'), 
        height = "500px"),
        style = {
            'width': '29%',
            'text-align' : 'right',
            'display' : 'inline-block'
            }
    ),
    html.Div(
        dcc.Slider(
        id='year-slider-news',
        min=1594412760000000000,
        max=time.time()*10**9,
        value=time.time()*10**9 - 864000*10**9,
        step=86400*10**9,
        ), style={'width': '69%','text-align' : 'left'}),
    html.Div(id="year-slider-value-news", style={
            "color": colors["text"],
            'width': '69%',
            'text-align' : 'center'}),
    dcc.Interval(
            id='interval-component-news-chart',
            interval=60*1000, # in milliseconds
            n_intervals=0
        ),
    html.Div([html.P(id = "count-news",
                    style={
                        "color": colors["text"]
                        }
                    ),
                dcc.Interval(id='interval-component-count',
                        interval=10*1000, # in milliseconds
                        n_intervals=0)
        ]),
    html.Div(dash_table.DataTable(
        id="table_newsGILD",
        columns=[{
            "id" : "source",
            "name" : "Source",
            "type" : "text"
            },{
            "id" : "published",
            "name" : "Published",
            "type" : "datetime"
            },{
            "id" : "title",
            "name" : "Title",
            "type" : "text"
            },{
            "id" : "url",
            "name" : "url",
            "type" : "text",
            "presentation" : "markdown"
            },{
            "id" : "sentiment",
            "name" : "TextBlob",
            "type" : "numeric",
            "format" : Format(
                precision = 5,
            )},{
            "id" : "sentiment_vader",
            "name" : "Vader",
            "type" : "numeric",
            "format" : Format(
                precision = 5,
            ),}
            ],

        filter_action='native',
        css=[{'selector': '.dash-filter > input', 'rule': 'color: #01ff70; text-align : left'}],
        style_filter={"backgroundColor" : "#663300"}, #styly filtrů fungujou divně proto je zbytek přímo v css
        data=get_data_news("newsGILD").to_dict('records'),
        fixed_rows={ 'headers': True, 'data': 0 },
        sort_action="native",
        page_size= 10,
        style_header={
            "fontWeight" : "bold",
            "textAlign" : "center"
        },
        style_cell={
            "textAlign" : "left",
            "backgroundColor" : colors["background"],
            "color" : colors["text"],

        },
        style_data={
        'whiteSpace': 'normal',
        'height': 'auto',
        'maxWidth': '500px',
        'minWidth': '50px',
        },
        style_cell_conditional=[
            {
            'if': {'column_id': 'followers'},
            'width': '90px'
            },
            {
            'if': {'column_id': 'time'},
            'width': '90px'
            },
        ],
        style_data_conditional=[                
            {
                "if": {"state": "selected"},              # 'active' | 'selected'
                "backgroundColor": "#003855",
                "border": "white",
            },
        ],
        style_as_list_view=True,
        virtualization=True,
        page_action="none"
        ),style={
            #"width": "48%",
            #"align": "right",
            #"display": "inline-block"
            }),
    dcc.Interval(
        id='interval-component-newsGILD',
        interval=70*1000, # in milliseconds
        n_intervals=0
    )
])

reddit_layout = html.Div(style={"backgroundColor": "black"},children=[
    html.Button(dcc.Link('index', href='/',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Twitter sentiment', href='/twitter_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('News Sentiment', href='/news_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Running Scripts', href='/running_scripts',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"], "float":"right"}),
    html.H1(children='Reddit Sentiment',
        style=
        {
        "color": colors["text"],
        "textAlign": "center"
        }),
    html.Div(
        [
            dcc.Dropdown(
                id='reddit-dropdown',
                options=[
                    {'label': 'GILD or Gilead or Remdesivir', 'value': 'redditGILD'},
                    #{'label': 'AMD', 'value': 'redditAMD'},
                    #{'label': 'San Francisco', 'value': 'SF'}
                ],
                value='redditGILD',
                clearable=False,
                style = {
                        'width': '300px',
                        #'padding-left' : '100px',
                        #'color' : colors["button_text"],
                        #'background-color' : colors["button_background"],
                        },
            ),
        ]),
    html.Div(
        [
            dcc.Checklist(
                id = 'checklist_gild',
                options = [
                    {"label" : "Long MA TextBlob", "value" : "long_ma"},
                    {"label" : "Short MA TextBlob", "value" : "short_ma"},
                    {"label" : "Long MA Vader", "value" : "vader_ma_long"},
                    {"label" : "Short MA Vader", "value" : "vader_ma_short"},
                    {"label" : "Scatter TextBlob", "value" : "sentiment_textblob"},
                    {"label" : "Scatter Vader", "value" : "sentiment_vader"}
                ],
                value = ["sentiment_textblob"],
                labelStyle = {"display" : "inline-block", "background-color": colors["button_background"], "color" : colors["button_text"], "border" : "black"},
                inputStyle={"margin-left": "8px"}
            ),
        ],
    ),
    html.Div([dcc.Graph(id='chart-with-slider-reddit'),
        dcc.Slider(
        id='year-slider-reddit',
        min=132541261000000000,
        max=time.time()*10**9,
        value=time.time()*10**9 - 2592000*10**9,
        step=86400*10**9,
        ),
    dcc.Interval(
            id='interval-component-reddit-chart',
            interval=60*1000, # in milliseconds
            n_intervals=0
        )
        ], style={'width': '100%', 'display': 'inline-block'}),

    #    html.Div(html.Img(
    #        id = "wordcloud_reddit",
    #        src = app.get_asset_url('wordcloud_reddit_gild.svg'), 
    #        height = "500px"),
    #        style = {
    #            'width': '29%', 
    #            'display': 'inline-block', 
    #            'text-align' : 'center'
    #            }
    #        ),
    html.Div([html.P(id = "count-reddit",
                    style={
                        "color": colors["text"]
                        }
                    ),
                dcc.Interval(id='interval-component-count',
                        interval=10*1000, # in milliseconds
                        n_intervals=0)
        ]),
    html.Div(dash_table.DataTable(
        id="table_redditGILD",
        columns=[{
            "id" : "time",
            "name" : "Time",
            "type" : "datetime"
            },{
            "id" : "subreddit",
            "name" : "Subreddit",
            "type" : "text"
            },{
            "id" : "post",
            "name" : "Post",
            "type" : "text"
            },{
            "id" : "username",
            "name" : "Username",
            "type" : "text"
            },{
            "id" : "karma_post",
            "name" : "Post Karma",
            "type" : "numeric",
            },{
            "id" : "ups",
            "name" : "Upvotes",
            "type" : "numeric",
            },{
            "id" : "topic_comment",
            "name" : "Comment",
            "type" : "text"
            },{
            "id" : "sentiment_textblob",
            "name" : "TextBlob",
            "type" : "numeric",
            "format" : Format(
                precision = 5,
            ),},{
            "id" : "sentiment_vader",
            "name" : "Vader",
            "type" : "numeric",
            "format" : Format(
                precision = 5,
            ),},{
            "id" : "url",
            "name" : "url",
            "type" : "text",
            "presentation" : "markdown"
            }
            ],

        filter_action='native',
        css=[{'selector': '.dash-filter > input', 'rule': 'color: #01ff70; text-align : left'}],
        style_filter={"backgroundColor" : "#663300"}, #styly filtrů fungujou divně proto je zbytek přímo v css
        data=get_data_reddit("redditGILD").to_dict('records'),
        fixed_rows={ 'headers': True, 'data': 0 },
        sort_action="native",
        page_size= 10,
        style_header={
            "fontWeight" : "bold",
            "textAlign" : "center"
        },
        style_cell={
            "textAlign" : "left",
            "backgroundColor" : colors["background"],
            "color" : colors["text"],

        },
        style_data={
        'whiteSpace': 'normal',
        'height': 'auto',
        'maxWidth': '500px',
        'minWidth': '50px',
        },
        style_cell_conditional=[
            {
            'if': {'column_id': 'ups'},
            'width': '50px'
            },
            {
            'if': {'column_id': 'username'},
            'width': '90px'
            },
        ],
        style_data_conditional=[                
            {
                "if": {"state": "selected"},              # 'active' | 'selected'
                "backgroundColor": "#003855",
                "border": "white",
            },
        ],
        style_as_list_view=True,
        virtualization=True,
        page_action="none"
        ),style={
            #"width": "48%",
            #"align": "right",
            #"display": "inline-block"
            }),
    dcc.Interval(
        id='interval-component-redditGILD',
        interval=70*1000, # in milliseconds
        n_intervals=0
    )
])

running_scripts = html.Div(style={"backgroundColor": "black"},children=[
    html.Button(dcc.Link('Index', href='/',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Twitter sentiment', href='/twitter_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('News Sentiment', href='/news_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.Button(dcc.Link('Reddit Sentiment', href='/reddit_sentiment',style={"color" : colors["button_text"]}), style={"background-color" : colors["button_background"], "border" : colors["button_border"]}),
    html.H1(
    children='Running Scripts',
    style={
        "color": colors["text"],
        "textAlign": "center"
        }),
    html.Div(dash_table.DataTable(
        id="table_running_scripts",
        columns=[{
            "id" : "script",
            "name" : "Script",
            "type" : "text"
            },{
            "id" : "time",
            "name" : "Last Update",
            "type" : "datetime"
            },{
            "id" : "status",
            "name" : "Updated Last Hour",
            "type" : "text"
            }],

        #filter_action='native',
        css=[{'selector': '.dash-filter > input', 'rule': 'color: #01ff70; text-align : left'}],
        #style_filter={"backgroundColor" : "#663300"}, #styly filtrů fungujou divně proto je zbytek přímo v css
        data=data_frame_is_it_running.to_dict('records'),
        fixed_rows={ 'headers': True, 'data': 0 },
        sort_action="native",
        page_size= 5,
        style_header={
            "fontWeight" : "bold",
            "textAlign" : "center"
        },
        style_cell={
            "textAlign" : "left",
            "backgroundColor" : colors["background"],
            "color" : colors["text"],

        },
        style_data={
        'whiteSpace': 'normal',
        'height': 'auto',
        'maxWidth': '500px',
        'minWidth': '100px',
        },
        style_cell_conditional=[
            {
            'if': {'column_id': 'script'},
            'width': '90px'
            },
            {
            'if': {'column_id': 'time'},
            'width': '90px'
            },
            {
            'if': {'column_id':'status'},
            'width':'90px'    
            },
        ],
        style_data_conditional=[
            {
            'if': {'filter_query': '{status} = YES', 'column_id': 'status'},
            "color" : colors["button_text"],
            "textAlign":"center"
            }
        ],
        style_as_list_view=True,
        #virtualization=True,
        page_action="none"
        ),style={
            #"width": "48%",
            "margin-left": "20px",
            "margin-right": "20px",
            #"display": "inline-block"
            }),
    dcc.Interval(
        id='interval-component-iir',
        interval=10*1000, # in milliseconds
        n_intervals=0
    ) 
])

#--------------------callback pro otevření cesty k jiné Dash stránce--------------------
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])     #callbak pro víc stránek
def display_page(pathname):
    if pathname == '/twitter_sentiment':
        return twitter_sentiment
    elif pathname == '/news_sentiment':
        return GILD_sentiment
    elif pathname == '/reddit_sentiment':
        return reddit_layout
    elif pathname =='/running_scripts':
        return running_scripts
    elif pathname =='/portfolio':
        return portfolio.portfolio_layout
    else:
        return index

#================================================================================================================


#--------------------callback pro update grafu z MySQL tweetTable-----------------------
@app.callback(
    Output('chart-with-slider-tweetTable', 'figure'),
    [Input('year-slider-tweetTable', 'value'), #callback pro chart slider
     #Input('interval-component-chart','n_intervals'), #callbak pro update grafu
     Input('twitter-dropdown', 'value'), #callback pro dropdown
     Input('sentiment_ma', 'value') #callback pro checklist
     ]) 

def update_tweetTable(selected_time, keyword, selector): #(n_intervals) pro auto update
    selected_time_datetime = datetime.datetime.fromtimestamp(selected_time/1000000000).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    #print("twitter chart update, selected time=",selected_time_datetime)
    cnx = mysql.connector.connect(user=kody.mysql_username, password=kody.mysql_password,
                                  host='localhost',
                                  database='twitter',
                                  charset = 'utf8')    
    df_filtered = pd.read_sql('SELECT created_at, sentiment_textblob, volume, sentiment_vader FROM '+ keyword +' WHERE created_at >= "'+selected_time_datetime+'"ORDER BY created_at ASC', con=cnx)
    df_filtered = df_filtered.set_index(["created_at"])
    df_filtered["ma_short"] = df_filtered.sentiment_textblob.rolling(window=10).mean()
    df_filtered["ma_long"] = df_filtered.sentiment_textblob.rolling(window=100).mean()
    df_filtered["vader_ma_short"] = df_filtered.sentiment_vader.rolling(window=10).mean()
    df_filtered["vader_ma_long"] = df_filtered.sentiment_vader.rolling(window=100).mean()    
    df_filtered['epoch'] = df_filtered.index.astype(np.int64)
    df_volume_filtered = df_filtered.resample('30min').agg({'volume': np.sum})
    df_volume_filtered["epoch"] =  df_volume_filtered.index.astype(np.int64)
    #df_volume["MA"] = df_volume.volume.rolling(window=100).mean()
    #df_filtered = df[df.epoch > selected_time]
    #df_volume = get_data_twitter_volume(keyword)
    #df_volume_filtered = df_volume[df_volume.epoch > selected_time]
    fig = make_subplots(rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0, #to když se změní tak nefunguje row_heights
            row_heights=[0.8, 0.2],
            )
    if "sentiment_textblob" in selector:    
        scatter = go.Scatter(x=df_filtered.index, y=df_filtered["sentiment_textblob"],marker_color="#ff8000", mode="markers", name="Sentiment TextBlob", marker={"size":4}, text=df_filtered["title"]) #*
        fig.append_trace(scatter, 1, 1)
    if "sentiment_vader" in selector:    
        scatter = go.Scatter(x=df_filtered.index, y=df_filtered["sentiment_vader"],marker_color="#ff0000", mode="markers", name="Sentiment Vader", marker={"size":4}, text=df_filtered["title"]) #*
        fig.append_trace(scatter, 1, 1)
    if "short_ma" in selector:
        short_ma = go.Scatter(x=df_filtered.index, y=df_filtered["ma_short"],line_color="#ffff00", mode="lines", name="Short MA TextBlob")
        fig.append_trace(short_ma, 1, 1)
    if "long_ma" in selector: 
        long_ma = go.Scatter(x=df_filtered.index, y=df_filtered["ma_long"], line_color="#00ffff", mode="lines", name="Long MA TextBlob")
        fig.append_trace(long_ma, 1, 1)
    if "vader_ma_short" in selector:
        vader_ma_short = go.Scatter(x=df_filtered.index, y=df_filtered["vader_ma_short"], line_color="#8000ff", mode="lines", name="10 news MA Vader")
        fig.append_trace(vader_ma_short, 1, 1)
    if "vader_ma_long" in selector:    
        vader_ma_long = go.Scatter(x=df_filtered.index, y=df_filtered["vader_ma_long"], line_color="#ff007f", mode="lines", name="30 news MA Vader")          
        fig.append_trace(vader_ma_long, 1, 1)
    volume = go.Bar(x=df_volume_filtered.index, y=df_volume_filtered["volume"], marker_color="#ff8000", name="2m Volume", text = df_volume_filtered["volume"])
    fig.append_trace(volume, 2, 1)
    #volume_MA = go.Scatter(x=df_filtered.index, y=df_filtered["MA"], fill="tozeroy", mode="none", fillcolor="rgba(255, 128, 0, 0.4)", name="Volume MA 1O")
    #fig.append_trace(volume_MA, 2, 1)

    fig["layout"].update(#title_text="test",
                        template="plotly_dark", 
                        legend_title_text="", 
                        legend_orientation="h", 
                        legend=dict(x=0, y=-0.13),
                        transition_duration=0,
                        margin=dict(l=0, r=0, t=20, b=0),
                        paper_bgcolor="black",
                        plot_bgcolor="black",
                        title={
                            "yref": "paper",
                            "y" : 1,
                            "x" : 0.5,
                            "yanchor" : "bottom"},
                            )
    #print("Pocet tweetu v db: ", len(data_frame["time"]))
    return fig

#--------------------callback pro update hodnoty slider_value-tweetTable-----------------
@app.callback(Output('year-slider-value-tweetTable', 'children'),
                [Input("year-slider-tweetTable", "drag_value")
                ])
def slider_twitter(drag_value):
    if drag_value == None:  #first load == None
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        drag_value_datetime = yesterday.strftime("%Y-%m-%d %H:%M:%S")
    else:
        drag_value_datetime = datetime.datetime.fromtimestamp(drag_value/1000000000).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    return 'Slider Value: {}'.format(drag_value_datetime)

#--------------------callback pro update tabulky z MySQL tweetTable---------------------
@app.callback(Output('table', 'data'),
              [#Input('interval-component-chart', 'n_intervals'),
              Input('twitter-dropdown', 'value'),
              Input('table_checklist', 'value'),
              ])            
def update_table(keyword, selector): #(n_intervals) pro auto update
    cnx = mysql.connector.connect(user=kody.mysql_username, password=kody.mysql_password,
                                  host='localhost',
                                  database='twitter',
                                  charset = 'utf8')
    if keyword == "tweetTable_resampled_5m":
        keyword = "tweetTable"
    if keyword == "tweetTable_AR_NET_rt":
        keyword = "tweetTable_AR_NET"    
    if keyword == "tweetTable_AR_ORCL_rt":
        keyword = "tweetTable_AR_ORCL"
    if keyword == "tweetTable_AR_PFE_rt":
        keyword = "tweetTable_AR_PFE"
    if keyword == "tweetTable_AR_RACE_rt":
        keyword = "tweetTable_AR_RACE"
    if "last_day" in selector:
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        yesterday = yesterday.strftime("%Y-%m-%d %H:%M:%S")        
        df = pd.read_sql('SELECT * FROM '+ keyword +' WHERE created_at >= "'+yesterday+'" ORDER BY created_at ASC', con=cnx).to_dict('records') #aby fungovalo data_frame.resample
    if "all_tweets" in selector:
        df = pd.read_sql('SELECT * FROM '+ keyword +' ORDER BY created_at ASC', con=cnx).to_dict('records')
    return df

#================================================================================================================


#--------------------callback pro update tabulky z MySQL newsGILD-----------------------
@app.callback(Output('table_newsGILD', 'data'),
             [Input('news-dropdown', 'value'), #callback pro dropdown
              Input('interval-component-newsGILD', 'n_intervals')])
def update_table_gild(news, n_interval):
    df = get_data_news(news).sort_index(ascending=False)#nejdřív seřadím pro default sort v datatablu
    df = df.reset_index().rename(columns={df.index.name:'published'}) #protože index nejde zobrazit v datatablu
    print("news table update")
    return df.to_dict('records')

#--------------------callback pro update grafu z MYSQL newsGILD-------------------------
@app.callback(
    Output('chart-with-slider-news', 'figure'),
    [Input('year-slider-news', 'value'), #callback pro chart slider
     Input('interval-component-news-chart','n_intervals'), #callbak pro update grafu
     Input('news-dropdown', 'value'), #callback pro dropdown
     Input('checklist_gild', 'value')]) #callback pro checklist
def update_news_figure(selected_time, n_interval, keyword, selector):
    selected_time_datetime = datetime.datetime.fromtimestamp(selected_time/1000000000).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    print("news chart update")
    cnx = mysql.connector.connect(user=kody.mysql_username, password=kody.mysql_password,
                                  host='localhost',
                                  database='twitter',
                                  charset = 'utf8')
    df_filtered = pd.read_sql('SELECT source, published, title, url, sentiment, sentiment_vader FROM '+ keyword +' WHERE published >= "'+selected_time_datetime+'" ORDER BY published ASC', con=cnx)
    df_filtered = df_filtered.set_index(['published'])
    df_filtered["ma_short"] = df_filtered.sentiment.rolling(window=10).mean()
    df_filtered["ma_long"] = df_filtered.sentiment.rolling(window=30).mean()
    df_filtered["vader_ma_short"] = df_filtered.sentiment_vader.rolling(window=10).mean()
    df_filtered["vader_ma_long"] = df_filtered.sentiment_vader.rolling(window=30).mean()
    df_filtered['epoch'] = df_filtered.index.astype(np.int64)
    df_filtered["volume"] = 1
    links = df_filtered['url'].to_list()
    rows = []
    for x in links:
        link = '[link](' +str(x) + ')'
        rows.append(link)#
    df_filtered['url'] = rows
    df_volume_filtered = df_filtered.resample('30min').agg({'volume': np.sum})
    df_volume_filtered["epoch"] =  df_volume_filtered.index.astype(np.int64)
    #df_volume = get_data_news(table_name).resample('720min').agg({'volume': np.sum, 'sentiment': np.mean,'sentiment_vader': np.mean})
    #df_volume["epoch"] =  df_volume.index.astype(np.int64)
    df_volume_filtered["MA"] = df_volume_filtered.volume.rolling(window=10).mean()
    #df_volume_filtered = df_volume[df_volume.epoch > selected_time]
    #df_filtered_scatter = df.tail(1000) #zobrazí posledních n-tweetů v grafu jako body*
    fig = make_subplots(rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0, #to když se změní tak nefunguje row_heights
            row_heights=[0.8, 0.2],
            )
    if "sentiment_textblob" in selector:    
        scatter = go.Scatter(x=df_filtered.index, y=df_filtered["sentiment"],marker_color="#ff8000", mode="markers", name="Sentiment TextBlob", marker={"size":4}, text=df_filtered["title"]) #*
        fig.append_trace(scatter, 1, 1)
    if "sentiment_vader" in selector:    
        scatter = go.Scatter(x=df_filtered.index, y=df_filtered["sentiment_vader"],marker_color="#ff0000", mode="markers", name="Sentiment Vader", marker={"size":4}, text=df_filtered["title"]) #*
        fig.append_trace(scatter, 1, 1)
    if "short_ma" in selector:
        short_ma = go.Scatter(x=df_filtered.index, y=df_filtered["ma_short"],line_color="#ffff00", mode="lines", name="Short MA TextBlob")
        fig.append_trace(short_ma, 1, 1)
    if "long_ma" in selector: 
        long_ma = go.Scatter(x=df_filtered.index, y=df_filtered["ma_long"], line_color="#00ffff", mode="lines", name="Long MA TextBlob")
        fig.append_trace(long_ma, 1, 1)
    if "vader_ma_short" in selector:
        vader_ma_short = go.Scatter(x=df_filtered.index, y=df_filtered["vader_ma_short"], line_color="#8000ff", mode="lines", name="10 news MA Vader")
        fig.append_trace(vader_ma_short, 1, 1)
    if "vader_ma_long" in selector:    
        vader_ma_long = go.Scatter(x=df_filtered.index, y=df_filtered["vader_ma_long"], line_color="#ff007f", mode="lines", name="30 news MA Vader")          
        fig.append_trace(vader_ma_long, 1, 1)
    volume = go.Bar(x=df_volume_filtered.index, y=df_volume_filtered["volume"], marker_color="#ff8000", name="12h Volume", text = df_volume_filtered["volume"])
    fig.append_trace(volume, 2, 1)
    volume_MA = go.Scatter(x=df_volume_filtered.index, y=df_volume_filtered["MA"], fill="tozeroy", mode="none", fillcolor="rgba(255, 128, 0, 0.4)", name="Volume MA 1O")
    fig.append_trace(volume_MA, 2, 1)

    fig["layout"].update(#title_text=news,
                        template="plotly_dark", 
                        legend_title_text="", 
                        legend_orientation="h", 
                        legend=dict(x=0, y=-0.13),
                        transition_duration=0,
                        margin=dict(l=0, r=0, t=20, b=0),
                        paper_bgcolor="black",
                        plot_bgcolor="black",
                        title={
                            "yref": "paper",
                            "y" : 1,
                            "x" : 0.5,
                            "yanchor" : "bottom"},
                            )
    #print("Pocet tweetu v db: ", len(data_frame["time"]))
    return fig

#--------------------callback pro update hodnoty slider_value-news----------------------
@app.callback(Output('year-slider-value-news', 'children'),
                [Input("year-slider-news", "drag_value")
                ])
def slider_news(drag_value):
    if drag_value == None:  #first load == None
        yesterday = datetime.datetime.now() - datetime.timedelta(days=10)
        drag_value_datetime = yesterday.strftime("%Y-%m-%d %H:%M:%S")
    else:
        drag_value_datetime = datetime.datetime.fromtimestamp(drag_value/1000000000).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    return 'Slider Value: {}'.format(drag_value_datetime)

#--------------------callback pro update tabulky z MySQL running_scripts----------------
@app.callback(dash.dependencies.Output('table_running_scripts', 'data'),
              [dash.dependencies.Input('interval-component-iir', 'n_intervals')])
def update_is_it_running(n_intervals):
    now_minus_one_hour = dt.now() - relativedelta(hours=1)
    data_frame_is_it_running = pd.read_sql('SELECT script, time FROM running_scripts ORDER BY time ASC', con=kody.cnx)
    data_frame_is_it_running["status"] = np.where(data_frame_is_it_running["time"] > now_minus_one_hour, "YES","NO")
    data_frame_is_it_running = data_frame_is_it_running.to_dict('records')
    return data_frame_is_it_running

#--------------------callback pro update wordcloudu newsGILD----------------------------
@app.callback(Output("wordcloud_news", "src"),
             [Input("news-dropdown", "value")])
def update_body_image(news):
    src = "/assets/wordcloud_"+news+".svg"
    return src

#================================================================================================================

#--------------------callback pro update tabulky z MySQL redditGILD-----------------------
@app.callback(Output('table_redditGILD', 'data'),
             [Input('reddit-dropdown', 'value'), #callback pro dropdown
              Input('interval-component-redditGILD', 'n_intervals')])
def update_table_reddit(reddit, n_interval):
    df = get_data_reddit(reddit).sort_index(ascending=False)#nejdřív seřadím pro default sort v datatablu
    df = df.reset_index().rename(columns={df.index.name:'time'}) #protože index nejde zobrazit v datatablu
    print("news table update")
    return df.to_dict('records')

#--------------------callback pro update grafu z MYSQL redditGILD-------------------------
@app.callback(
    Output('chart-with-slider-reddit', 'figure'),
    [Input('year-slider-reddit', 'value'), #callback pro chart slider
     Input('interval-component-reddit-chart','n_intervals'), #callbak pro update grafu
     Input('reddit-dropdown', 'value'), #callback pro dropdown
     Input('checklist_gild', 'value')]) #callback pro checklist
def update_reddit_figure(selected_time, n_interval, reddit, selector):
    print("reddit chart update")
    df = get_data_reddit(reddit)
    df_volume = get_data_reddit_volume(reddit)
    df_filtered = df[df.epoch > selected_time]
    df_volume_filtered = df_volume[df_volume.epoch > selected_time]
    #df_filtered_scatter = df.tail(1000) #zobrazí posledních n-tweetů v grafu jako body*
    fig = make_subplots(rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0, #to když se změní tak nefunguje row_heights
            row_heights=[0.8, 0.2],
            )
    if "sentiment_textblob" in selector:    
        scatter = go.Scatter(x=df_filtered.index, y=df_filtered["sentiment_textblob"],marker_color="#ff8000", mode="markers", name="Sentiment TextBlob", marker={"size":4}, text=df_filtered["topic_comment"]) #*
        fig.append_trace(scatter, 1, 1)
    if "sentiment_vader" in selector:    
        scatter = go.Scatter(x=df_filtered.index, y=df_filtered["sentiment_vader"],marker_color="#ff0000", mode="markers", name="Sentiment Vader", marker={"size":4}, text=df_filtered["topic_comment"]) #*
        fig.append_trace(scatter, 1, 1)
    if "short_ma" in selector:
        short_ma = go.Scatter(x=df_filtered.index, y=df_filtered["ma_short"],line_color="#ffff00", mode="lines", name="Short MA TextBlob")
        fig.append_trace(short_ma, 1, 1)
    if "long_ma" in selector: 
        long_ma = go.Scatter(x=df_filtered.index, y=df_filtered["ma_long"], line_color="#00ffff", mode="lines", name="Long MA TextBlob")
        fig.append_trace(long_ma, 1, 1)
    if "vader_ma_short" in selector:
        vader_ma_short = go.Scatter(x=df_filtered.index, y=df_filtered["vader_ma_short"], line_color="#8000ff", mode="lines", name="10 reddit MA Vader")
        fig.append_trace(vader_ma_short, 1, 1)
    if "vader_ma_long" in selector:    
        vader_ma_long = go.Scatter(x=df_filtered.index, y=df_filtered["vader_ma_long"], line_color="#ff007f", mode="lines", name="30 reddit MA Vader")          
        fig.append_trace(vader_ma_long, 1, 1)
    volume = go.Bar(x=df_volume_filtered.index, y=df_volume_filtered["volume"], marker_color="#ff8000", name="12h Volume", text = df_volume_filtered["volume"])
    fig.append_trace(volume, 2, 1)
    volume_MA = go.Scatter(x=df_volume_filtered.index, y=df_volume_filtered["MA"], fill="tozeroy", mode="none", fillcolor="rgba(255, 128, 0, 0.4)", name="Volume MA 1O")
    fig.append_trace(volume_MA, 2, 1)

    fig["layout"].update(title_text=reddit,
                        template="plotly_dark", 
                        legend_title_text="", 
                        legend_orientation="h", 
                        legend=dict(x=0, y=-0.13),
                        transition_duration=0,
                        margin=dict(l=0, r=0, t=20, b=0),
                        paper_bgcolor="black",
                        plot_bgcolor="black",
                        title={
                            "yref": "paper",
                            "y" : 1,
                            "x" : 0.5,
                            "yanchor" : "bottom"},
                            )
    #print("Pocet tweetu v db: ", len(data_frame["time"]))
    return fig

#================================================================================================================

#--------------------twitter callback pro update "Database contains ... rows"-------------------
@app.callback(Output("count-tweetTable", "children"),
             [Input('twitter-dropdown', 'value'),
              Input("interval-component-count-tweetTable", "n_intervals")])
def count_row(keyword, n_intervals):
    cnx = mysql.connector.connect(user=kody.mysql_username, password=kody.mysql_password,
                                  host='localhost',
                                  database='twitter',
                                  charset = 'utf8')
    cursor = cnx.cursor()
    if keyword == "tweetTable_resampled_5m":
        keyword = "tweetTable"
    if keyword == "tweetTable_AR_NET_rt":
        keyword = "tweetTable_AR_NET"    
    if keyword == "tweetTable_AR_ORCL_rt":
        keyword = "tweetTable_AR_ORCL"
    if keyword == "tweetTable_AR_PFE_rt":
        keyword = "tweetTable_AR_PFE"
    if keyword == "tweetTable_AR_RACE_rt":
        keyword = "tweetTable_AR_RACE"
    cursor.execute("""
                   SELECT COUNT(*) 
                   FROM """+ keyword +""";
                   """
                   )
    count = str(cursor.fetchone()[0])
    p = "Database contains "
    p3 = " rows "
    info = "".join([p,count,p3])
    return info

#--------------------news callback pro update "Database contains ... rows"-------------------
@app.callback(Output("count-news", "children"),
             [Input('news-dropdown', 'value'),
              Input("interval-component-count", "n_intervals")])
def count_row(news, n_intervals):
    cnx = mysql.connector.connect(user=kody.mysql_username, password=kody.mysql_password,
                                  host='localhost',
                                  database='twitter',
                                  charset = 'utf8')
    cursor = cnx.cursor()
    cursor.execute("""
                   SELECT COUNT(*) 
                   FROM """+ news +""";
                   """
                   )
    count = str(cursor.fetchone()[0])
    cursor.execute("""SELECT published FROM """+ news +""" ORDER BY published ASC LIMIT 1""")
    cursor.close
    for firstrow in cursor.fetchall():
        firstresult = firstrow
    datetime_from = firstresult[0].strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""SELECT published FROM """+ news +""" ORDER BY published DESC LIMIT 1""")
    for lastrow in cursor.fetchall():
        lastresult = lastrow
    datetime_to = lastresult[0].strftime('%Y-%m-%d %H:%M:%S')
    p = "Database contains "
    p3 = " rows "
    datetime_fromtext = "Since: "
    datetime_totext = " Until: "
    info = "".join([p,count,p3,datetime_fromtext,datetime_from,datetime_totext,datetime_to])
    return info

#--------------------reddit callback pro update "Database contains ... rows"-------------------
@app.callback(Output("count-reddit", "children"),
             [Input('reddit-dropdown', 'value'),
              Input("interval-component-count", "n_intervals")])
def count_row(news, n_intervals):
    cursor=kody.cnx.cursor()
    cursor.execute("""
                   SELECT COUNT(*) 
                   FROM """+ news +""";
                   """
                   )
    count = str(cursor.fetchone()[0])
    p = "Database contains "
    p3 = " rows "
    info = "".join([p,count,p3])
    return info

if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0")
