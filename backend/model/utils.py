"""
ClimaScope - Advanced AI Intelligence Utilities
Health score calculation and insight generation engine
"""

import numpy as np
from datetime import datetime

class SystemHealthAnalyzer:
    """Advanced system health analysis for multi-sensor intelligence"""
    
    def __init__(self):
        # Define safe operating ranges for each sensor
        self.safe_ranges = {
            'temperature': {'min': 15.0, 'max': 35.0, 'optimal': (20.0, 25.0)},
            'humidity': {'min': 30.0, 'max': 70.0, 'optimal': (40.0, 60.0)},
            'pressure': {'min': 980.0, 'max': 1040.0, 'optimal': (1000.0, 1020.0)},
            'gas_ppm': {'min': 50.0, 'max': 300.0, 'optimal': (100.0, 200.0)}
        }
        
        # Weight factors for health score calculation
        self.health_weights = {
            'temperature': 0.3,
            'humidity': 0.2,
            'pressure': 0.2,
            'gas_ppm': 0.3
        }
    
    def calculate_sensor_score(self, value, sensor_type):
        """Calculate individual sensor health score (0-100)"""
        if sensor_type not in self.safe_ranges:
            return 75.0  # Default score for unknown sensors
        
        range_info = self.safe_ranges[sensor_type]
        min_safe, max_safe = range_info['min'], range_info['max']
        optimal_min, optimal_max = range_info['optimal']
        
        # Perfect score in optimal range
        if optimal_min <= value <= optimal_max:
            return 100.0
        
        # Linear penalty outside optimal range but within safe range
        if min_safe <= value <= max_safe:
            if value < optimal_min:
                distance = optimal_min - value
                total_distance = optimal_min - min_safe
            else:
                distance = value - optimal_max
                total_distance = max_safe - optimal_max
            
            penalty = (distance / total_distance) * 30  # Max 30 point penalty
            return max(70.0, 100.0 - penalty)
        
        # Heavy penalty outside safe range
        if value < min_safe:
            distance = min_safe - value
            return max(0.0, 40.0 - (distance * 0.5))
        else:
            distance = value - max_safe
            return max(0.0, 40.0 - (distance * 0.1))
    
    def calculate_system_health_score(self, temperature, humidity, pressure, gas_ppm, anomaly_score):
        """
        Calculate comprehensive system health score (0-100)
        
        Formula:
        Health Score = Weighted sum of sensor scores + Anomaly adjustment
        
        Components:
        - Individual sensor scores (0-100 each)
        - Anomaly score penalty
        - Multi-sensor interaction bonus/penalty
        """
        
        # Calculate individual sensor scores
        temp_score = self.calculate_sensor_score(temperature, 'temperature')
        humidity_score = self.calculate_sensor_score(humidity, 'humidity')
        pressure_score = self.calculate_sensor_score(pressure, 'pressure')
        gas_score = self.calculate_sensor_score(gas_ppm, 'gas_ppm')
        
        # Weighted average of sensor scores
        sensor_health = (
            temp_score * self.health_weights['temperature'] +
            humidity_score * self.health_weights['humidity'] +
            pressure_score * self.health_weights['pressure'] +
            gas_score * self.health_weights['gas_ppm']
        )
        
        # Anomaly adjustment (0 to -20 points)
        anomaly_penalty = max(0, min(20, abs(anomaly_score) * 50))
        
        # Multi-sensor interaction analysis
        interaction_adjustment = self._calculate_interaction_bonus(
            temperature, humidity, pressure, gas_ppm
        )
        
        # Final health score
        health_score = sensor_health - anomaly_penalty + interaction_adjustment
        health_score = max(0.0, min(100.0, health_score))
        
        return {
            'overall_score': round(health_score, 1),
            'sensor_scores': {
                'temperature': round(temp_score, 1),
                'humidity': round(humidity_score, 1),
                'pressure': round(pressure_score, 1),
                'gas_ppm': round(gas_score, 1)
            },
            'anomaly_penalty': round(anomaly_penalty, 1),
            'interaction_adjustment': round(interaction_adjustment, 1),
            'components': {
                'sensor_health': round(sensor_health, 1),
                'anomaly_penalty': round(anomaly_penalty, 1),
                'interaction_bonus': round(interaction_adjustment, 1)
            }
        }
    
    def _calculate_interaction_bonus(self, temperature, humidity, pressure, gas_ppm):
        """Calculate multi-sensor interaction bonus/penalty"""
        bonus = 0.0
        
        # Temperature-Humidity interaction (Heat stress)
        if temperature > 30 and humidity > 60:
            bonus -= 5.0  # Heat stress penalty
        elif temperature < 20 and humidity < 40:
            bonus -= 3.0  # Cold stress penalty
        
        # Pressure-Temperature interaction (Weather stability)
        pressure_deviation = abs(pressure - 1013.25)
        temp_deviation = abs(temperature - 25.0)
        
        if pressure_deviation > 10 and temp_deviation > 5:
            bonus -= 4.0  # Unstable weather
        elif pressure_deviation < 2 and temp_deviation < 2:
            bonus += 3.0  # Very stable conditions
        
        # Gas-Temperature interaction (Combustion risk)
        if gas_ppm > 250 and temperature > 28:
            bonus -= 8.0  # High combustion risk
        elif gas_ppm < 150 and temperature < 22:
            bonus += 2.0  # Safe conditions
        
        # All sensors in optimal range
        optimal_temp = 20 <= temperature <= 25
        optimal_humidity = 40 <= humidity <= 60
        optimal_pressure = 1000 <= pressure <= 1020
        optimal_gas = 100 <= gas_ppm <= 200
        
        optimal_count = sum([optimal_temp, optimal_humidity, optimal_pressure, optimal_gas])
        if optimal_count >= 3:
            bonus += 5.0  # Excellent overall conditions
        
        return bonus
    
    def determine_status_level(self, health_score, anomaly_detected=False):
        """Determine system status based on health score and anomaly detection"""
        if anomaly_detected:
            return "danger"
        
        if health_score >= 80:
            return "normal"
        elif health_score >= 50:
            return "warning"
        else:
            return "danger"

