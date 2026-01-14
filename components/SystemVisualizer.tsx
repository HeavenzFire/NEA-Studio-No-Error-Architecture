
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { SystemState } from '../types';

interface SystemVisualizerProps {
  data: any[];
}

export const SystemVisualizer: React.FC<SystemVisualizerProps> = ({ data }) => {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorCoherence" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorEntropy" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
          <XAxis 
            dataKey="time" 
            hide 
          />
          <YAxis 
            domain={[0, 100]} 
            stroke="#525252" 
            fontSize={10} 
            tickFormatter={(val) => `${val}%`}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#171717', border: '1px solid #404040', fontSize: '12px' }}
            itemStyle={{ color: '#e5e5e5' }}
          />
          <Area 
            type="monotone" 
            dataKey="coherence" 
            stroke="#22c55e" 
            fillOpacity={1} 
            fill="url(#colorCoherence)" 
            strokeWidth={2}
            name="Coherence"
          />
          <Area 
            type="monotone" 
            dataKey="entropy" 
            stroke="#ef4444" 
            fillOpacity={1} 
            fill="url(#colorEntropy)" 
            strokeWidth={2}
            name="Entropy"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
