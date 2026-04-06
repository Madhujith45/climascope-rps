import React, { useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { getAuthToken } from '../services/auth';
import toast from 'react-hot-toast';

const BASE_URL = import.meta.env.VITE_BACKEND_URL;

function getRaw(reading) {
  return reading?.raw || {};
}

function getProcessed(reading) {
  return reading?.processed || {};
}

export default function Reports() {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadCSV = async () => {
    setDownloading(true);
    try {
      const token = getAuthToken();
      // Fetch a larger chunk for reports
      const res = await fetch(`${BASE_URL}/api/data/history?limit=1000`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch data for report');
      const data = await res.json();
      
      const records = (data.records || []).map((reading) => ({
        ...reading,
        temperature: getRaw(reading).temperature,
        humidity: getRaw(reading).humidity,
        pressure: getRaw(reading).pressure,
        gas_ppm: getProcessed(reading).gas_ppm ?? getRaw(reading).gas,
        risk_score: getProcessed(reading).risk_score,
        anomaly: getProcessed(reading).anomaly,
      }));
      if (records.length === 0) {
        toast.error('No data available to export.');
        return;
      }

      // Generate CSV
      const headers = ['Timestamp', 'Device ID', 'Temperature', 'Humidity', 'Pressure', 'Gas(ppm)', 'Risk Score', 'Anomaly'];
      const csvRows = [];
      csvRows.push(headers.join(','));

      for (const row of records) {
        const values = [
          row.timestamp,
          row.device_id || 'unassigned',
          row.temperature,
          row.humidity,
          row.pressure,
          row.gas_ppm ?? row.gas ?? 0,
          row.risk_score,
          row.anomaly
        ];
        csvRows.push(values.join(','));
      }

      const csvString = csvRows.join('\n');
      const blob = new Blob([csvString], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `climascope_report_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      toast.success('CSV Report generated!');
    } catch (err) {
      toast.error(err.message || 'Error generating report');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="Export Reports" subtitle="Generate detailed CSV summaries of your environmental data." />
      
      <div className="glass-card p-10 flex flex-col items-center justify-center text-center h-96">
        <div className="text-4xl mb-4">N/A</div>
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Download Data Export</h3>
        <p className="text-sm text-gray-400 max-w-sm mb-6">
          Export the last 1000 sensor readings into a CSV file for external analysis, auditing, or compliance tracking.
        </p>
        
        <button 
          onClick={handleDownloadCSV}
          disabled={downloading}
          className="auth-btn px-6 py-2 text-sm max-w-[200px]"
        >
          {downloading ? 'Preparing...' : 'Download CSV'}
        </button>
      </div>
    </div>
  );
}


