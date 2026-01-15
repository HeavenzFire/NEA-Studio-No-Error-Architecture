
import React from 'react';
import { KpiMetrics } from '../types';
import { TrendingUp, Target, ShieldAlert, Zap, Binary, Activity } from 'lucide-react';

interface KpiPanelProps {
  kpis: KpiMetrics;
  coherence: number;
}

export const KpiPanel: React.FC<KpiPanelProps> = ({ kpis, coherence }) => {
  const formatPercent = (val: number) => `${val.toFixed(1)}%`;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="glass p-5 rounded-[1.5rem] border-l-4 border-l-emerald-500 border border-white/5">
        <div className="flex items-center gap-2 mb-1">
          <Binary className="w-4 h-4 text-emerald-500" />
          <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Syntropy (Φ)</span>
        </div>
        <div className="text-2xl font-black text-white mono">{kpis.syntropy.toFixed(2)}</div>
        <div className="text-[9px] text-zinc-700 uppercase font-bold">State Order Index</div>
      </div>

      <div className="glass p-5 rounded-[1.5rem] border-l-4 border-l-blue-500 border border-white/5">
        <div className="flex items-center gap-2 mb-1">
          <Activity className="w-4 h-4 text-blue-500" />
          <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Coverage</span>
        </div>
        <div className="text-2xl font-black text-white mono">{formatPercent(coherence)}</div>
        <div className="text-[9px] text-zinc-700 uppercase font-bold">Mapped State Space</div>
      </div>

      <div className="glass p-5 rounded-[1.5rem] border-l-4 border-l-amber-500 border border-white/5">
        <div className="flex items-center gap-2 mb-1">
          <Target className="w-4 h-4 text-amber-500" />
          <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Admissions</span>
        </div>
        <div className="text-2xl font-black text-white mono">{formatPercent(kpis.admissionRate)}</div>
        <div className="text-[9px] text-zinc-700 uppercase font-bold">Containment Yield</div>
      </div>

      <div className="glass p-5 rounded-[1.5rem] border-l-4 border-l-zinc-100 border border-white/5">
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-4 h-4 text-zinc-100" />
          <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Efficiency</span>
        </div>
        <div className="text-2xl font-black text-white mono">{kpis.opMultiplier.toFixed(2)}x</div>
        <div className="text-[9px] text-zinc-700 uppercase font-bold">Operational Multiplier</div>
      </div>
    </div>
  );
};
