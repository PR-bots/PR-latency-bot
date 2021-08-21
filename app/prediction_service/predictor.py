# predict using the trained model

import sys, pathlib, traceback
from typing import List, Dict
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from app.models.pull_request import PullRequest
from app.models.installation import Installation
from app.prediction_service.factor_getter import FactorGetter
from app.utils.config_loader import ConfigLoader
from app.prediction_service.trainer import Trainer

'''
需要修改为合适的factors list，并且要修改预测函数及调用，同时要修改预测后次方转换（2^Y）才是最终分钟数
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
    
    def predict(self, pr: PullRequest, installation: Installation) -> bool:
        '''
            predict whether the pull request can be merged
            params:
                pr: with owner login, repo name and number
                installation: which installation is for
            return:
                can merge or not: bool
        '''
        try:
            # get the factors for this pr
            factorDict = self._get_factors(pr, installation)
            factorList = ConfigLoader().load_prediction_service_config()["trainer"]["factor_list"][self.type]
            X_test = [factorDict[self._factor_cut_suffix(f, ["_open", "_close"])] for f in factorList]
            if self.type == "submission":
                predictions = self.modelSubmission.predict([X_test])
            elif self.type == "process":
                predictions = self.modelProcess.predict([X_test])

            if predictions[0] == 1:
                return True
            elif predictions[0] == 0:
                return False
            else:
                raise Exception("error with the prediction result of func predict.")
        except Exception as e:
            print("error with func predict: %s" % (repr(e)))
            print(traceback.format_exc())