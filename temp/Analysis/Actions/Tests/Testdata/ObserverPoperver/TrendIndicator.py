import numpy as np
from matplotlib import pyplot as plt

import numpy as np

class TrendObserver():
    def __init__(self , N):
        self.N = N
        self.x = np.arange(1,self.N+1,1)
        self.const_fact = 12 / ((N - 1) * (N) * (N + 1))
        self.filter = self.const_fact * (self.x[::-1] - (N+1)/2)


    def apply_filter(self,y):
        ## Non-recursive procedure
        ## y is the time series
        y_out = np.convolve(y,self.filter,mode = 'valid')
        self.y_sum = self.const_fact * np.sum(y[-self.N:])

        self.trend_before = y_out[-1]
        return(y_out)


    def apply_ite(self,y_new,y_last):
        ## Recursive Procedure
        ## Needs to be initiatiated by applying apply_filter once to a part of the time series
        ## y_new is the new value
        ## y_last is the first value in the window of the previous step

        # Update Trend
        trend_new = self.trend_before - self.y_sum
        trend_new += self.const_fact * y_last * (self.N + 1)/2
        trend_new += self.const_fact * y_new * (self.N - 1)/2

        # Update other stuff
        self.y_sum += self.const_fact * ( y_new - y_last )
        self.trend_before = trend_new.copy()

        return(trend_new)

## Generate signal ##
N_sample = 10000
N_window = 250
#y = np.array([0,1,10,15,30])
y_rand = np.random.normal(loc=0.0, scale=1.0, size=N_sample)
y = np.cumsum(y_rand)

#y = np.array([0,10])
x = np.arange(1,len(y)+1,1)
N = len(y)

## Procedure providing entire dataseries
TrendObs = TrendObserver(N_window)
y_filter = TrendObs.apply_filter(y)

## Iterative procedure ##
y_ite = list(TrendObs.apply_filter(y[:N_window])) ## Initialize with first N_window observations
for i in range(N_window, len(y)):
    y_ite += [TrendObs.apply_ite(y[i],y[i-N_window])] ## Iteration with supplied new and oldest value

## Plotting ##
fig, ax1 = plt.subplots()

color = 'tab:blue'
ax1.set_xlabel('Time')
ax1.set_ylabel('Stock', color=color)
ax1.plot(x, y, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:red'
ax2.set_ylabel('Trend', color=color)  # we already handled the x-label with ax1
ax2.plot(x[N_window-1:],y_filter, color=color)
ax2.plot(x[N_window-1:],y_ite, color=color)
ax2.plot([x[0] , x[-1]],[0,0], color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()

