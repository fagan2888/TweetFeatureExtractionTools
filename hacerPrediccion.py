import weka.core.jvm as jvm
import sys
import traceback
from weka.core.converters import Loader
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.filters import Filter, MultiFilter
from extractor_de_features import Tweet,TweetFeatureExtractor


# Fuentes:
# https://github.com/fracpete/python-weka-wrapper-examples/blob/master/src/wekaexamples/classifiers/output_class_distribution.py
# http://pythonhosted.org/python-weka-wrapper/examples.html

topics =   {0:'video chavista periodista sentada dtb'.split(" "),\
            1:'venezuela vivo cnn soyfdelrincon senal'.split(" "),\
            2:'trump donald mes opinion mexico'.split(" "),\
            3:'muerte dolares angeles prostitutas venden'.split(" "),\
            4:'ecuador vuelta cne lomasvisto resultados'.split(" "),\
            5:'uu ee indocumentados inmigrantes aissami'.split(" "),\
            6:'sports illustrated 2017 rubia portada'.split(" "),\
            7:'fotos lomasvisto anos accesorios orgullo'.split(" "),\
            8:'muere brutal embarazada companeras recibir'.split(" "),\
            9:'jong kim nam muerte corea'.split(" ")}

header = "tweet_id,hashtags,mentions,uppercase,nonalpha,urls,len,numbers,topic_id,favorite_count,retweet_count,spam\n"

def asignarTopico(tweetText):
    """
    #
    #   @tweetText : texto del tuit
    #
    #   @return maxIndx : indice del topico mas cercano al tuit
    #
    """
    palabras = tweetText.split(" ")
    puntuacion = [0 for i in topics]
    maxIndx = 0
    maxim = 0
    for indxT in topics :
        for palabra in palabras :
            for topWord in topics[indxT]:
                if topWord == palabra :
                    puntuacion[indxT] += 1
                    if puntuacion[indxT] > maxim :
                        maxim = puntuacion[indxT]
                        maxIndx = indxT
                
    return maxIndx

def guardarVectores(testCSVFilename,vectores) :
    with open(testCSVFilename,"w") as ofile:
        ofile.write(header)
        for vector in vectores :
            ofile.write(str(vector["tweet_id"]))
            ofile.write(",")
            ofile.write(str(vector["hashtags"]))
            ofile.write(",")
            ofile.write(str(vector["mentions"]))
            ofile.write(",")
            ofile.write(str(vector["uppercase"]))
            ofile.write(",")
            ofile.write(str(vector["nonalpha"]))
            ofile.write(",")
            ofile.write(str(vector["urls"]))
            ofile.write(",")
            ofile.write(str(vector["len"]))
            ofile.write(",")
            ofile.write(str(vector["numbers"]))
            ofile.write(",")
            ofile.write(str(vector["topic_id"]))
            ofile.write(",")
            ofile.write(str(vector["favorite_count"]))
            ofile.write(",")
            ofile.write(str(vector["retweet_count"]))
            ofile.write(",")
            ofile.write(str(vector["spam"]))
            ofile.write("\n")
        ofile.close()

def detectarSpam_(tuitsConDatos,modeloFilename) :
    vectores = []
    for status in tuitsConDatos :
        vector = construirFeature(status["tweetText"], \
                                 status["tweet_id"],\
                                 status["favorite_count"],\
                                 status["retweet_count"])
        vectores.append(vector)
    
    ifileName = "predictMe.csv"
    #modelFilename = "tweets/modelos/naivebayes.model"
    #modelFilename = "tweets/modelos/usado_en_interfaz_knn.model"
    
    guardarVectores(ifileName,vectores)
    predicciones = predictWithWeka(ifileName,modeloFilename)
    return predicciones

def detectarSpam(tuitsConDatos,modeloFilename):
    """
    #
    #   @tuitsConDatos : lista de diccionarios status con los indices
    #                    tweetText, tweet_id, favorite_count y retweet_count
    #
    #   @return predicciones : lista de predicciones por cada tuit de input.
    #                           Cada prediccion es un diccionario con los indices
    #                           index, actual, predicted, error y distribution
    #
    """
    predicciones = []
    try:
        jvm.start()
        jvm.start(system_cp=True, packages=True)
        predicciones = detectarSpam_(tuitsConDatos,modeloFilename)
        
    except Exception, e:
        print(traceback.format_exc())
    finally:
        jvm.stop()
        return predicciones
    

