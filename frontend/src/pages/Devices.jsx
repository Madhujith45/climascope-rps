import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { getAuthToken } from '../services/auth';
import toast from 'react-hot-toast';

const BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshCount, setRefreshCount] = useState(0);

  useEffect(() => {
    fetchDevices();
  }, []);

  // Auto-refresh every 10 seconds to catch newly created devices
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDevices();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchDevices = async () => {
    try {
      // Use public endpoint - no authentication required
      // Backend computes online/offline status based on last_seen timestamp
      const res = await fetch(`${BASE_URL}/api/devices/all`);
      
      if (res.ok) {
        const data = await res.json();
        // Extract devices from DeviceListResponse { devices: [...], total: N }
        const deviceList = data.devices || [];
        setDevices(deviceList.filter(d => d)); // Filter out nulls
      } else if (res.status === 404 || res.status === 400) {
        // No devices created yet - show empty state
        setDevices([]);
      } else {
        // Other error - log but still show empty state
        console.error(`Failed to fetch devices: ${res.status}`);
        setDevices([]);
      }
    } catch (err) {
      console.error(err);
      // Don't show toast error for network errors - just silently show empty state
      // This allows the page to function even if backend is temporarily unavailable
      setDevices([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <div className="flex justify-between items-start mb-6">
        <PageHeader 
          title="Hardware Nodes" 
          subtitle="Manage and monitor physical Raspberry Pi Edge endpoints." 
        />
        <button
          onClick={() => {
            setLoading(true);
            fetchDevices();
          }}
          disabled={loading}
          className="px-3 py-1 text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded hover:bg-yellow-500/30 transition-colors disabled:opacity-50 font-mono"
        >
          {loading ? 'SCANNING...' : 'REFRESH'}
        </button>
      </div>
      
      {loading ? (
        <div className="flex h-32 items-center justify-center text-gray-400 font-mono">
          SCANNING MESH...
        </div>
      ) : devices.length === 0 ? (
        <div className="glass-card p-8 text-center text-gray-400">
          <div className="text-4xl mb-3 opacity-50">N/A</div>
          <p>No external hardware configured.</p>
          <div className="mt-4 text-xs font-mono opacity-60">Install and link edge/main.py on the Pi</div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {devices.map(device => (
            <div key={device.device_id} className="glass-card p-6 border-l-4 border-l-yellow-500 hover:-translate-y-1 transition-transform">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold font-mono text-yellow-400">
                  {device.device_name || device.device_id.toUpperCase()}
                </h3>
                <span className={`px-2 py-1 text-xs rounded-full font-mono ${
                  device.status === 'online' 
                    ? 'bg-green-500/20 text-green-400' 
                    : device.status === 'slow'
                    ? 'bg-yellow-500/20 text-yellow-400'
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {(device.status || 'offline').toUpperCase()}
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-gray-300">
                <div className="flex justify-between">
                  <span>Device ID:</span>
                  <span className="font-mono text-green-400">{device.device_id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Location:</span>
                  <span>{device.location || 'Default'}</span>
                </div>
                {device.last_seen && (
                  <div className="flex justify-between">
                    <span>Last Seen:</span>
                    <span className="font-mono text-xs">{new Date(device.last_seen).toLocaleTimeString()}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Active:</span>
                  <span>{device.is_active ? '✓ Yes' : '✗ No'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

