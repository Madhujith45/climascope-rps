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

const REFRESH_MS = 10_000;
const BASE_URL = import.meta.env.VITE_BACKEND_URL;

function getRaw(reading) {
  return reading?.raw || {};
}

function getProcessed(reading) {
  return reading?.processed || {};
}

export default function Analytics() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = getAuthToken();
        const res = await fetch(`${BASE_URL}/api/data/history?limit=100`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch historical data');
        const data = await res.json();
        // Enforce timeline order so charts render left->right oldest to newest.
        const records = Array.isArray(data.records) ? data.records : [];
        const normalized = records.map((reading) => ({
          ...reading,
          temperature: getRaw(reading).temperature,
          humidity: getRaw(reading).humidity,
          pressure: getRaw(reading).pressure,
          gas_ppm: getProcessed(reading).gas_ppm ?? getRaw(reading).gas,
          risk_score: getProcessed(reading).risk_score,
          anomaly: getProcessed(reading).anomaly,
        }));
        normalized.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        setHistory(normalized);
      } catch (err) {
        toast.error('Error loading deep analytics');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
    const id = setInterval(fetchHistory, REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    elements: { point: { radius: 0 } },
    scales: {
      x: {
        grid: { display: false, color: 'rgba(255,255,255,0.05)' },
        ticks: { color: 'rgba(255,255,255,0.5)', autoSkip: true, maxTicksLimit: 10 }
      },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } }
    },
    plugins: {
      legend: { labels: { color: 'rgba(255,255,255,0.7)' } },
      tooltip: {
        callbacks: {
          title: (items) => {
            if (!items?.length) return ''
            const idx = items[0].dataIndex
            const ts = history[idx]?.timestamp
            return ts ? new Date(ts).toLocaleString() : ''
          }
        }
      }
    }
  };

  const labels = history.map(d => new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
  
  const envData = {
    labels,
    datasets: [
      {
        label: 'Temperature (°C)',
        data: history.map(d => d.temperature),
        borderColor: '#4a8040',
        backgroundColor: 'rgba(45, 212, 191, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Humidity (%)',
        data: history.map(d => d.humidity),
        borderColor: '#4a8040',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Gas (ppm)',
        data: history.map(d => d.gas_ppm ?? d.gas ?? 0),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4,
        fill: true,
      }
    ],
  };

  return (
    <div className="p-6 md:px-8 pb-10 page-in">
      <PageHeader title="Deep Analytics" subtitle="Advanced historical data and trends over time." />

      {loading ? (
        <div className="glass-card p-10 flex flex-col items-center justify-center text-center h-96 skeleton rounded-2xl" />
      ) : history.length === 0 ? (
        <div className="glass-card p-10 flex flex-col items-center justify-center text-center h-96">
          <div className="text-4xl mb-4">N/A</div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">No Data Available Yet</h3>
          <p className="text-sm text-gray-400 max-w-sm">Connect a device to start recording analytics over time.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div
            className="glass-card p-6"
            style={{ background: 'rgba(22, 26, 18, 0.84)', borderColor: 'rgba(184,134,11,0.32)' }}
          >
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Multivariate Timeline (Last 100 entries)</h3>
            <p className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
              Timeline is rendered from MongoDB logged timestamps (live Pi ingestion history).
            </p>
            <div style={{ height: '360px' }}>
              <Line data={envData} options={chartOptions} />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div
              className="glass-card p-6"
              style={{ background: 'rgba(22, 26, 18, 0.84)', borderColor: 'rgba(184,134,11,0.32)' }}
            >
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Risk Variance</h3>
              <div style={{ height: '240px' }}>
                <Line 
                  options={chartOptions} 
                  data={{
                    labels,
                    datasets: [{
                      label: 'Risk Score (0-100)',
                      data: history.map(d => d.risk_score ?? d.processed?.risk_score ?? 0),
                      borderColor: '#a04030',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      tension: 0.4,
                      fill: true,
                    }]
                  }} 
                />
              </div>
            </div>
            <div
              className="glass-card p-6"
              style={{ background: 'rgba(22, 26, 18, 0.84)', borderColor: 'rgba(184,134,11,0.32)' }}
            >
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Atmospheric Pressure</h3>
              <div style={{ height: '240px' }}>
                <Line 
                  options={chartOptions} 
                  data={{
                    labels,
                    datasets: [{
                      label: 'Pressure (hPa)',
                      data: history.map(d => d.pressure),
                      borderColor: '#b8860b',
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




