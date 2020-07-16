import multidict as multidict

import numpy as np
import pandas as pd
import kody

import os
import re
from PIL import Image
from os import path
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from plotly.tools import mpl_to_plotly
import random
import time

def grey_color_func(word, font_size, position, orientation, random_state=None,
                    **kwargs):
    return "hsl(30, 0%%, %d%%)" % random.randint(60, 100)

def get_data(table_name):
    #table_name="tweetTable"
    data_xrp = pd.read_sql('SELECT title FROM '+ table_name +' ORDER BY time ASC', con=kody.cnx)
    return data_xrp


def getFrequencyDictForText(sentence):
    fullTermsDict = multidict.MultiDict()
    tmpDict = {}

    # making dict for counting frequencies
    for text in sentence.split(" "):
        if re.match("rt|stock|gilead|a|the|an|the|to|in|for|of|or|by|with|is|on|that|be", text):
            continue
        val = tmpDict.get(text, 0)
        tmpDict[text.lower()] = val + 1
    for key in tmpDict:
        fullTermsDict.add(key, tmpDict[key])
    return fullTermsDict


def makeImage(text):
    alice_mask = np.array(Image.open("newspaper_mask.png"))

    wc = WordCloud(background_color="black", margin = 0, max_words=1000, mask=alice_mask)
    # generate word cloud
    wc.generate_from_frequencies(text)

    # show
    plt.imshow(wc.recolor(color_func=grey_color_func, random_state=3), interpolation="bilinear")
    plt.axis("off")
    plt.savefig("assets/wordcloud_news_gild", dpi = 150, bbox_inches='tight',facecolor='black', edgecolor='black')

while True:
    tweets_list = ' '.join(get_data("newsGILD")["title"].tolist())
    text = tweets_list
    makeImage(getFrequencyDictForText(text))
    time.sleep(15)