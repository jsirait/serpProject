from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import pymysql

import json
import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np

import random

app = Flask(__name__)
app.debug = True
bootsrap = Bootstrap(app)

# PcRoYpry3JEMWa3

cand_articleNum_dict = {} # candidateName : articleNumber

try:
    mydb = pymysql.connect(
        host = "jsirait.mysql.pythonanywhere-services.com",
        user = "jsirait",
        password = "midnightjasmine",
        database = "jsirait$election2020"
        )

    # --- making bar chart candidates and # of articles ---

    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT DISTINCT QUERY FROM thirtyCandidates;"
    )
    candidates = [aa[0] for aa in mycursor.fetchall()]

    mycursor.execute("select count(*) from thirtyCandidates;")
    totalArticlesNum = mycursor.fetchall()[0][0]

    # print(str(candidates))

    for candidateName in candidates:
        # seeing how many time that query appears = how many articles there are
        mycursor.execute(
            "SELECT COUNT(distinct query,URL) FROM thirtyCandidates WHERE query = (%s)", (candidateName,)
        )
        articleNum = mycursor.fetchall()
        cand_articleNum_dict[candidateName] = articleNum[0][0] # to accomodate how data is fetched

    # print(str(cand_articleNum_dict))

    # keys = [i for i in cand_articleNum_dict.keys()]
    # values = [j for j in cand_articleNum_dict.values()]
    flist = [(k,v) for k,v in cand_articleNum_dict.items()]
    flist.sort(key=lambda x:x[1], reverse=True)
    keys = [i[0] for i in flist]
    values=[i[1] for i in flist]

    # --- making bar chart or scatter graph of domains and their frequencies ---

    sourceFrequency = {} # domain : count or maybe just count?
    instruction = "select domain, count(distinct query,URL) as c from thirtyCandidates group by domain order by c desc limit 25;"
    mycursor.execute(instruction)
    sources = mycursor.fetchall()


    # print(str(sources)) ('WSHU', 26)

    for tuples in sources:
        source = tuples[0]
        freq = tuples[1]
        sourceFrequency[source] = freq

    source = [ii for ii in sourceFrequency.keys()]
    freqs = [jj for jj in sourceFrequency.values()]

    # ----------------------------------------------------------------------
    # -- making heatmap of prob. article from a news source in position x --
    # ----------------------------------------------------------------------

    top_tier_1 = list(sourceFrequency.items())
    # print(top_tier_1)
    top_tier = [ii[0] for ii in top_tier_1[:8]]

    fin = {}

    for pNewsSource in top_tier:
        likelihoods = [0,0,0,0,0,0,0,0,0,0]
        for ii in range(0,10):
            mycursor.execute("select count(URL) from thirtyCandidates where domain=(%s) and story_position=(%s);",(pNewsSource,ii+1))
            numObserved = mycursor.fetchall()[0][0]
            mycursor.execute("select count(URL) from thirtyCandidates where story_position=(%s);",(ii+1,))
            totalObserved = mycursor.fetchall()[0][0]
            llhood = round((numObserved/totalObserved),2)
            likelihoods[ii]=llhood
        fin[pNewsSource]=likelihoods
    mycursor.close()
    mydb.close()
    fin1 = list(fin.items())
    hforz = [ii[1] for ii in fin1]
    hfory = [ii[0] for ii in fin1]


except IOError as e:
    print(e)


# ---------------------------
# | making heatmap (tryout) |
# ---------------------------
    '''
        Returns the list [x, y, z] value for the heatmap to be created.
        So in this case, [[1:11], [3 news sources], [corresponding frequencies]]
    '''
