import datetime, traceback

class TimeOperator():

    def convertTZTime2TimeStamp(self, utc):
        result = None
        try:
            UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
            result = datetime.datetime.strptime(utc, UTC_FORMAT)
        except Exception as e:
            print('error with func convertTZTime2TimeStamp: %s' % (repr(e)))
            print(traceback.format_exc())
        finally:
            return result