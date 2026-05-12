import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { getAuthToken } from '../services/auth';
import toast from 'react-hot-toast';

const BASE_URL = import.meta.env.VITE_BACKEND_URL;

function parseServerTime(value) {
  if (!value) return null;
  let raw = value;
  if (typeof raw === 'object' && raw !== null && '$date' in raw) {
    raw = raw.$date;
  }
  if (typeof raw === 'string') {
    const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(raw);
    if (!hasTimezone) {
      raw = `${raw}Z`;
    }
  }
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatRelativeTime(value) {
  if (!value) return null;
  const diffMs = Date.now() - value.getTime();
  if (!Number.isFinite(diffMs) || diffMs < 0) return null;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours} hr ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} d ago`;
}

function getDeviceStatus(device) {
  const status = (device?.status || '').toLowerCase();
  if (status === 'online' || status === 'slow' || status === 'offline') {
    return status;
  }
  const lastSeen = parseServerTime(device?.last_seen);
  if (lastSeen) {
    const ageMs = Date.now() - lastSeen.getTime();
    if (ageMs <= 60000) return 'online';
    if (ageMs <= 300000) return 'slow';
    return 'offline';
  }
  return device?.is_active !== false ? 'online' : 'offline';
}

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
      // Try public endpoint first (no auth required).
      // If it is protected, fall back to the authenticated list endpoint.
      let res = await fetch(`${BASE_URL}/api/devices/all`);

      if (!res.ok && res.status === 401) {
        const token = getAuthToken();
        if (token) {
          res = await fetch(`${BASE_URL}/api/devices/list`, {
            headers: { Authorization: `Bearer ${token}` }
          });
        }
      }

      if (res.ok) {
        const data = await res.json();
        // Extract devices from DeviceListResponse { devices: [...], total: N }
        const deviceList = data.devices || [];
        setDevices(deviceList.filter(d => d));
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
                    {(() => {
                      const lastSeen = parseServerTime(device.last_seen);
                      const status = getDeviceStatus(device);
                      const label = status === 'offline'
                        ? formatRelativeTime(lastSeen)
                        : lastSeen?.toLocaleTimeString();
                      return (
                        <span className="font-mono text-xs">{label || '-'}</span>
                      );
                    })()}
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

