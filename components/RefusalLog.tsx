
import React from 'react';
import { WorkUnit } from '../types';
import { ShieldAlert, Target, CheckCircle2, AlertTriangle } from 'lucide-react';

interface RefusalLogProps {
  history: WorkUnit[];
}

export const RefusalLog: React.FC<RefusalLogProps> = ({ history }) => {
  return (
    <div className="flex flex-col h-full bg-black/20">
      <div className="flex-1 overflow-y-auto space-y-1 px-4 py-4 scrollbar-hide">
        {history.slice(-25).reverse().map((work) => (
          <div 
            key={work.id}
            className={`px-4 py-2 text-[10px] mono flex items-center justify-between border-l-2 transition-all duration-300 ${
              work.status === 'PREEMPTED' 
                ? 'bg-amber-950/5 border-l-amber-500 text-amber-500/80' 
                : work.status === 'FAILED'
                ? 'bg-red-950/10 border-l-red-600 text-red-500'
                : work.status === 'ADMITTED'
                ? 'bg-blue-950/5 border-l-blue-500 text-blue-400'
                : 'bg-green-950/5 border-l-green-600 text-green-500/80'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="opacity-40 tabular-nums">[{new Date(work.timestamp).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' })}]</span>
              <span className="font-black uppercase tracking-widest min-w-[80px]">
                {work.status === 'PREEMPTED' ? 'PREEMPTED' : work.status}
              </span>
              <span className="opacity-30">|</span>
              <span className="opacity-60">{work.id}</span>
            </div>
            
            <div className="flex items-center gap-4">
              {work.status === 'PREEMPTED' && <Target className="w-3 h-3 opacity-50" />}
              {work.status === 'FAILED' && <ShieldAlert className="w-3 h-3 opacity-50" />}
              {work.status === 'COMPLETED' && <CheckCircle2 className="w-3 h-3 opacity-50" />}
              <span className="font-bold opacity-80">{work.reason || `V=${work.payload}`}</span>
            </div>
          </div>
        ))}
        {history.length === 0 && (
          <div className="text-zinc-800 font-black uppercase text-[10px] tracking-[0.5em] text-center py-32 animate-pulse">
            System Idle // Awaiting Invariant Trace
          </div>
        )}
      </div>
    </div>
  );
};
