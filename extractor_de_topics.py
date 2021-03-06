#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Extraído en parte de: https://de.dariah.eu/tatom/topic_model_python.html

import numpy as np
import sklearn.feature_extraction.text as text
from sklearn import decomposition
from palabras_comunes import palabras_comunes
import csv

# Se abre el archivo con tuits desordenados y se guardan sus contenidos
texts = []
statuses = []
input_file = csv.DictReader(open("datasets/dumpCaraotaDigitalCNNELaPatillaRANDOM.csv", "r"))
for row in input_file:
    texts.append(row["text"])
    statuses.append(row)


# Token count matrix
print("Computing term frequency matrix")
vectorizer = text.CountVectorizer(input='content', 
                                    stop_words=palabras_comunes, 
                                    max_df=0.5,
                                    lowercase=True,
                                    strip_accents="ascii",
                                    encoding="utf-8",
                                    analyzer="word")


# Document term matrix
print("Computing document term matrix")
dtm = vectorizer.fit_transform(texts).toarray()

vocab = np.array(vectorizer.get_feature_names())


# Se aplica la factorizacion no negativa de la matriz de frecuencias
num_topics = 10
num_top_words = 5
print("Applying NMF with "+str(num_topics)+" topics and "+str(num_top_words)+" top words")
clf = decomposition.NMF(n_components=num_topics, random_state=1)
doctopic = clf.fit_transform(dtm)


topic_words = []

# Se obtienen los top words por cada topico
print("Getting top words")
for topic in clf.components_:
    word_idx = np.argsort(topic)[::-1][0:num_top_words]
    topic_words.append([vocab[i].encode('utf-8') for i in word_idx])

doctopic = doctopic / np.sum(doctopic, axis=1, keepdims=True)

#print document-vs-topic-matrix dim
print("(documents, terms) = ",dtm.shape)


print("Saving tweet_id with its topics datasets/idTuitsWithTopTopics.csv")
#Se enlaza el id de cada tuit con los ids de sus top topics
with open("datasets/idTuitsWithTopTopics.csv","w") as fileDocTopics :
    fileDocTopics.write("tweet_id,top_topic_1,top_topic_2,top_topic_3\n")
    for i,row in enumerate(statuses):
        top_topics = np.argsort(doctopic[i,:])[::-1][0:3]
        top_topics_str = ' '.join(str(t) for t in top_topics)
        #print("{}: {}".format(i, top_topics_str))
        fileDocTopics.write(row["id"]+","+\
                            str(top_topics[0])+","+\
                            str(top_topics[1])+","+\
                            str(top_topics[2])+"\n")
    fileDocTopics.close()

print("Saving topic_id with its top words datasets/topicsWithTopWords.csv")
# Se enlaza el id de cada topic con sus top words
with open("datasets/topicsWithTopWords.csv","w") as fileTopics :
    fileTopics.write("id_topic, wordsbag\n")
    for t in range(len(topic_words)):
        print("Topic {}: {}".format(t, ' '.join(topic_words[t][:15])))
        fileTopics.write(str(t)+",'"+(' '.join(topic_words[t][:15]))+"'\n")
    fileTopics.close()


