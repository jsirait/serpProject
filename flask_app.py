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
    candidates = mycursor.fetchall()
    print(candidates)

    mycursor.execute("select count(*) from thirtyCandidates;")
    totalArticlesNum = mycursor.fetchall()[0][0]

    # print(str(candidates))

    for tuples in candidates:
        candidateName = tuples[0]
        # seeing how many time that query appears = how many articles there are
        mycursor.execute(
            "SELECT COUNT(title) FROM thirtyCandidates WHERE query = (%s)", (candidateName,)
        )
        articleNum = mycursor.fetchall()
        cand_articleNum_dict[candidateName] = articleNum[0][0] # to accomodate how data is fetched
        print("Data for graph 0 has been processed!")

    # print(str(cand_articleNum_dict))

    keys = [i for i in cand_articleNum_dict.keys()]
    values = [j for j in cand_articleNum_dict.values()]

    # --- making bar chart or scatter graph of domains and their frequencies ---

    sourceFrequency = {} # source : domain, count or maybe just count?
    instruction = "select source, count(*) from thirtyCandidates group by source"
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
    # --- making heatmap of candidates and number of articles about them ---

    '''
        Returns the list [x, y, z] value for the heatmap to be created.
        So in this case, [[1:11], [3 news sources], [corresponding frequencies]]
    '''
    def heatmappy(kandidat):
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
            print(hold)
        return [[i for i in range(1,11)], hm_sourcesList, forz]

    # ^^^ works but takes so much time to run ...


    # ----------------------------------------------------------------------
    # --- making '5 Top News Source talking about a candidate' bar graph ---
    def topns(tn_candidate):
        tn_sourceFreq = {}
        mycursor.execute("select source,count(*) as count from thirtyCandidates where query=(%s) group by source order by count desc limit 5;",
                (tn_candidate,)) # choosing 5 top sources
        fetched = mycursor.fetchall()
        for tuples in fetched:
            source = tuples[0]
            freq = tuples[1]
            tn_sourceFreq[source] = freq

        # mycursor.execute("select count(title) from thirtyCandidates where query=(%s);",(tn_candidate))
        # fetched0 = mycursor.fetchall()

        tn_source = [ii for ii in tn_sourceFreq.keys()]
        tn_freqs = [jj for jj in tn_sourceFreq.values()]

        mycursor.execute("select party,state,current_occupation from candidates where name=(%s);",(tn_candidate,))
        temp = mycursor.fetchall()
        if len(temp) == 0:
            return [None,None,None,None,None,None]
        else:
            fetched1=temp[0]
        # print(fetched1)
        return [tn_source,tn_freqs,fetched1[0],fetched1[1],fetched1[2],cand_articleNum_dict[tn_candidate]]


    # have not closed mydb and mycursor

except IOError as e:
    print(e)

@app.route('/')
def index():

    graphs = [
        dict(
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
                title='Total Number of Articles'
            )
        ),

        dict(
            data=[
                dict(
                    x=source,
                    y=freqs,
                    type='scatter',
                    marker=[dict(line=dict(color='brickred'))]
                )
            ],
            layout={
                "title":"Freqs of News Source"
            }
        )
    ]

    # Add "ids" to each of the graphs to pass up to the client
    # for templating
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    # print(graphJSON)

    return render_template('index.html',
                           ids=ids,
                           graphJSON=graphJSON)

@app.route('/heatmap', methods=['GET', 'POST'])
def createHeatmap():
    currentCandidate = "Bernie Sanders"
    candidateList = [ii[0] for ii in candidates]
    # print(candidateList[:5])
    if request.method == 'POST':
        currentCandidate = request.form['cands']
    hmap_data = heatmappy(currentCandidate)
    # print(hmap_data[1])
    return render_template('heatmap.html', hmap_data=hmap_data, candidateList=candidateList,
        currentCandidate=currentCandidate)

@app.route('/demo')
def demo():
    return render_template('demo.html')

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
                title="5 top news sources"
            )
        )
    party = "Democrat" if sc_data[2] == 0 else "Republican"
    state = sc_data[3]
    occupation = sc_data[4]
    return render_template('specificCandidate.html', username=username, graph=graph,
        party=party, state=state, occupation=occupation, num_articles=sc_data[5], totalArticlesNum=totalArticlesNum)

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
