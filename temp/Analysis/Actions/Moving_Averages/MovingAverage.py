
import decimal;


class MovingAverage(object):

    def __init__(self, precision="0.00000001"):
        self._precision = decimal.Decimal(precision);
        self._last_timestamp = 0;
