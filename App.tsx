
import React, { useState, useEffect, useCallback } from 'react';
import { ArchitectureMode, SystemState, WorkUnit, SystemConstraint } from './types';
import { SystemVisualizer } from './components/SystemVisualizer';
import { RefusalLog } from './components/RefusalLog';
import { KpiPanel } from './components/KpiPanel';
import { formalizeSpec } from './services/geminiService';
import { Activity, Shield, ShieldAlert, Cpu, Layers, Terminal, Zap, Info, ChevronRight, Play, FileText, Loader2 } from 'lucide-react';

const App: React.FC = () => {
  const [mode, setMode] = useState<ArchitectureMode>(ArchitectureMode.NO_ERROR);
  const [history, setHistory] = useState<WorkUnit[]>([]);
  const [stats, setStats] = useState<SystemState>({
    throughput: 0,
    coherence: 100,
    entropy: 0,
    activeWork: [],
    history: [],
    kpis: {
      admissionRate: 100,
      failureRate: 0,
      totalRequests: 0,
      avgPayload: 0
    }
  });
  const [chartData, setChartData] = useState<any[]>([]);
  const [specInput, setSpecInput] = useState('');
  const [generatedSpec, setGeneratedSpec] = useState<any>(null);
  const [loadingSpec, setLoadingSpec] = useState(false);

  // Simulation loop
  useEffect(() => {
    const timer = setInterval(() => {
      setStats(prev => {
        const currentActiveCount = prev.activeWork.length;
        
        // Entropy generation logic: Traditional mode increases entropy with load
        // NEA mode stays at 0 entropy because it refuses unstable work
        const entropyIncrement = mode === ArchitectureMode.TRADITIONAL 
          ? (currentActiveCount * 2.5) 
          : 0;
        
        const newEntropy = Math.min(100, Math.max(0, prev.entropy + (entropyIncrement - 5))); // -5 for natural decay
        const newCoherence = 100 - newEntropy;
        
        // Process active work
        const updatedActiveWork = prev.activeWork
          .map(w => ({ ...w, payload: w.payload - 15 }))
          .filter(w => w.payload > 0);
        
        // Track completed units
        const finished = prev.activeWork.filter(w => w.payload <= 0);
        if (finished.length > 0) {
          setHistory(h => [...h, ...finished.map(f => ({ ...f, status: 'COMPLETED' as const }))]);
        }

        // Calculate real-time KPIs from history
        const last100 = [...history.slice(-100)];
        const admissions = last100.filter(w => w.status === 'ADMITTED' || w.status === 'COMPLETED').length;
        const failures = last100.filter(w => w.status === 'FAILED').length;
        const total = last100.length || 1;

        return {
          ...prev,
          activeWork: updatedActiveWork,
          entropy: newEntropy,
          coherence: newCoherence,
          throughput: finished.length * 10,
          kpis: {
            admissionRate: (admissions / total) * 100,
            failureRate: (failures / total) * 100,
            totalRequests: prev.history.length + finished.length,
            avgPayload: 0 // placeholder
          }
        };
      });
    }, 800);

    return () => clearInterval(timer);
  }, [mode, history]);

  // Chart data sync
  useEffect(() => {
    const timer = setInterval(() => {
      setChartData(prev => {
        const newData = [...prev, {
          time: new Date().toLocaleTimeString(),
          coherence: stats.coherence,
          entropy: stats.entropy,
          throughput: stats.throughput
        }].slice(-40);
        return newData;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [stats]);

  const requestWork = useCallback(() => {
    const payload = Math.floor(Math.random() * 60) + 30;
    const workId = `REQ-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;
    
    // NO-ERROR ARCHITECTURE ADMISSION CONTROL
    if (mode === ArchitectureMode.NO_ERROR) {
      const capacityThreshold = 4;
      const instabilityThreshold = 10; // NEA refuses if any entropy is detected

      const isOverloaded = stats.activeWork.length >= capacityThreshold;
      const isUnstable = stats.entropy > instabilityThreshold;

      if (isOverloaded || isUnstable) {
        const reason = isOverloaded ? 'SATURATION_REJECT' : 'UNSTABLE_STATE_REFUSAL';
        setHistory(h => [...h, { 
          id: workId, 
          payload, 
          timestamp: Date.now(), 
          status: 'REFUSED',
          reason 
        }]);
        return;
      }
    }

    // ADMISSION GRANTED
    const newWork: WorkUnit = {
      id: workId,
      payload,
      timestamp: Date.now(),
      status: 'ADMITTED'
    };

    setStats(prev => ({
      ...prev,
      activeWork: [...prev.activeWork, newWork]
    }));

    // TRADITIONAL MODE: Risk of failure during execution
    if (mode === ArchitectureMode.TRADITIONAL) {
      const failureRisk = (stats.entropy / 100) + 0.05; // Base 5% risk + entropy scaling
      if (Math.random() < failureRisk) {
        setTimeout(() => {
          setStats(prev => ({
            ...prev,
            activeWork: prev.activeWork.filter(w => w.id !== workId)
          }));
          setHistory(h => [...h, { ...newWork, status: 'FAILED', reason: 'RUN-TIME_EXCEPTION' }]);
        }, 300);
      }
    }
  }, [mode, stats.activeWork.length, stats.entropy]);

  const handleGenerateSpec = async () => {
    if (!specInput.trim()) return;
    setLoadingSpec(true);
    try {
      const result = await formalizeSpec(specInput);
      setGeneratedSpec(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSpec(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-zinc-300 selection:bg-green-500/30 flex flex-col">
      {/* Engineering Header */}
      <header className="border-b border-zinc-900 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-7 h-7 bg-green-500 rounded flex items-center justify-center">
              <Shield className="text-black w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <h1 className="font-bold tracking-tighter text-white uppercase text-sm">NEA Studio</h1>
              <span className="text-[9px] text-zinc-500 mono leading-none tracking-widest">NO-ERROR ARCHITECTURE LAB</span>
            </div>
          </div>

          <div className="flex items-center gap-1 bg-zinc-900/50 p-1 rounded-lg border border-zinc-800">
            <button 
              onClick={() => setMode(ArchitectureMode.TRADITIONAL)}
              className={`px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all ${
                mode === ArchitectureMode.TRADITIONAL 
                  ? 'bg-red-500 text-black shadow-lg shadow-red-500/20' 
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Traditional
            </button>
            <button 
              onClick={() => setMode(ArchitectureMode.NO_ERROR)}
              className={`px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all ${
                mode === ArchitectureMode.NO_ERROR 
                  ? 'bg-green-500 text-black shadow-lg shadow-green-500/20' 
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              No-Error
            </button>
          </div>
        </div>
      </header>

      {/* Primary Dashboard Layout */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6 grid grid-cols-12 gap-6">
        
        {/* Left: Operational Metrics & Controls */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <section className="glass rounded-xl p-5 overflow-hidden relative">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500 flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5" /> Admission Control
              </h2>
              <div className={`w-2 h-2 rounded-full animate-pulse ${mode === ArchitectureMode.NO_ERROR ? 'bg-green-500' : 'bg-red-500'}`} />
            </div>
            
            <button 
              onClick={requestWork}
              className="w-full py-4 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-xl flex items-center justify-center gap-3 group transition-all"
            >
              <Zap className="w-4 h-4 text-amber-500 group-active:scale-125 transition-transform" />
              <span className="font-bold text-xs uppercase tracking-widest">Inject Work Unit</span>
            </button>

            <div className="mt-8 space-y-4">
              <div className="flex justify-between items-end border-b border-zinc-900 pb-2">
                <span className="text-[10px] uppercase text-zinc-500 font-bold">In-Flight Units</span>
                <span className="text-xl font-bold mono text-white">{stats.activeWork.length}</span>
              </div>
              <div className="flex justify-between items-end border-b border-zinc-900 pb-2">
                <span className="text-[10px] uppercase text-zinc-500 font-bold">System Load</span>
                <span className="text-xl font-bold mono text-white">{Math.round((stats.activeWork.length / 4) * 100)}%</span>
              </div>
            </div>
          </section>

          <section className="glass rounded-xl p-5">
            <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500 mb-4 flex items-center gap-2">
              <ShieldAlert className="w-3.5 h-3.5 text-zinc-500" /> System Constraints
            </h2>
            <div className="space-y-6">
              {[
                { label: 'Capacity', value: (stats.activeWork.length / 4) * 100, threshold: 100, unit: '%' },
                { label: 'Entropy', value: stats.entropy, threshold: 20, unit: '%' },
                { label: 'Consistency', value: stats.coherence, threshold: 100, unit: '%' },
              ].map((c) => (
                <div key={c.label} className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-bold uppercase tracking-tight">
                    <span className="text-zinc-500">{c.label}</span>
                    <span className={c.value > c.threshold ? 'text-red-500' : 'text-zinc-300'}>{Math.round(c.value)}{c.unit}</span>
                  </div>
                  <div className="h-1 bg-zinc-900 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 ${c.value > c.threshold ? 'bg-red-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min(100, c.value)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="p-4 bg-green-950/10 border border-green-900/30 rounded-xl">
             <div className="flex gap-3">
                <Info className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed text-zinc-400">
                  <span className="text-green-500 font-bold">NEA Logic:</span> Refusals occur <span className="text-white italic underline underline-offset-2">before</span> execution begins. If execution starts, completion is guaranteed.
                </p>
             </div>
          </section>
        </div>

        {/* Middle: Visualization & Logs */}
        <div className="col-span-12 lg:col-span-6 space-y-6">
          <KpiPanel kpis={stats.kpis} coherence={stats.coherence} />
          
          <section className="glass rounded-xl p-6 h-[400px] flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500 flex items-center gap-2">
                <Activity className="w-3.5 h-3.5" /> State Trajectory
              </h2>
              <div className="flex gap-4 text-[10px] font-bold uppercase">
                <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-green-500" /> Coherence</span>
                <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-red-500" /> Entropy</span>
              </div>
            </div>
            <div className="flex-1">
              <SystemVisualizer data={chartData} />
            </div>
          </section>

          <section className="glass rounded-xl h-[450px] overflow-hidden flex flex-col">
            <div className="p-4 border-b border-zinc-900 flex justify-between items-center bg-zinc-950/30">
              <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500 flex items-center gap-2">
                <Layers className="w-3.5 h-3.5" /> Immutable Event Stream
              </h2>
              <span className="text-[9px] mono text-zinc-600">RETAIN_LAST_100</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <RefusalLog history={history} />
            </div>
          </section>
        </div>

        {/* Right: Spec Generator & Knowledge Base */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <section className="glass rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-blue-500" />
              <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">NEA Formalizer</h2>
            </div>
            <p className="text-[11px] text-zinc-500">Transform informal system descriptions into rigid NEA specifications.</p>
            <textarea 
              value={specInput}
              onChange={(e) => setSpecInput(e.target.value)}
              placeholder="Describe your system (e.g. 'A high-frequency trading gateway')..."
              className="w-full h-32 bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-xs focus:ring-1 focus:ring-blue-500 outline-none resize-none placeholder:text-zinc-700"
            />
            <button 
              onClick={handleGenerateSpec}
              disabled={loadingSpec || !specInput}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 transition-all"
            >
              {loadingSpec ? <Loader2 className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3" />}
              Generate Engineering Spec
            </button>

            {generatedSpec && (
              <div className="mt-4 p-4 bg-blue-950/10 border border-blue-900/30 rounded-lg animate-in fade-in slide-in-from-top-2">
                <h3 className="text-[10px] font-bold uppercase text-blue-400 mb-2">{generatedSpec.systemName}</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-[9px] uppercase font-bold text-zinc-500 block">Admission Control</span>
                    <p className="text-[10px] leading-tight text-zinc-300 mt-1">{generatedSpec.refusalLogic}</p>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase font-bold text-zinc-500 block">Atomic Transitions</span>
                    <ul className="mt-1 space-y-1">
                      {generatedSpec.atomicTransitions.slice(0, 3).map((t: string, i: number) => (
                        <li key={i} className="text-[9px] text-zinc-400 flex items-start gap-1">
                          <div className="w-1 h-1 rounded-full bg-blue-500 mt-1 flex-shrink-0" />
                          {t}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </section>

          <section className="glass rounded-xl p-5 border-t-2 border-t-zinc-800">
            <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500 mb-4">Core Principles</h2>
            <div className="space-y-4">
              {[
                { title: "Refusals > Exceptions", text: "Errors occur after execution. Refusals occur before." },
                { title: "Total Transitions", text: "If execution begins, completion is guaranteed." },
                { title: "Metric Loops", text: "Observation and control are collapsed into a single cycle." }
              ].map((p, i) => (
                <div key={i} className="group">
                  <div className="text-[10px] font-bold uppercase text-zinc-300 group-hover:text-green-500 transition-colors mb-1">{p.title}</div>
                  <div className="text-[10px] text-zinc-600 leading-snug">{p.text}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
      
      {/* Simulation Footer */}
      <footer className="border-t border-zinc-900 bg-zinc-950/50 p-2 text-center">
        <div className="text-[9px] mono text-zinc-600 uppercase tracking-[0.3em]">
          Deterministic Coherence Simulation Active // Mode: {mode}
        </div>
      </footer>
    </div>
  );
};

export default App;