def construirFeature(tweetText, tweet_id,favorite_count,retweet_count) :
    """
    #
    #
    #   @tweetText : texto del tuit
    #   @tweet_id : id del tuit
    #   @favorite_count : numero de favoritos del tuit
    #   @retweet_count : numero de veces retuiteado
    #
    #   @return featureVector : diccionario con cada atributo del tuit
    #                           sin ser preprocesado
    #
    """
    idTopico = asignarTopico(tweetText)
    tweet = Tweet(tweetText, tweet_id,favorite_count,retweet_count)
    extractor = TweetFeatureExtractor(tweet_id)
    extractor.extractFeatures(tweet)
    featureVector = extractor.getFetureVector()
    featureVector["tweet_id"] = tweet_id
    featureVector["topic_id"]=idTopico
    featureVector["spam"] = 'n' if int(tweet_id) % 2 else 'y'
    return featureVector


def predictWithWeka(csvFilenameWithInputToPredict,modelFilename):
    """
    #   Nota: para usar sin conocer la clase, se puede colocar una clase dummy
    #   e ignorar los valores actual y error de @return results.
    #
    #   Nota: es necesario que el archivo de nombre @csvFilenameWithInputToPredict
    #   contenga instancias de ambas clases (spam y sanas)
    #
    #   @csvFilenameWithInputToPredict : nombre del archivo csv con las instancias
    #                                   a predecir.
    #
    #   @modelFilename : nombre del archivo de modelo generado por weka y 
    #                    compatible con el archivo csv de entrada
    #
    #   @return results : lista de diccionarios con los siguientes indices
    #                      index, actual, predicted, error y distribution
    """
    loader = Loader(classname="weka.core.converters.CSVLoader")
    cls = Classifier(jobject=serialization.read(modelFilename))
    #print(cls)
    
    data = loader.load_file(csvFilenameWithInputToPredict)
    data.class_is_last()
    
    multi = MultiFilter()
    remove = Filter(classname="weka.filters.unsupervised.attribute.Remove", options=["-R", "first"])
    numericToNom = Filter(classname="weka.filters.unsupervised.attribute.NumericToNominal", options=["-R","8,11"])
    normalize = Filter(classname="weka.filters.unsupervised.attribute.Normalize",options=["-S","1.0","-T","0.0"])
    multi.filters = [remove, numericToNom, normalize]
    multi.inputformat(data)
    test = multi.filter(data)
    
    
    results = []
    for index, inst in enumerate(test):
        result = dict()
        
        pred = cls.classify_instance(inst)
        dist = cls.distribution_for_instance(inst)
        
        result["index"] = index+1
        result["actual"] = inst.get_string_value(inst.class_index)
        result["predicted"] = inst.class_attribute.value(int(pred))
        result["error"] = "yes" if pred != inst.get_value(inst.class_index) else "no"
        result["distribution"] = str(dist.tolist())
        
        results.append(result)
        #print result
        
    return results

def main() :
    
    input_file = csv.DictReader(open("datasets/dumpCNNEE_APLICACION.csv", "r"))
    tuits = []
    ids = []
    for row in input_file :
        tuit = dict()
        tuit["tweetText"] = row["text"]
        tuit["tweet_id"] = row["id"]
        tuit["favorite_count"] = row["favorite_count"]
        tuit["retweet_count"] = row["retweet_count"]
        tuits.append(tuit)
        ids.append(row["id"])
    
    ifileName = "predictMe.csv"
    modeloFilename = "naivebayes.model"
    
    predicciones = detectarSpam(tuits,modeloFilename)
    
    out = open("resultadosCNNEE_APLICACION.csv","w")
    out.write("tweet_id,distribution1,distribution2,predicted\n")
    for indx,tweet_id in enumerate(ids) :
        out.write(str(tweet_id))
        out.write(",")
        distribution = ast.literal_eval(predicciones[indx]["distribution"])
        out.write(str(distribution[0]))
        out.write(",")
        out.write(str(distribution[1]))
        out.write(",")
        out.write(str(predicciones[indx]["predicted"]))
        out.write("\n")
    out.close()
    


if __name__ == "__main__":
    import ast
    import csv
    try:
        #jvm.start()
        #jvm.start(system_cp=True, packages=True)
        main()
    except Exception, e:
        print(traceback.format_exc())
    finally:
        #jvm.stop()
        pass