def heatmappy(kandidat):
    try:
        mydb = pymysql.connect(
            host = "jsirait.mysql.pythonanywhere-services.com",
            user = "jsirait",
            password = "midnightjasmine",
            database = "jsirait$election2020"
            )

        mycursor = mydb.cursor()
        # based on news source ---
        # hm_instruction = "select source, position, count(*) from thirtyCandidates where query = (%s) group by source, position;"
        hm_sourcesList = []
        hm_candidate = kandidat
        hm1 = mycursor.execute("select distinct source from thirtyCandidates where query = (%s) limit 3",
                (hm_candidate)) # choosing 3 random sources
        hm_sourcesTuples = mycursor.fetchall()

        # then we iterate through all possible news source and see how many there are for each position
        forz = []
        hold = 0
        for aa in hm_sourcesTuples:
            hold+=1
            sourceCount = []
            hm_sourcesList.append(aa[0])
            for position in range(1,11):
                hm3 = mycursor.execute("select count(*) from thirtyCandidates where query = (%s) and source = (%s) and position = (%s)",
                (hm_candidate, aa[0], position))
                count = mycursor.fetchall()
                sourceCount.append(count[0][0])
            forz.append(sourceCount)
            # print(hold)
        mycursor.close()
        mydb.close()
        return [[i for i in range(1,11)], hm_sourcesList, forz]
    except IOError as e:
        print(e)

    # ^^^ works but takes so much time to run ...


    # ----------------------------------------------------------------------
    # |   making '10 Top News Source talking about a candidate' bar graph   |
    # ----------------------------------------------------------------------
def topns(tn_candidate):
    try:
        mydb = pymysql.connect(
            host = "jsirait.mysql.pythonanywhere-services.com",
            user = "jsirait",
            password = "midnightjasmine",
            database = "jsirait$election2020"
        )

    # --- making bar chart candidates and # of articles ---

        mycursor = mydb.cursor()
        tn_sourceFreq = {}
        mycursor.execute("select domain,count(*) as count from thirtyCandidates where query=(%s) group by domain order by count desc limit 10;",
                (tn_candidate,)) # choosing 5 top sources
        fetched = mycursor.fetchall()
        for tuples in fetched:
            source = tuples[0]
            freq = tuples[1]
            tn_sourceFreq[source] = freq

        tn_source = [ii for ii in tn_sourceFreq.keys()]
        tn_freqs = [jj for jj in tn_sourceFreq.values()]

        mycursor.execute("select party,state,current_occupation, photo_link from candidates where name=(%s);",(tn_candidate,))
        temp = mycursor.fetchall()
        if len(temp) == 0:
            return [None,None,None,None,None,"#",None]
        else:
            fetched1=temp[0]
        # print(fetched1)
        mycursor.close()
        mydb.close()
        return [tn_source,tn_freqs,fetched1[0],fetched1[1],fetched1[2],fetched1[3],cand_articleNum_dict[tn_candidate]]
    except IOError as e:
        print(e)

#--------------------------------------------
#| making box plot for individual candidate |
#--------------------------------------------
def bp(bp_candidate):
    try:
        mydb = pymysql.connect(
            host = "jsirait.mysql.pythonanywhere-services.com",
            user = "jsirait",
            password = "midnightjasmine",
            database = "jsirait$election2020"
        )
        mycursor = mydb.cursor()
        mycursor.execute("select freshness_in_mins from thirtyCandidates where freshness_in_mins IS NOT NULL and freshness_in_mins < 45000 and query=(%s)",
            (bp_candidate,))
        bp_temp = mycursor.fetchall()
        freshness = [element[0] for element in bp_temp]
        mycursor.close()
        mydb.close()
        return freshness
    except IOError as e:
        print(e)

#----------------------------------------------------------------------------------
#| Creating a heatmap presenting probability an article from a news source appears|
#| in a particular position                                                       |
#----------------------------------------------------------------------------------

def pHeatmap():
    '''
        Returns a dictionary mapping the news source names as keys to a list
        containing 10 elements representing the likelihood that given position X
        (1-10), we see article form that news source there.
    '''
    try:
        mydb = pymysql.connect(
            host = "jsirait.mysql.pythonanywhere-services.com",
            user = "jsirait",
            password = "midnightjasmine",
            database = "jsirait$election2020"
        )
        mycursor = mydb.cursor()
        fin = {}

        for pNewsSource in top_tier:
            likelihoods = [0,0,0,0,0,0,0,0,0,0]
            for ii in range(0,10):
                mycursor.execute("select count(URL) from thirtyCandidates where domain=(%s) and story_position=(%s);",(pNewsSource,ii+1))
                numObserved = mycursor.fetchall()[0][0]
                mycursor.execute("select count(URL) from thirtyCandidates where story_position=(%s);",(ii+1,))
                totalObserved = mycursor.fetchall()[0][0]
                llhood = round((numObserved/totalObserved),2)
                likelihoods[ii]=llhood
            fin[pNewsSource]=likelihoods
        mycursor.close()
        mydb.close()
        fin1 = list(fin.items())
        pforz = [ii[1] for ii in fin1]
        pfory = [ii[0] for ii in fin1]
        return (pfory,pforz)
    except IOError as e:
        print(e)


