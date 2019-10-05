#!/usr/bin/env python
# coding: utf-8
import pandas as pd
from rake_nltk import Rake
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from surprise import Reader, Dataset, SVD, evaluate
import os
from movies.models import *
from easyRec.utils import *

data_path=os.path.abspath('datasets/movie_data.csv')
rating_path=os.path.abspath('datasets/movie_ratings.csv')

def get_movie_details(title):
    qSet=Movie.objects.filter(movie_title=title)
    qSet=qSet[0]
    ans={}
    ans['movie_title']=qSet.movie_title
    ans['movie_id']=qSet.movie_id
    ans['movie_plot']=qSet.movie_plot
    ans['movie_genre']=qSet.movie_genre
    ans['movie_link']=qSet.movie_link
    ans['imdb_rating']=qSet.imdb_rating
    return ans

def popular_movies():
    data = pd.read_csv(data_path)
    data = data.sort_values('imdb_rating', ascending=False)
    ans = []
    i = 0
    for index, row in data.iterrows():
        i += 1
        if (i >= 7):
            break
        ans.append(row['movie_title'])
    final=[]
    for i in ans:
        final.append(get_movie_details(i))
    return final

def top_charts(genre):
    data = pd.read_csv(data_path)
    data = data.sort_values('imdb_rating', ascending=False)
    ans = []
    for index, row in data.iterrows():
        if (genre in row['movie_genre']):
            ans.append(row['movie_title'])
    final=[]
    for i in ans[:6]:
        final.append(get_movie_details(i))
    return final

def clean_genre(s):
    return s.replace(' ','').split(',')

def clean_actors(s):
    return s.replace(' ','').lower().split(',')

def clean_director(s):
    return s.replace(' ','').lower().split(',')

def similar_movies(title):
    data = pd.read_csv(data_path)
    data=data.drop('imdb_rating',1)
    data=data.drop('movie_link',1)
    data=data.drop('movie_id',1)
    data['movie_genre'] = data['movie_genre'].map(lambda x: clean_genre(x))
    data['actors'] = data['actors'].map(lambda x: clean_actors(x))
    data['director'] = data['director'].map(lambda x: clean_director(x))

    data['key_words'] = ""

    for index, row in data.iterrows():
        plot = row['movie_plot']
        r = Rake()
        r.extract_keywords_from_text(plot)
        key_words_dict_scores = r.get_word_degrees()
        data.at[index, 'key_words'] = list(key_words_dict_scores.keys())
    data.drop(columns=['movie_plot'], inplace=True)

    data.set_index('movie_title', inplace=True)

    data['bag_of_words'] = ''
    columns = data.columns
    for index, row in data.iterrows():
        words = ''
        for col in columns:
            words = words + ' '.join(row[col]) + ' '
        data.at[index, 'bag_of_words'] = words

    data.drop(columns=[col for col in data.columns if col != 'bag_of_words'], inplace=True)

    count = TfidfVectorizer()
    count_matrix = count.fit_transform(data['bag_of_words'])
    indices = pd.Series(data.index)
    cosine_sim = cosine_similarity(count_matrix, count_matrix)

    idx = indices[indices == title].index[0]

    score_series = pd.Series(cosine_sim[idx]).sort_values(ascending=False)

    top_10_indexes = list(score_series.iloc[1:6].index)

    ans=[]
    for i in top_10_indexes:
        ans.append(data.iloc[i].name)
    final=[]
    for i in ans:
        final.append(get_movie_details(i))
    return final

def personalized_movies(username):
    ratings = pd.read_csv(rating_path)
    reader = Reader()
    data = Dataset.load_from_df(ratings[['username', 'movie_id', 'rating']], reader)
    data.split(n_folds=5)
    svd = SVD()
    evaluate(svd, data, measures=['RMSE'])
    temp=[]
    obj=Movie.objects.all()
    for i in obj:
        temp.append([i.movie_id,i.movie_title,svd.predict(username,i.movie_id).est])
    temp.sort(key= lambda x:x[2],reverse=True)
    ans=[]
    print('predicted_ratings',temp)
    rated=Movie_Rating.objects.filter(username=username)
    already_rated=[]
    for i in rated:
        already_rated.append(i.movie_id)
    j=0
    for i in temp:
        if(j>17):
            break
        if(i[0] not in already_rated):
            ans.append(i[1])
            j+=1
    final=[]
    for i in ans:
        final.append(get_movie_details(i))
    return final

def rate_movie(username,movie_id,rating):
    qSet=Movie_Rating.objects.filter(username=username,movie_id=movie_id)
    if(len(qSet)==0):
        old = open(rating_path,'a')
        old.write(str(username) + "," + str(movie_id) + "," + str(rating) + "\n")
        old.close()
        obj = Movie_Rating(username=str(username), movie_id=str(movie_id), rating=str(rating))
        obj.save()
    else:
        #to update rating csv file
        qSet[0].rating=rating
        qSet[0].save()
        with open(rating_path, 'r') as f:
            data = f.readlines()
            f.close()
        for i in range(len(data)):
            if ((username + ',' + movie_id) in data[i]):
                data[i] = username + ',' + movie_id + ',' + rating+'\n'
        with open(rating_path, 'w') as file:
            file.writelines(data)
            file.close()



'''
#tests->
print(popular_movies())
print(top_charts('Horror'))
print(similar_movies('Dunkirk'))
'''
#print(get_movie_details('Dunkirk'))
#print(personalized_movies('admin'))