from enum import Enum

class SignalType(Enum):
    BUY_LEVERAGE = "BUY_LEVERAGE"
    BUY_INVERSE = "BUY_INVERSE"
    NEUTRAL = "NEUTRAL"

class Strategy:
    def __init__(self, rsi_long_threshold: float, rsi_short_threshold: float, use_macd_filter: bool = True):
        self.rsi_long_threshold = rsi_long_threshold
        self.rsi_short_threshold = rsi_short_threshold
        self.use_macd_filter = use_macd_filter

    def decide_direction(self, rsi: float, macd: float, signal: float) -> SignalType:
        """
        Decide trading direction based on SPY indicators.
        """
        # Long Condition (Bullish) -> Buy Leverage
        is_bullish_macd = (macd > signal) if self.use_macd_filter else True
        if rsi > self.rsi_long_threshold and is_bullish_macd:
            return SignalType.BUY_LEVERAGE
        
        # Short Condition (Bearish) -> Buy Inverse
        is_bearish_macd = (macd < signal) if self.use_macd_filter else True
        if rsi < self.rsi_short_threshold and is_bearish_macd:
            return SignalType.BUY_INVERSE
            
        return SignalType.NEUTRAL
