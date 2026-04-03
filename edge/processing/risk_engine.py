from collections import deque
import math

class RiskEngine:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.history = {
            "temperature": deque(maxlen=window_size),
            "humidity": deque(maxlen=window_size),
            "pressure": deque(maxlen=window_size),
            "gas": deque(maxlen=window_size)
        }
        self.last_gas_base = None
    
    def _mean(self, values):
        if not values: return 0
        return sum(values) / len(values)
        
    def _std(self, values, mean):
        if len(values) < 2: return 0
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
        
    def _z_score_anomaly(self, value, mean, std):
        if std == 0: return False
        z = (value - mean) / std
        return abs(z) > 2.5
        
    def _roc(self, values):
        if len(values) < 2: return 0
        return values[-1] - values[-2]

    def process(self, data):
        temp = data.get("temperature", 0)
        hum = data.get("humidity", 0)
        pres = data.get("pressure", 0)
        gas = data.get("gas", 0)

        # 1. Rolling Stats
        t_mean = self._mean(self.history["temperature"])
        t_std = self._std(self.history["temperature"], t_mean)
        
        h_mean = self._mean(self.history["humidity"])
        h_std = self._std(self.history["humidity"], h_mean)
        
        p_mean = self._mean(self.history["pressure"])
        p_std = self._std(self.history["pressure"], p_mean)
        
        g_mean = self._mean(self.history["gas"])
        g_std = self._std(self.history["gas"], g_mean)

        # Append current values
        self.history["temperature"].append(temp)
        self.history["humidity"].append(hum)
        self.history["pressure"].append(pres)
        self.history["gas"].append(gas)

        # 2. Rate of Change
        t_roc = self._roc(self.history["temperature"])
        h_roc = self._roc(self.history["humidity"])
        p_roc = self._roc(self.history["pressure"])

        # 3. Z-score Anomaly
        temp_anom = self._z_score_anomaly(temp, t_mean, t_std) if len(self.history["temperature"]) > 1 else False
        hum_anom = self._z_score_anomaly(hum, h_mean, h_std) if len(self.history["humidity"]) > 1 else False
        pres_anom = self._z_score_anomaly(pres, p_mean, p_std) if len(self.history["pressure"]) > 1 else False
        gas_anom = self._z_score_anomaly(gas, g_mean, g_std) if len(self.history["gas"]) > 1 else False
        
        anomaly = temp_anom or hum_anom or pres_anom or gas_anom

        # 4. Risk Score Formula
        # Normalize inputs for score computation (heuristic scaling)
        # Gas spike (0-100 scale ideally, assume normal max change is 50)
        gas_spike = min(abs(gas - g_mean) / 50 if g_mean else 0, 1.0)
        # Pressure gradient (assume normal max change is ~1hPa)
        p_grad = min(abs(p_roc) / 1.0, 1.0)
        # Temp ROC (assume max change 2C)
        t_grad = min(abs(t_roc) / 2.0, 1.0)
        # Hum ROC (assume max change 5%)
        h_grad = min(abs(h_roc) / 5.0, 1.0)

        risk_score = (
            (gas_spike * 100 * 0.30) +
            (p_grad * 100 * 0.25) +
            (t_grad * 100 * 0.20) +
            (h_grad * 100 * 0.15) +
            ((100 if anomaly else 0) * 0.10)
        )
        
        risk_score = min(max(int(risk_score), 0), 100)
        
        if risk_score > 65:
            level = "HIGH"
        elif risk_score > 30:
            level = "MODERATE"
        else:
            level = "SAFE"

        return {
            "risk_score": risk_score,
            "level": level,
            "anomaly": anomaly
        }
