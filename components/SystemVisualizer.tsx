
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface SystemVisualizerProps {
  data: any[];
}

export const SystemVisualizer: React.FC<SystemVisualizerProps> = ({ data }) => {
  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorSyntropy" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorEntropy" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#171717" vertical={false} />
          <XAxis 
            dataKey="time" 
            hide 
          />
          <YAxis 
            yAxisId="left"
            domain={[0, 100]} 
            stroke="#404040" 
            fontSize={9} 
            tickFormatter={(val) => `${val}%`}
            orientation="left"
          />
          <YAxis 
            yAxisId="right"
            domain={[0, 10]} 
            stroke="#10b981" 
            fontSize={9} 
            orientation="right"
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #262626', fontSize: '10px', borderRadius: '8px' }}
            itemStyle={{ color: '#a3a3a3' }}
          />
          <Area 
            yAxisId="left"
            type="monotone" 
            dataKey="entropy" 
            stroke="#ef4444" 
            fillOpacity={1} 
            fill="url(#colorEntropy)" 
            strokeWidth={1.5}
            name="Entropy (E)"
            dot={false}
          />
          <Area 
            yAxisId="right"
            type="monotone" 
            dataKey="syntropy" 
            stroke="#10b981" 
            fillOpacity={1} 
            fill="url(#colorSyntropy)" 
            strokeWidth={3}
            name="Syntropy (Φ)"
            dot={false}
          />
          <Line
            yAxisId="left"
            type="stepAfter"
            dataKey="safety_floor"
            stroke="#404040"
            strokeDasharray="5 5"
            name="Invariant Limit"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
