import React, { useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { getAuthToken } from '../services/auth';
import toast from 'react-hot-toast';

export default function Reports() {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadCSV = async () => {
    setDownloading(true);
    try {
      const token = getAuthToken();
      // Fetch a larger chunk for reports
      const res = await fetch('/api/data/history?limit=1000', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch data for report');
      const data = await res.json();
      
      const records = data.records || [];
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
          row.gas || row.gas_ppm || 0,
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
        <div className="text-4xl mb-4">??</div>
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


