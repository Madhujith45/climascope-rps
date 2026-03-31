import React from 'react'
import { PageHeader } from '../components/PageHeader'

export default function Analytics() {
  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="Deep Analytics" subtitle="Advanced historical data and trends." />
      
      <div className="glass-card p-10 flex flex-col items-center justify-center text-center h-96">
        <div className="text-4xl mb-4">📈</div>
        <h3 className="text-lg font-semibold text-white mb-2">Historical Analytics Coming Soon</h3>
        <p className="text-sm text-gray-400 max-w-sm">We're building advanced reporting charts to let you analyze your data across weeks and months.</p>
      </div>
    </div>
  )
}
