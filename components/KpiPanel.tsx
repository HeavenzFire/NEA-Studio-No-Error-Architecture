
import React from 'react';
import { KpiMetrics } from '../types';
import { TrendingUp, Target, ShieldAlert, Zap } from 'lucide-react';

interface KpiPanelProps {
  kpis: KpiMetrics;
  coherence: number;
}

export const KpiPanel: React.FC<KpiPanelProps> = ({ kpis, coherence }) => {
  const formatPercent = (val: number) => `${val.toFixed(1)}%`;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="glass p-4 rounded-xl border-l-4 border-l-green-500">
        <div className="flex items-center gap-2 mb-1">
          <Target className="w-4 h-4 text-green-500" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Coherence</span>
        </div>
        <div className="text-2xl font-bold text-white mono">{formatPercent(coherence)}</div>
        <div className="text-[9px] text-zinc-600 uppercase font-medium">System Integrity</div>
      </div>

      <div className="glass p-4 rounded-xl border-l-4 border-l-blue-500">
        <div className="flex items-center gap-2 mb-1">
          <TrendingUp className="w-4 h-4 text-blue-500" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Admissions</span>
        </div>
        <div className="text-2xl font-bold text-white mono">{formatPercent(kpis.admissionRate)}</div>
        <div className="text-[9px] text-zinc-600 uppercase font-medium">Pre-Admission Flow</div>
      </div>

      <div className="glass p-4 rounded-xl border-l-4 border-l-red-500">
        <div className="flex items-center gap-2 mb-1">
          <ShieldAlert className="w-4 h-4 text-red-500" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Failed States</span>
        </div>
        <div className="text-2xl font-bold text-white mono">{formatPercent(kpis.failureRate)}</div>
        <div className="text-[9px] text-zinc-600 uppercase font-medium">Incoherent States</div>
      </div>

      <div className="glass p-4 rounded-xl border-l-4 border-l-amber-500">
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-4 h-4 text-amber-500" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Throughput</span>
        </div>
        <div className="text-2xl font-bold text-white mono">{kpis.totalRequests}</div>
        <div className="text-[9px] text-zinc-600 uppercase font-medium">Processed Units</div>
      </div>
    </div>
  );
};
