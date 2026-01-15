
import React from 'react';
import { ControlMode } from '../types';
import { Shield, Activity, Binary, Scale, Target } from 'lucide-react';

interface AnalysisPanelProps {
  mode: ControlMode;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ mode }) => {
  const isBounded = mode === ControlMode.BOUNDED;

  return (
    <div className="glass rounded-[2.5rem] p-10 border-l-4 border-l-zinc-900 border border-white/5 shadow-2xl">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Scale className="w-6 h-6 text-zinc-700" />
          <h3 className="text-[12px] font-black uppercase tracking-[0.3em] text-zinc-600">Architectural Differential</h3>
        </div>
        <div className="px-4 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-[9px] font-black text-zinc-700 uppercase tracking-widest">
          Control Paradigm Analysis
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <div className={`space-y-6 transition-all duration-1000 ${!isBounded ? 'opacity-100 scale-100' : 'opacity-10 scale-95 grayscale'}`}>
          <div className="flex items-center gap-3 text-red-500 font-black text-[11px] uppercase tracking-tighter">
            <Activity className="w-4 h-4" /> Reactive-Failure Logic
          </div>
          <div className="bg-red-950/5 border border-red-900/10 p-6 rounded-[1.5rem] space-y-4">
            <p className="text-[12px] text-zinc-600 leading-relaxed font-medium">
              "System identifies state corruption only after execution. Entropy is treated as an inevitable noise factor to be caught via post-facto exception handling."
            </p>
            <div className="space-y-3 mono text-[10px] text-red-400/50 uppercase font-black tracking-tight">
              <div className="flex justify-between border-b border-red-900/10 pb-2"><span>Error Model:</span> <span>Catch-and-Recover</span></div>
              <div className="flex justify-between border-b border-red-900/10 pb-2"><span>State Trust:</span> <span>Optimistic</span></div>
              <div className="flex justify-between"><span>Entropy Impact:</span> <span>Unbounded Leak</span></div>
            </div>
          </div>
        </div>

        <div className={`space-y-6 transition-all duration-1000 ${isBounded ? 'opacity-100 scale-100' : 'opacity-15 scale-95'}`}>
          <div className="flex items-center gap-3 text-emerald-500 font-black text-[11px] uppercase tracking-tighter">
            <Target className="w-4 h-4" /> Entropy-Bounded Logic
          </div>
          <div className="bg-emerald-950/5 border border-emerald-900/10 p-6 rounded-[1.5rem] shadow-inner space-y-4">
            <p className="text-[12px] text-zinc-300 leading-relaxed font-bold italic">
              "Entropy is rendered operationally irrelevant through deterministic admission control. State transitions are projected against invariants (I) prior to commitment."
            </p>
            <div className="space-y-3 mono text-[10px] text-emerald-400 uppercase font-black tracking-tight">
              <div className="flex justify-between border-b border-emerald-900/10 pb-2"><span>Error Model:</span> <span>Admission-Preempt</span></div>
              <div className="flex justify-between border-b border-emerald-900/10 pb-2"><span>State Trust:</span> <span>Guaranteed</span></div>
              <div className="flex justify-between"><span>Entropy Impact:</span> <span>Boundary Contained</span></div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-10 flex justify-center items-center gap-8">
        <div className="h-[1px] flex-1 bg-zinc-900" />
        <div className="flex items-center gap-3 text-[10px] font-black text-zinc-800 uppercase mono tracking-[0.2em]">
          <Binary className="w-4 h-4" /> Deterministic Consistency Layer Active
        </div>
        <div className="h-[1px] flex-1 bg-zinc-900" />
      </div>
    </div>
  );
};