class InsightGenerator:
    """Generate intelligent insights based on sensor data and anomalies"""
    
    def __init__(self):
        self.insight_templates = {
            'temperature': {
                'stable': "Temperature stable within normal range",
                'rising': "Temperature trending upward - monitor for overheating",
                'falling': "Temperature decreasing - possible cooling trend",
                'high': "Temperature elevated - check ventilation",
                'low': "Temperature low - possible heating needed"
            },
            'humidity': {
                'stable': "Humidity levels stable",
                'high': "High humidity detected - risk of condensation",
                'low': "Low humidity - may cause dryness issues"
            },
            'gas': {
                'normal': "Gas levels within safe range",
                'spike': "Sudden gas spike detected - investigate source",
                'elevated': "Gas levels elevated - ensure ventilation",
                'low': "Gas levels low - normal baseline"
            },
            'pressure': {
                'stable': "Atmospheric pressure stable",
                'dropping': "Pressure dropping - weather change likely",
                'rising': "Pressure rising - stable weather pattern",
                'abnormal': "Pressure abnormal - environmental instability"
            },
            'anomaly': {
                'detected': "⚠️ Anomaly detected in sensor patterns",
                'multiple': "Multiple anomalies detected - system stress",
                'resolved': "Anomaly resolved - system stable"
            },
            'health': {
                'excellent': "🟢 System health excellent",
                'good': "🟡 System health good",
                'fair': "🟠 System health fair - monitor closely",
                'poor': "🔴 System health poor - action required"
            }
        }
    
    def generate_insight(self, temperature, humidity, pressure, gas_ppm, 
                      anomaly_detected, anomaly_score, health_score, 
                      temp_trend=None, gas_trend=None):
        """
        Generate comprehensive insight based on all sensor data
        
        Returns structured insight with primary message and details
        """
        
        insights = []
        
        # Temperature analysis
        temp_insight = self._analyze_temperature(temperature, temp_trend)
        if temp_insight:
            insights.append(temp_insight)
        
        # Gas analysis
        gas_insight = self._analyze_gas(gas_ppm, gas_trend)
        if gas_insight:
            insights.append(gas_insight)
        
        # Pressure analysis
        pressure_insight = self._analyze_pressure(pressure)
        if pressure_insight:
            insights.append(pressure_insight)
        
        # Humidity analysis
        humidity_insight = self._analyze_humidity(humidity)
        if humidity_insight:
            insights.append(humidity_insight)
        
        # Anomaly analysis
        if anomaly_detected:
            insights.append(self.insight_templates['anomaly']['detected'])
            insights.append(f"Anomaly score: {anomaly_score:.3f}")
        
        # Health status
        health_status = self._get_health_status(health_score)
        insights.append(health_status)
        
        # Combine insights into coherent message
        primary_insight = insights[0] if insights else "System operating normally"
        detailed_insights = insights[1:3] if len(insights) > 1 else []
        
        return {
            'primary': primary_insight,
            'details': detailed_insights,
            'health_status': health_status,
            'recommendations': self._generate_recommendations(
                temperature, humidity, pressure, gas_ppm, 
                anomaly_detected, health_score
            )
        }
    
    def _analyze_temperature(self, temperature, trend=None):
        """Analyze temperature patterns"""
        if trend == 'rising':
            return self.insight_templates['temperature']['rising']
        elif trend == 'falling':
            return self.insight_templates['temperature']['falling']
        elif temperature > 30:
            return self.insight_templates['temperature']['high']
        elif temperature < 18:
            return self.insight_templates['temperature']['low']
        else:
            return self.insight_templates['temperature']['stable']
    
    def _analyze_gas(self, gas_ppm, trend=None):
        """Analyze gas levels"""
        if gas_ppm > 400:
            return self.insight_templates['gas']['spike']
        elif gas_ppm > 250:
            return self.insight_templates['gas']['elevated']
        elif gas_ppm < 100:
            return self.insight_templates['gas']['low']
        else:
            return self.insight_templates['gas']['normal']
    
    def _analyze_pressure(self, pressure):
        """Analyze pressure patterns"""
        if pressure > 1030:
            return self.insight_templates['pressure']['rising']
        elif pressure < 990:
            return self.insight_templates['pressure']['dropping']
        elif 990 <= pressure <= 1030:
            return self.insight_templates['pressure']['stable']
        else:
            return self.insight_templates['pressure']['abnormal']
    
    def _analyze_humidity(self, humidity):
        """Analyze humidity levels"""
        if humidity > 65:
            return self.insight_templates['humidity']['high']
        elif humidity < 35:
            return self.insight_templates['humidity']['low']
        else:
            return self.insight_templates['humidity']['stable']
    
    def _get_health_status(self, health_score):
        """Get health status message"""
        if health_score >= 85:
            return self.insight_templates['health']['excellent']
        elif health_score >= 70:
            return self.insight_templates['health']['good']
        elif health_score >= 50:
            return self.insight_templates['health']['fair']
        else:
            return self.insight_templates['health']['poor']
    
    def _generate_recommendations(self, temperature, humidity, pressure, gas_ppm, 
                               anomaly_detected, health_score):
        """Generate actionable recommendations"""
        recommendations = []
        
        if anomaly_detected:
            recommendations.append("🔍 Investigate sensor readings for potential faults")
        
        if temperature > 32:
            recommendations.append("🌡️ Increase ventilation or reduce heat sources")
        elif temperature < 18:
            recommendations.append("🔥 Check heating system functionality")
        
        if gas_ppm > 300:
            recommendations.append("💨 Immediate ventilation required - check for gas sources")
        elif gas_ppm > 200:
            recommendations.append("🪟 Ensure adequate ventilation")
        
        if humidity > 65:
            recommendations.append("💧 Use dehumidifier or increase air circulation")
        elif humidity < 35:
            recommendations.append("🌫 Consider humidification for comfort")
        
        if health_score < 50:
            recommendations.append("⚠️ System health poor - comprehensive check recommended")
        
        return recommendations

def calculate_prediction_confidence(model_type, anomaly_score, health_score):
    """Calculate confidence based on model type and system state"""
    base_confidence = {
        'LinearRegression': 0.85,
        'RandomForest': 0.90,
        'XGBoost': 0.92
    }.get(model_type, 0.80)
    
    # Adjust confidence based on anomaly score and health
    if abs(anomaly_score) > 0.15:
        base_confidence -= 0.15  # Reduce confidence for anomalies
    
    if health_score < 50:
        base_confidence -= 0.10  # Reduce confidence for poor health
    
    return max(0.5, min(0.95, base_confidence))

def format_insight_message(insight_data):
    """Format insight data into human-readable message"""
    primary = insight_data.get('primary', 'System operating normally')
    details = insight_data.get('details', [])
    recommendations = insight_data.get('recommendations', [])
    
    message_parts = [primary]
    
    if details:
        message_parts.extend(details[:2])  # Limit details
    
    if recommendations:
        message_parts.append(" | " + " | ".join(recommendations[:2]))  # Limit recommendations
    
    return " | ".join(message_parts)
