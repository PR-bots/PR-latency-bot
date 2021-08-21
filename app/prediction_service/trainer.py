# train the prediction model
# there are two modes:
# 1. old: train using our dataset (use data from all the repositories)
# 2. new: crawl new dataset for training (use only data in the target repository)

import sys, pathlib, requests
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from typing import Optional, List
from app.utils.config_loader import ConfigLoader
# for training the model
import pickle, traceback
import pandas as pd
from sklearn import model_selection
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

class Trainer():

    mode: Optional[str]
    datasetUrl: Optional[str]
    datasetName: Optional[str]

    '''
        We split models into two kinds:
        1. model trained using just the factors occurred at the submission time
        2. model trained using the process factors, e.g., the number of comments
        For users, they can also split according to the usage of CI tools, etc. Please have a look at the paper.
    '''
    modelSubmissionPath: Optional[str]
    modelSubmissionFactors: List[str]
    modelSubmission = None
    modelProcessPath: Optional[str]
    modelProcessFactors: List[str]
    modelProcess = None

    def __init__(self) -> None:
        config = ConfigLoader().load_prediction_service_config()
        if "trainer" not in config or "mode" not in config["trainer"]:
            raise Exception("error with the initialization of Trainer object: [trainer]->[mode] not in configuration")

        if "factor_list" not in config["trainer"] or "submission" not in config["trainer"]["factor_list"] or "process" not in config["trainer"]["factor_list"]:
            raise Exception("error with the initialization of Trainer object: [trainer]->[factor_list]->[submission/process] not in configuration")
        self.modelSubmissionFactors = config["trainer"]["factor_list"]["submission"]
        self.modelProcessFactors = config["trainer"]["factor_list"]["process"]

        self.mode = config['trainer']['mode']
        if self.mode == "old":
            # choose to use the old mode
            if "dataset_url" not in config["trainer"] or "dataset_name" not in config["trainer"]:
                raise Exception("error with the initialization of Trainer object: [trainer]->[dataset_url/name] not in configuration")
            self.datasetUrl = config["trainer"]["dataset_url"]
            self.datasetName = config["trainer"]["dataset_name"]
            
            if "model_names" not in config["trainer"] or "submission" not in config["trainer"]["model_names"] or "process" not in config["trainer"]["model_names"]:
                raise Exception("error with the initialization of Trainer object: [trainer]->[model_names] not in configuration")
            self.modelSubmissionPath = config["trainer"]["model_names"]["submission"]
            self.modelProcessPath = config["trainer"]["model_names"]["process"]

            self.train() # initialize the models (self.modelSubmission/self.modelProcess)
        else:
            # choose to use the new mode
            raise Exception("new mode is not supported right now")

    def download_dataset(self):
        # download the dataset
        if pathlib.Path(self.datasetName).is_file():
            print("already downloaded the training dataset")
        else:
            print("downloading training dataset from %s ..." % (self.datasetUrl))
            dataset = requests.get(self.datasetUrl)
            open(self.datasetName, 'wb').write(dataset.content)
            print("finish downloading training dataset.")

    def _log_transfer(self, factors: List, df: pd.DataFrame) -> pd.DataFrame:
        try:
            for factor in factors:
                if factor in df.columns:
                    df[factor] = np.log2(df[factor] + 0.5)
            return df
        except Exception as e:
            print("error with func _log_transfer: %s" % (repr(e)))
            print(traceback.format_exc())

    def _train_one_model(self, factors: List, dataPath: str, modelPath: str):

        '''
            This function is used to train one model (90% data for training and 10% for testing)
            params:
                factors: the list of factors for training the model
        '''
        try:
            df = pd.read_csv(dataPath, nrows=700000)
            Y = df[['lifetime_minutes']]
            Y = self._log_transfer(['lifetime_minutes'], Y)
            X = df[factors]
            continuous_factors = ConfigLoader().load_prediction_service_config()["trainer"]["factor_list"]["continuous"] # read continuous variables
            X = self._log_transfer(continuous_factors, X)
            X_train, X_test, Y_train, Y_test = model_selection.train_test_split(X, Y, test_size=0.1, random_state=10)
            # Fit the model on training set
            model = LinearRegression()
            model.fit(X_train, Y_train)
            # Test the model performance
            Y_test_hat = model.predict(X_test)
            print("the performance of the trained model (r2_score):")
            print(r2_score(Y_test, Y_test_hat))
            # save the model to disk
            pickle.dump(model, open(modelPath, 'wb'))
            return model
        except Exception as e:
            print("error with func _train_one_model: %s" % (repr(e)))
            print(traceback.format_exc())


    def train(self):
        
        '''
        train a model, save it to the model path and return it
        return:
            pickle models
        '''

        try:
            
            # train the model
            if pathlib.Path(self.modelSubmissionPath).is_file():
                print("already trained the submission model")
                self.modelSubmission = pickle.load(open(self.modelSubmissionPath, 'rb'))
            if pathlib.Path(self.modelProcessPath).is_file():
                print("already trained the process model")
                self.modelProcess = pickle.load(open(self.modelProcessPath, 'rb'))

            if self.modelSubmission is None:
                # download dataset
                self.download_dataset()
                # train the model
                self.modelSubmission = self._train_one_model(factors=self.modelSubmissionFactors, dataPath=self.datasetName, modelPath=self.modelSubmissionPath)
            if self.modelProcess is None:
                self.download_dataset()
                self.modelProcess = self._train_one_model(factors=self.modelProcessFactors, dataPath=self.datasetName, modelPath=self.modelProcessPath)
                

        except Exception as e:
            print("error with func train: %s" % (repr(e)))
            print(traceback.format_exc())


if __name__ == "__main__":
    print("training the model...")
    trainer = Trainer()
    print("finish")