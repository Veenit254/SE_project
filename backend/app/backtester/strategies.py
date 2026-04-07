import pandas as pd
import numpy as np
from typing import Callable

STRATEGY_REGISTRY: dict[str, Callable] = {}

def strategy(name: str):
    def decorator(fn):
        STRATEGY_REGISTRY[name] = fn
        return fn
    return decorator

@strategy("ma_crossover")
def ma_crossover(df: pd.DataFrame, fast: int = 20,
                 slow: int = 50) -> pd.Series:
    fast_ma = df["close"].rolling(fast).mean()
    slow_ma = df["close"].rolling(slow).mean()
    signal = pd.Series(0, index=df.index)
    signal[fast_ma > slow_ma] = 1
    signal[fast_ma < slow_ma] = -1
    return signal

@strategy("rsi_mean_reversion")
def rsi_mean_reversion(df: pd.DataFrame, period: int = 14,
                       oversold: float = 30,
                       overbought: float = 70) -> pd.Series:
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    signal = pd.Series(0, index=df.index)
    signal[rsi < oversold]   = 1    # long when oversold
    signal[rsi > overbought] = -1   # short when overbought
    return signal

@strategy("bollinger_breakout")
def bollinger_breakout(df: pd.DataFrame, window: int = 20,
                       num_std: float = 2.0) -> pd.Series:
    mid   = df["close"].rolling(window).mean()
    std   = df["close"].rolling(window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    signal = pd.Series(0, index=df.index)
    signal[df["close"] < lower] = 1
    signal[df["close"] > upper] = -1
    return signal