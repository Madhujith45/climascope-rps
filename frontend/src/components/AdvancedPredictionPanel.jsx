/**
 * ClimaScope - Advanced AI Prediction Panel
 * 
 * Displays intelligent predictions with anomaly detection, health scores,
 * and comprehensive insights from the enhanced ML system.
 */

import React, { useState, useEffect } from 'react'
import { getPrediction, getModelStatus } from '../services/api'

function AdvancedPredictionPanel({ sensorData }) {
  const [prediction, setPrediction] = useState(null)
  const [modelStatus, setModelStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load model status on component mount
  useEffect(() => {
    const loadModelStatus = async () => {
      try {
        const status = await getModelStatus()
        setModelStatus(status)
      } catch (err) {
        console.error('Failed to load model status:', err)
      }
    }
    loadModelStatus()
  }, [])

  // Get prediction when sensor data changes
  useEffect(() => {
    if (!sensorData) return

    const fetchPrediction = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const reading = {
          temperature: sensorData.temperature || 0,
          humidity: sensorData.humidity || 50,
          pressure: sensorData.pressure || 1013,
          gas_voltage: sensorData.mq2_voltage || 1.5,
          gas_ppm: sensorData.gas_ppm || 200
        }
        
        const result = await getPrediction(reading)
        setPrediction(result)
      } catch (err) {
        setError(err.message || 'Advanced prediction failed')
      } finally {
        setLoading(false)
      }
    }

    fetchPrediction()
  }, [sensorData])

  const getStatusColor = (status) => {
    switch (status) {
      case 'normal': return 'text-green-400 bg-green-950/30 border-green-800/50'
      case 'warning': return 'text-yellow-400 bg-yellow-950/30 border-yellow-800/50'
      case 'danger': return 'text-red-400 bg-red-950/30 border-red-800/50'
      default: return 'text-gray-400 bg-gray-950/30 border-gray-800/50'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'normal':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'warning':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        )
      case 'danger':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      default:
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  const getHealthColor = (score) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 50) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getHealthIcon = (score) => {
    if (score >= 80) return 'LOW'
    if (score >= 50) return 'MED'
    return 'HIGH'
  }

  const getAnomalyColor = (score) => {
    if (score > 0.1) return 'text-red-400'
    if (score < -0.1) return 'text-green-400'
    return 'text-yellow-400'
  }

  if (!sensorData) {
    return (
      <div className="rounded-2xl border p-4 backdrop-blur-xl"
           style={{ background: 'linear-gradient(135deg, rgba(200,168,64,0.12), rgba(200,168,64,0.05)), rgba(30, 35, 20, 0.65)', borderColor: 'rgba(138, 128, 96, 0.2)', boxShadow: '0 8px 32px rgba(0,0,0,0.4), 0 0 30px rgba(200,168,64,0.18)' }}>
        <div className="text-center text-gray-500 text-sm">
          No sensor data available for advanced prediction
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border p-4 backdrop-blur-xl"
         style={{ background: 'linear-gradient(135deg, rgba(200,168,64,0.12), rgba(200,168,64,0.05)), rgba(30, 35, 20, 0.65)', borderColor: 'rgba(138, 128, 96, 0.2)', boxShadow: '0 8px 32px rgba(0,0,0,0.4), 0 0 30px rgba(200,168,64,0.18)' }}>
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Advanced AI Intelligence</h3>
        {modelStatus && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className={`h-2 w-2 rounded-full ${modelStatus.model_loaded ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>Dual Models</span>
          </div>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-800/50 bg-red-950/30 px-3 py-2 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="mb-4 text-center text-gray-400 text-sm">
          <div className="inline-flex items-center gap-2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-600 border-t-yellow-400" />
            Computing advanced prediction...
          </div>
        </div>
      )}

      {/* Advanced Prediction Result */}
      {prediction && !loading && (
        <div className="space-y-4">
          {/* Main Prediction */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-gray-500 mb-1">Temperature Prediction</div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">
                {prediction.prediction?.toFixed(1)}°C
              </div>
            </div>
            <div className={`px-3 py-2 rounded-full border flex items-center gap-2 ${getStatusColor(prediction.status)}`}>
              {getStatusIcon(prediction.status)}
              <span className="text-xs font-medium capitalize">{prediction.status}</span>
            </div>
          </div>

          {/* Health Score */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-1">
              <div className="text-xs text-gray-500 mb-2">System Health Score</div>
              <div className="flex items-center gap-3">
                <div className="text-3xl font-bold">
                  <span className={getHealthColor(prediction.health_score)}>
                    {getHealthIcon(prediction.health_score)} {prediction.health_score}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="h-2 w-full bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-300 ${
                        prediction.health_score >= 80 ? 'bg-green-500' : 
                        prediction.health_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${prediction.health_score}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {prediction.health_score >= 80 ? 'Excellent' : 
                 prediction.health_score >= 50 ? 'Fair' : 'Critical'}
              </div>
            </div>

            {/* Anomaly Detection */}
            <div className="col-span-1">
              <div className="text-xs text-gray-500 mb-2">Anomaly Detection</div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Status:</span>
                  <span className={`text-xs font-medium ${prediction.anomaly ? 'text-red-400' : 'text-green-400'}`}>
                    {prediction.anomaly ? 'WARNING ANOMALY' : 'OK Normal'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Score:</span>
                  <span className={`text-xs font-medium ${getAnomalyColor(prediction.anomaly_score)}`}>
                    {prediction.anomaly_score?.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Confidence Score */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Confidence</span>
            <div className="flex items-center gap-2">
              <div className="h-2 w-20 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-300 ${
                    prediction.confidence >= 0.8 ? 'bg-green-500' : 
                    prediction.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${(prediction.confidence || 0) * 100}%` }}
                />
              </div>
              <span className={`text-xs font-medium ${
                prediction.confidence >= 0.8 ? 'text-green-400' : 
                prediction.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {Math.round((prediction.confidence || 0) * 100)}%
              </span>
            </div>
          </div>

          {/* Advanced Insights */}
          {prediction.insight && (
            <div className="rounded-lg border border-gray-800 bg-gray-800/30 px-3 py-3">
              <div className="text-xs text-gray-400 mb-2 flex items-center gap-2">
                <span>AI AI Insights</span>
              </div>
              <div className="text-xs text-gray-300 leading-relaxed">
                {prediction.insight}
              </div>
            </div>
          )}

          {/* Timestamp */}
          {prediction.timestamp && (
            <div className="text-xs text-gray-600 text-right">
              Analyzed at {new Date(prediction.timestamp).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}

      {/* Model Info */}
      {modelStatus && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <div className="text-xs text-gray-600">
            <div className="mb-2 font-semibold text-gray-400">Model Information</div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>Regression:</span>
                  <span className="text-gray-400">{modelStatus.regression_model_type}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span>Anomaly:</span>
                  <span className="text-gray-400">{modelStatus.anomaly_model_type}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>Features:</span>
                  <span className="text-gray-400">{modelStatus.feature_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Target:</span>
                  <span className="text-gray-400">{modelStatus.target_variable}</span>
                </div>
              </div>
            </div>
            {modelStatus.last_trained && (
              <div className="mt-2 text-center text-gray-500">
                Last trained: {new Date(modelStatus.last_trained).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AdvancedPredictionPanel




