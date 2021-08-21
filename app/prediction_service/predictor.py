# predict using the trained model

from inspect import trace
from math import ceil
import sys, pathlib, traceback
from typing import List, Dict, Optional
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np

from app.models.pull_request import PullRequest
from app.models.installation import Installation
from app.prediction_service.factor_getter import FactorGetter
from app.utils.config_loader import ConfigLoader
from app.prediction_service.trainer import Trainer

'''
并且要修改预测函数及调用，同时要修改预测后次方转换（2^Y）才是最终分钟数
还需要修改预测后的返回结果（返回信息，非boolean，如何体现数值大小）
'''

class Predictor():

    modelSubmission = None
    modelProcess = None
    type: str

    def __init__(self, trainer: Trainer, type: str) -> None:
        self.modelSubmission = trainer.modelSubmission
        self.modelProcess = trainer.modelProcess
        self.type = type

    def _get_factors(self, pr: PullRequest, installation: Installation) -> Dict:
        result: Dict
        result = FactorGetter(pr, installation).query_pr_infos()
        return result

    def _factor_cut_suffix(self, s, suffixList):
        try:
            for suffix in suffixList:
                if s.endswith(suffix):
                    return s[:-len(suffix)]
            return s
        except Exception as e:
            print("error with func _factor_cut_suffix: %s" % (repr(e)))
            print(traceback.format_exc())

    def _convert_factor_dict_2_df(self, factorDict: Dict):
        try:
            for key, value in factorDict.items():
                factorDict[key] = [value]
            df = pd.DataFrame.from_dict(factorDict)
            return df
        except Exception as e:
            print("error with func _convert_factor_dict_2_df: %s" % (repr(e)))
            print(traceback.format_exc())

    def _log_transfer(self, factors: List, df: pd.DataFrame) -> pd.DataFrame:
        try:
            for factor in factors:
                if factor in df.columns:
                    df[factor] = np.log2(df[factor] + 0.5)
            return df
        except Exception as e:
            print("error with func _log_transfer: %s" % (repr(e)))
            print(traceback.format_exc())
    
    def predict(self, pr: PullRequest, installation: Installation) -> Optional[int]:
        '''
            predict whether the pull request can be merged
            params:
                pr: with owner login, repo name and number
                installation: which installation is for
            return:
                int: >0 the minutes needed for the pr to finish
                int: -1 wrong prediction
                None: error
        '''
        try:
            # get the factors for this pr
            factorDict = self._get_factors(pr, installation)
            factorDF = self._convert_factor_dict_2_df(factorDict)
            factorList = ConfigLoader().load_prediction_service_config()["trainer"]["factor_list"][self.type]
            factorList = [self._factor_cut_suffix(f, ["_open", "_close"]) for f in factorList]
            factorDF = self._log_transfer(factorList, factorDF)
            X_test = [factorDF[f].iloc[0] for f in factorList]
            if self.type == "submission":
                predictions = self.modelSubmission.predict([X_test])
            elif self.type == "process":
                predictions = self.modelProcess.predict([X_test])
            prediction = 2**predictions[0][0] - 0.5
            if prediction <= factorDict["lifetime_minutes"]:
                print("the prediction is not correct.")
                return -1
            else:
                return ceil(prediction - factorDict["lifetime_minutes"])
        except Exception as e:
            print("error with func predict: %s" % (repr(e)))
            print(traceback.format_exc())
            return None