from typing import List
import re, traceback


class WordCounter():

    def count(self, strs: List) -> int:
        try:
            result: int = 0
            for s in strs:
                if s is None:
                    pass
                result += len(re.findall(r'\w+', s))
            return result
        except Exception as e:
            print("error with func count: %s" % (repr(e)))
            print(traceback.format_exc())