import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { getAuthToken } from '../services/auth';
import toast from 'react-hot-toast';

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const token = getAuthToken();
      const res = await fetch('/api/devices', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDevices(data.devices || []);
      }
    } catch (err) {
      console.error(err);
      toast.error('Failed to load edge hardware.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader 
        title="Hardware Nodes" 
        subtitle="Manage and monitor physical Raspberry Pi Edge endpoints." 
      />
      
      {loading ? (
        <div className="flex h-32 items-center justify-center text-gray-400 font-mono">
          SCANNING MESH...
        </div>
      ) : devices.length === 0 ? (
        <div className="glass-card p-8 text-center text-gray-400">
          <div className="text-4xl mb-3 opacity-50">??</div>
          <p>No external hardware configured.</p>
          <div className="mt-4 text-xs font-mono opacity-60">Install and link edge/main.py on the Pi</div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {devices.map(device => (
            <div key={device.device_id} className="glass-card p-6 border-l-4 border-l-blue-500 hover:-translate-y-1 transition-transform">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold font-mono text-blue-400">
                  {device.device_id.toUpperCase()}
                </h3>
                <span className={`px-2 py-1 text-xs rounded-full ${device.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {device.status.toUpperCase()}
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-gray-300">
                <div className="flex justify-between">
                  <span>Sensors:</span>
                  <span className="font-mono text-emerald-400">BMP, DHT, MQ</span>
                </div>
                <div className="flex justify-between">
                  <span>Location:</span>
                  <span>{device.location || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Uptime:</span>
                  <span>System Nominal</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
