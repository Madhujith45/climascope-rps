import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { getAuthToken } from '../services/auth';
import toast from 'react-hot-toast';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function Analytics() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = getAuthToken();
        const res = await fetch('/api/data/history?limit=100', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch historical data');
        const data = await res.json();
        // Data usually returned as newest first, so reverse for chart (oldest to newest left to right)
        setHistory((data.records || []).reverse());
      } catch (err) {
        toast.error('Error loading deep analytics');
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    elements: { point: { radius: 0 } },
    scales: {
      x: { grid: { display: false, color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } }
    },
    plugins: {
      legend: { labels: { color: 'rgba(255,255,255,0.7)' } }
    }
  };

  const labels = history.map(d => new Date(d.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}));
  
  const envData = {
    labels,
    datasets: [
      {
        label: 'Temperature (°C)',
        data: history.map(d => d.temperature),
        borderColor: '#2dd4bf',
        backgroundColor: 'rgba(45, 212, 191, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Humidity (%)',
        data: history.map(d => d.humidity),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Gas (ppm)',
        data: history.map(d => d.gas_ppm || d.gas || 0),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4,
        fill: true,
      }
    ],
  };

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="Deep Analytics" subtitle="Advanced historical data and trends over time." />

      {loading ? (
        <div className="glass-card p-10 flex flex-col items-center justify-center text-center h-96 skeleton rounded-2xl" />
      ) : history.length === 0 ? (
        <div className="glass-card p-10 flex flex-col items-center justify-center text-center h-96">
          <div className="text-4xl mb-4">??</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Data Available Yet</h3>
          <p className="text-sm text-gray-400 max-w-sm">Connect a device to start recording analytics over time.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="glass-card p-6" style={{ height: '400px' }}>
            <h3 className="text-sm font-semibold text-white mb-4">Multivariate Timeline (Last 100 entries)</h3>
            <Line data={envData} options={chartOptions} />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-white mb-4">Risk Variance</h3>
              <div style={{ height: '240px' }}>
                <Line 
                  options={chartOptions} 
                  data={{
                    labels,
                    datasets: [{
                      label: 'Risk Score (0-100)',
                      data: history.map(d => d.risk_score),
                      borderColor: '#ef4444',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      tension: 0.4,
                      fill: true,
                    }]
                  }} 
                />
              </div>
            </div>
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-white mb-4">Atmospheric Pressure</h3>
              <div style={{ height: '240px' }}>
                <Line 
                  options={chartOptions} 
                  data={{
                    labels,
                    datasets: [{
                      label: 'Pressure (hPa)',
                      data: history.map(d => d.pressure),
                      borderColor: '#8b5cf6',
                      tension: 0.4
                    }]
                  }} 
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
