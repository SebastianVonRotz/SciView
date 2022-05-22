import glob
from urllib.parse import unquote
import random
# import nltk
# import re
# import string
import gensim
# from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer # or LancasterStemmer, RegexpStemmer, SnowballStemmer
from nltk.stem import WordNetLemmatizer 
# nltk.download('punkt')
# nltk.download('stopwords')
stemmer = PorterStemmer()
stop_words = stopwords.words('english') # or any other list of your choice
lemmatizer = WordNetLemmatizer()
from langdetect import detect_langs # pip install langdetect
import time
# import multiprocessing as mp
import pickle
from itertools import islice
import pandas as pd


def DOI_Path_Dictionary(dirNum, dataPath):
    '''
    Based on the number of the directory and path to those directories a dictionary is created with keys as DOIs and the corresponding Path to this file as values.
    '''
    # Init dict
    doiPathDict={}

    # Add 2nd part of the dir name
    dir=dirNum + "00000\ "

    # Crete the prefix which can then be used
    prefix=(dataPath + dir).replace(" ","")
    targetPattern = prefix +"**\*.txt"
    doiPathList=glob.glob(targetPattern)

    # Go trough each Path and store the formated doi as key and the corresponding path as Value
    for path in doiPathList:

        # Remove file ending
        pathString=path.replace(".txt","")

        # Remove Prefix and replace \ with / and then create URL format
        pathString=pathString.replace(prefix,"").replace("\\","/")
        doi = unquote(pathString)
        doiPathDict[doi]=path
    
    return doiPathDict



def Random_DOI_Path_Pair(doiPathDict):

    # Get random dictionary pair in dictionary
    # Using random.choice() + list() + items()
    res = key, val = random.choice(list(doiPathDict.items()))

    # printing result
    print("The random pair is : " + str(res))

    # Print corresponding data
    with open(val, "r", encoding="utf8") as f:
        contents = f.read()
        len(contents)
        print(contents[0:100])



def Chunks(data, SIZE):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}



def Preprocess_Token_List(tokenList,minlength,maxlength):
    # lowercase
    tokenList=[token.lower() for token in tokenList]

    # Alphabetical
    tokenList=[token for token in tokenList if token.isalpha()]

    # Stemming of the token
    #tokenList=map(stemmer.stem,tokenList)

    # lemmatization of the token
    tokenList=map(lemmatizer.lemmatize,tokenList)

    # return nothing if token part of stop_words
    tokenList=[token for token in tokenList if token not in stop_words]

    # remove token if its a punctuation
    tokenList=map(gensim.parsing.preprocessing.strip_punctuation,tokenList)

    # remove token if is a number
    tokenList=map(gensim.parsing.preprocessing.strip_numeric,tokenList)

    # remove token if it under a certain length
    tokenList=[token for token in tokenList if len(token) > minlength]

    # remove token if it is above a certain length
    tokenList=[token for token in tokenList if len(token) < maxlength]

    return list(tokenList)





def Preprocessed_Dict_and_Metadata(doiPathDict):

    # Start Global Timer which times the whole function
    tic = time.perf_counter()

    # init local tic for iterCount which times a specific chunk of processed documents
    tictic= time.perf_counter()

    # Init MetaDataframe
    MetaData=pd.DataFrame(columns=["DOI","Token Amount", "Language"])

    # Init the counter of iterations
    iterCount=0

    #Init Dicitonary for storing  preprocessed texts
    FtPr={}

    # Init Dictionary for storing doi and path of documents which could not be openend
    encodingError={}

    # Iterate trough each doi and corresponding path  in the dictionary
    for doi, path in doiPathDict.items():
        # Load Text
        try:
            Ft=open(path, "r", encoding="utf8").read()
            # Try detecting language
            try:
                language=detect_langs(Ft)
            except:
                language="no language detected"
            # Remove the
            Ft=Ft.replace("-\n\n","") 
            Ft=Ft.replace("-\n","") 
            # print ("Removed end of line hyphenations")
            # FullText_Token.pickle
            FtTo=list(gensim.utils.tokenize(Ft))
            # Define Preprocessing parameters
            minlength = 1
            maxlength = 30
            FtToPr=Preprocess_Token_List(FtTo,minlength,maxlength)
            # Append MetaData
            MetaData=MetaData.append(pd.DataFrame([[doi,len(FtToPr),language]],
                        columns=["DOI","Token Amount", "Language"]),ignore_index = True)
            # Append Preprocessed texts as dictionary
            FtPr[doi]=FtToPr
        except:
            encodingError[doi]=path
        
        if iterCount % 4000 == 0: 
            toctoc=time.perf_counter()
            print('iterCount = {}'.format(iterCount), "", "Time elapsed in seconds: ", round(toctoc-tictic,4), ", in minutes ", round((toctoc-tictic)/60,4), ", in hours: ", round((toctoc-tictic)/3600,4))
            tictic= time.perf_counter()
        iterCount+=1
    
    #Stop global timer and print
    toc = time.perf_counter()
    print("Time elapsed in seconds: ", round(toc-tic,4), ", in minutes ", round((toc-tic)/60,4), ", in hours: ", round((toc-tic)/3600,4))
   
    return MetaData, FtPr, encodingError





def Dict_Loader(dirNum, doiPath_Path, doiPath_Suffix):
    # Bring for example 27 into the form of "027"
    dirNum=str(dirNum).zfill(3)

    # Create path to dictionary
    openName=(doiPath_Path + dirNum + doiPath_Suffix).replace(" ","")

    # Open the dictionary
    with open(openName, 'rb') as handle:
        interDict = pickle.load(handle)  
    return interDict