@app.route('/')
def index():
    graphs2 = dict(
            data=[
                dict(
                    x=keys,
                    y=values,
                    type='bar',
                    marker=dict(
                        color='rgb(142,124,195)'
                    )
                )
            ],
            layout=dict(
                yaxis = dict(title="Number of articles")
            )
        )

    graphs3 = dict(
            data=[
                dict(
                    x=source,
                    y=freqs,
                    type='bar',
                    marker=dict(
                        color='rgb(142,124,195)'
                        )
                )
            ],
            layout=dict(
                xaxis = dict(automargin="true",tickangle='45'),
                yaxis = dict(title="Number of articles")
            )
        )

    graphs4 = dict(
            data=[
                dict(
                    z=hforz,
                    x=[1,2,3,4,5,6,7,8,9,10],
                    y=hfory,
                    colorscale='Greens',
                    type='heatmap'
                )
            ],
            layout=dict(
                annotations=[]
            )
        )

    return render_template('index.html',
                           graphs2=graphs2,
                           graphs3 = graphs3,
                          graphs4 = graphs4,
                           candidateNames = candidates,
                           top_tier = top_tier)

# @app.route('/heatmap', methods=['GET', 'POST'])
# def createHeatmap():
#     currentCandidate = "Bernie Sanders"
#     candidateList = [ii[0] for ii in candidates]
#     # print(candidateList[:5])
#     if request.method == 'POST':
#         currentCandidate = request.form['cands']
#     hmap_data = heatmappy(currentCandidate)
#     # print(hmap_data[1])
#     return render_template('heatmap.html', hmap_data=hmap_data, candidateList=candidateList,
#         currentCandidate=currentCandidate)

@app.route('/<username>')
def specCand(username):
    # username = random.choice(candidates)[0]
    print("Processing for",username)
    sc_data = topns(username)
    graph = dict(
            data=[
                dict(
                    x=sc_data[0],
                    y=sc_data[1],
                    type='bar',
                    marker=dict(
                        color='rgb(142,124,195)'
                    )
                )
            ],
            layout=dict(
                title="10 top news sources",
                xaxis = dict(title="News sources"),
                yaxis = dict(title="Number of (non-distinct) articles collected")
            )
        )
    party = "Democrat" if sc_data[2] == 0 else "Republican"
    state = sc_data[3]
    occupation = sc_data[4]
    photo_link = sc_data[5]

    bp_data = bp(username)
    graph1 = dict(
            data=[
                dict(
                    x=bp_data,
                    type='box'
                    )
            ],
            layout=dict(
                title="Distribution of the freshness of news articles",
                xaxis = dict(title="Freshness in minutes")
            )
        )
    return render_template('specificCandidate.html', username=username, graph=graph,
        party=party, state=state, occupation=occupation, num_articles=sc_data[6], totalArticlesNum=totalArticlesNum,
        graph1 = graph1, photo_link = photo_link)

if __name__ == '__main__':
    app.run(port=9990)


"""
    NOTES:
    1. Data are collected every 6 hours, from 15 Dec 2018 to 10 July 2019
    2. There are 24 candidates.
    3. There are 2410 distinct sources.

    Graphs drawn:
    1. Bar graph to represent name of candidates - number of articles
        on them.
    2.  A Scatter plot (?) or bar graph of the distinct news sources and domains
        and how many times they show up --> not very pretty
    3.  Heat map, x= position (1-10), y= news sources (only 4 for now, not speedy),
        saturation= number of articles from that news source about that candidate.
        AMY KLOBUCHAR.

    Next:
    1. Find way to change graph title as we update it
    2. Find way for selected candidate name to stick on the drop-down menu default
        value.

"""
