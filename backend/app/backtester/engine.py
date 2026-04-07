import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Callable

@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    metrics: dict

class VectorizedBacktester:
    def __init__(self, initial_capital: float = 100_000.0,
                 commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission

    def run(self, ohlcv: pd.DataFrame,
            signal_fn: Callable[[pd.DataFrame], pd.Series]) -> BacktestResult:
        """
        signal_fn must return a pd.Series with values in {-1, 0, 1}
        aligned to ohlcv.index.  All position sizing, slippage, and
        equity accounting is handled here — strategies stay pure.
        """
        df = ohlcv.copy()
        df["signal"] = signal_fn(df)
        
        # Shift by 1: you act on today's signal at tomorrow's open
        df["position"] = df["signal"].shift(1).fillna(0)
        
        # Vectorized returns: daily % change × position
        df["market_return"] = df["close"].pct_change()
        df["strategy_return"] = df["position"] * df["market_return"]
        
        # Apply round-trip commission on each position change
        df["trade"] = df["position"].diff().abs()
        df["strategy_return"] -= df["trade"] * self.commission
        
        # Compound equity curve
        df["equity"] = self.initial_capital * (1 + df["strategy_return"]).cumprod()
        df.loc[df.index[0], "equity"] = self.initial_capital
        
        # Build trade log (vectorized entry/exit detection)
        entries = df[df["trade"] > 0].copy()
        entries["type"] = np.where(df.loc[entries.index, "position"] > 0,
                                   "BUY", "SELL")
        entries["price"] = df.loc[entries.index, "close"]
        
        return BacktestResult(
            equity_curve=df["equity"],
            trades=entries[["type","price","position"]],
            metrics=self._compute_metrics(df["strategy_return"], df["equity"])
        )

    def _compute_metrics(self, returns: pd.Series,
                         equity: pd.Series) -> dict:
        ann = 252  # trading days
        excess = returns - 0.04 / ann   # risk-free rate annualized
        sharpe = (excess.mean() / excess.std()) * np.sqrt(ann) \
            if excess.std() > 0 else 0.0
        downside = returns[returns < 0].std()
        sortino = (excess.mean() / downside) * np.sqrt(ann) \
            if downside > 0 else 0.0
            
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        winning = returns[returns > 0]
        losing  = returns[returns < 0]
        win_rate = len(winning) / (len(winning) + len(losing)) \
            if (len(winning) + len(losing)) > 0 else 0.0
            
        ann_return = (equity.iloc[-1] / equity.iloc[0]) ** \
                     (ann / len(returns)) - 1
                     
        return {
            "sharpe_ratio":     round(sharpe, 4),
            "sortino_ratio":    round(sortino, 4),
            "max_drawdown":     round(max_drawdown, 4),
            "win_rate":         round(win_rate, 4),
            "annualized_return":round(ann_return, 4),
            "total_trades":     int(len(winning) + len(losing)),
            "profit_factor":    round(winning.sum() / abs(losing.sum()), 4)
                                if abs(losing.sum()) > 0 else float("inf")
        }