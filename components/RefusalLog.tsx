
import React from 'react';
import { WorkUnit } from '../types';

interface RefusalLogProps {
  history: WorkUnit[];
}

export const RefusalLog: React.FC<RefusalLogProps> = ({ history }) => {
  return (
    <div className="flex flex-col h-full">
      <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500 mb-4 px-4">Event Stream</h3>
      <div className="flex-1 overflow-y-auto space-y-2 px-4 pb-4">
        {history.slice(-20).reverse().map((work) => (
          <div 
            key={work.id}
            className={`p-3 rounded text-sm mono border flex justify-between items-center transition-all duration-300 ${
              work.status === 'REFUSED' 
                ? 'bg-red-950/20 border-red-900/40 text-red-400' 
                : work.status === 'FAILED'
                ? 'bg-zinc-800 border-dashed border-red-500 text-red-500'
                : 'bg-green-950/20 border-green-900/40 text-green-400'
            }`}
          >
            <div>
              <span className="opacity-50 mr-2">[{new Date(work.timestamp).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' })}]</span>
              <span className="font-semibold uppercase">{work.status}</span>
            </div>
            <div className="text-right">
              {work.reason || `Payload: ${work.payload}`}
            </div>
          </div>
        ))}
        {history.length === 0 && (
          <div className="text-zinc-600 italic text-center py-10">No events recorded. System idle.</div>
        )}
      </div>
    </div>
  );
};
