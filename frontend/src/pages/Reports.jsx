import React from 'react'
import { PageHeader } from '../components/PageHeader'

export default function Reports() {
  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="Export Reports" subtitle="Generate CSV and PDF summaries." />
      
      <div className="glass-card p-10 flex flex-col items-center justify-center text-center h-96">
        <div className="text-4xl mb-4">📑</div>
        <h3 className="text-lg font-semibold text-white mb-2">Reports module under construction</h3>
        <p className="text-sm text-gray-400 max-w-sm">Scheduled PDF and CSV exports are coming in the next update.</p>
      </div>
    </div>
  )
}
