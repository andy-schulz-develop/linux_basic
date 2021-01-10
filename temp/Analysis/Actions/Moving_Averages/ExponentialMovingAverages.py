
from Analysis.Actions.Moving_Averages.MovingAverage import MovingAverage;
import decimal;
import math;


class TimeDependentEma(MovingAverage):

    def __init__(self, time_parameter, precision=0.00000001):
        super(TimeDependentEma, self).__init__(precision=precision);
        self.__gamma = decimal.Decimal(precision) ** (1 / decimal.Decimal(time_parameter));
        self.__alpha = decimal.Decimal(1.0) - self.__gamma;
        self.__ema = None;

        self.__previous_value = 0;
        self.__previous_t = 0;

    def get_ema(self):
        return self.__ema;

    def get_minimum_number_of_points(self):
        if self.__alpha == 1:
            return 100;
        else:
            return int(math.ceil(1.5 * math.log(self._precision, decimal.Decimal(1.0) - self.__alpha)));

    def init_calculation(self, initial_timestamp: int, initial_price: decimal.Decimal):
        self.__ema = initial_price;
        self.__previous_t = initial_timestamp;
        self.__previous_value = self.__ema;

    def calculation_step(self, timestamp: int, price: decimal.Decimal):
        # TODO: CHECK!!!!!!!!!
        t = timestamp;
        x = price;
        dt = t - self.__previous_t
        y_new = self.__ema - (1 - self.__gamma) * self.__previous_value
        x_adj = self.__previous_value * (self.__gamma ** (-dt + 1) - self.__gamma)
        y_new += (1 - self.__gamma) * x_adj
        self.__ema = self.__gamma ** dt * y_new + (1 - self.__gamma) * x

        self.__previous_value = x
        self.__previous_t = t


class CachedEMA(MovingAverage):
    """
    Definition from
    """

    def __init__(self, time_parameter, precision="0.00000001"):
        super(CachedEMA, self).__init__(precision=precision);
        self.__ema = decimal.Decimal("0.0");
        self.__alpha = decimal.Decimal(2.0) / (decimal.Decimal(time_parameter) + decimal.Decimal(1.0));

    def get_ema(self):
        return self.__ema;

    def get_minimum_number_of_points(self):
        if self.__alpha == 1:
            return 100;
        else:
            return int(math.ceil(1.5 * math.log(self._precision, decimal.Decimal(1.0) - self.__alpha)));

    def calculation_step(self, price: decimal.Decimal):
        self.__ema = (price - self.__ema) * self.__alpha + self.__ema;
        return self.__ema;

    def init_calculation(self, initial_price: decimal.Decimal):
        self.__ema = initial_price;
