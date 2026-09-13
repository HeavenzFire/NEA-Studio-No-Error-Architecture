#!/usr/bin/env python3
"""
Synthetic Load-Test Suite for Hyper-Simulation Compression Engine
------------------------------------------------------------------
Stress tests the compression pipeline under maximum adversarial telemetry floods.

Test Scenarios:
1. EPS Ramp-Up: Gradually increase events/sec to find breaking point
2. Adversarial Flood: Inject burst anomalies at 10x normal rate
3. Multi-Swarm Concurrency: Simulate 1000+ swarms transmitting simultaneously
4. Memory Pressure Test: Run extended duration to test GC and archival
5. Compression Throughput Benchmark: Measure MB/sec compressed vs raw
"""

import time
import random
import math
import hashlib
import json
import statistics
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import sys

# Import existing engines
sys.path.insert(0, '/workspace')
from hyper_simulation_engine import (
    SimulationEvent, DeltaEncoder, SwarmBloomFilter, 
    HierarchicalAggregator, run_hyper_simulation_test
)

# ============================================================================
# LOAD TEST CONFIGURATION
# ============================================================================

@dataclass
class LoadTestConfig:
    """Configuration for synthetic load testing"""
    
    # Baseline performance targets
    target_eps: int = 1_000_000  # 1M events/sec target
    ramp_up_steps: int = 10
    step_duration_seconds: float = 5.0
    
    # Adversarial flood parameters
    flood_multiplier: int = 10
    flood_duration_seconds: float = 2.0
    flood_interval_seconds: float = 10.0
    
    # Swarm concurrency
    concurrent_swarms: int = 1000
    agents_per_swarm: int = 100
    
    # Memory pressure test
    extended_duration_minutes: int = 5
    gc_check_interval_seconds: float = 30.0
    
    # Performance thresholds
    max_latency_ms: float = 10.0
    min_compression_ratio: float = 5.0
    max_memory_mb: int = 4096
    
    # Reporting
    metrics_sample_rate: float = 0.01  # Sample 1% of events for detailed metrics
    output_file: str = '/workspace/load_test_results.json'


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Real-time performance tracking"""
    timestamps: deque = field(default_factory=lambda: deque(maxlen=10000))
    latencies_ms: deque = field(default_factory=lambda: deque(maxlen=10000))
    compression_ratios: deque = field(default_factory=lambda: deque(maxlen=1000))
    memory_usage_mb: deque = field(default_factory=lambda: deque(maxlen=100))
    event_counts: List[int] = field(default_factory=list)
    anomaly_counts: List[int] = field(default_factory=list)
    error_events: List[Dict] = field(default_factory=list)
    
    def record_event(self, latency_ms: float, compression_ratio: float, 
                     memory_mb: float, timestamp: float):
        self.latencies_ms.append(latency_ms)
        self.compression_ratios.append(compression_ratio)
        self.memory_usage_mb.append(memory_mb)
        self.timestamps.append(timestamp)
        
    def record_batch(self, event_count: int, anomaly_count: int):
        self.event_counts.append(event_count)
        self.anomaly_counts.append(anomaly_count)
    
    def record_error(self, error_type: str, details: str):
        self.error_events.append({
            'timestamp': time.time(),
            'type': error_type,
            'details': details
        })
    
    def get_summary(self) -> Dict:
        if not self.latencies_ms:
            return {'error': 'No metrics collected'}
            
        return {
            'latency': {
                'mean_ms': statistics.mean(self.latencies_ms),
                'median_ms': statistics.median(self.latencies_ms),
                'p95_ms': sorted(self.latencies_ms)[int(len(self.latencies_ms) * 0.95)] if len(self.latencies_ms) > 20 else max(self.latencies_ms),
                'p99_ms': sorted(self.latencies_ms)[int(len(self.latencies_ms) * 0.99)] if len(self.latencies_ms) > 100 else max(self.latencies_ms),
                'max_ms': max(self.latencies_ms)
            },
            'compression': {
                'mean_ratio': statistics.mean(self.compression_ratios),
                'min_ratio': min(self.compression_ratios),
                'max_ratio': max(self.compression_ratios)
            },
            'memory': {
                'mean_mb': statistics.mean(self.memory_usage_mb),
                'max_mb': max(self.memory_usage_mb),
                'trend': 'stable' if len(self.memory_usage_mb) < 10 else (
                    'increasing' if self.memory_usage_mb[-1] > self.memory_usage_mb[0] * 1.2
                    else 'decreasing' if self.memory_usage_mb[-1] < self.memory_usage_mb[0] * 0.8
                    else 'stable'
                )
            },
            'throughput': {
                'total_events': sum(self.event_counts),
                'total_anomalies': sum(self.anomaly_counts),
                'batches_processed': len(self.event_counts)
            },
            'errors': {
                'count': len(self.error_events),
                'recent': self.error_events[-10:] if self.error_events else []
            }
        }


# ============================================================================
# SYNTHETIC EVENT GENERATORS
# ============================================================================

class SyntheticEventGenerator:
    """Generates realistic adversarial telemetry patterns"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.rng = random.Random(42)
        self.phase_drift = 0.0
        self.adversarial_cycle = 0
        
    def generate_baseline_event(self, swarm_id: str, timestamp: float) -> SimulationEvent:
        """Generate normal operational telemetry"""
        # Simulate phase lock stability with minor fluctuations
        base_stability = 50.0 + math.sin(timestamp * 0.1) * 3.0
        noise = self.rng.gauss(0, 1.5)
        
        return SimulationEvent(
            timestamp=timestamp,
            swarm_id=swarm_id,
            metric_type='phase_lock_stability',
            value=base_stability + noise,
            metadata={'source': 'baseline'}
        )
    
    def generate_adversarial_event(self, swarm_id: str, timestamp: float, 
                                   intensity: float = 1.0) -> SimulationEvent:
        """Generate adversarial lambda pressure event"""
        self.adversarial_cycle += 1
        
        # Escalating attack patterns
        attack_types = [
            ('entropy_injection', 150.0 * intensity),
            ('threshold_manipulation', -80.0 * intensity),
            ('swarm_fragmentation', 200.0 * intensity),
            ('phase_desync', 120.0 * intensity)
        ]
        
        attack_type, base_value = self.rng.choice(attack_types)
        value = base_value + self.rng.gauss(0, 20.0 * intensity)
        
        return SimulationEvent(
            timestamp=timestamp,
            swarm_id=swarm_id,
            metric_type=attack_type,
            value=value,
            metadata={
                'source': 'adversarial',
                'intensity': intensity,
                'cycle': self.adversarial_cycle
            }
        )
    
    def generate_flood_burst(self, swarm_id: str, timestamp: float, 
                            count: int) -> List[SimulationEvent]:
        """Generate rapid burst of events (adversarial flood)"""
        events = []
        for i in range(count):
            event_time = timestamp + (i * 0.0001)  # Sub-millisecond spacing
            
            if self.rng.random() < 0.3:  # 30% adversarial during flood
                events.append(self.generate_adversarial_event(
                    swarm_id, event_time, intensity=self.rng.uniform(1.0, 3.0)
                ))
            else:
                events.append(self.generate_baseline_event(swarm_id, event_time))
                
        return events
    
    def generate_multi_swarm_snapshot(self, timestamp: float) -> List[SimulationEvent]:
        """Generate simultaneous telemetry from all swarms"""
        events = []
        for swarm_idx in range(self.config.concurrent_swarms):
            swarm_id = f"swarm_{swarm_idx:04d}"
            
            # Each swarm sends agent-level telemetry
            num_agents = self.rng.randint(10, self.config.agents_per_swarm)
            for agent_idx in range(num_agents):
                if self.rng.random() < 0.01:  # 1% adversarial
                    events.append(self.generate_adversarial_event(
                        f"{swarm_id}_agent_{agent_idx}", timestamp
                    ))
                else:
                    events.append(self.generate_baseline_event(
                        f"{swarm_id}_agent_{agent_idx}", timestamp
                    ))
                    
        return events


# ============================================================================
# LOAD TEST SCENARIOS
# ============================================================================

class LoadTestRunner:
    """Executes synthetic load test scenarios"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.generator = SyntheticEventGenerator(config)
        self.metrics = PerformanceMetrics()
        self.rng = random.Random(42)  # Add RNG for sampling decisions
        
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024  # Convert KB to MB on Linux
        except:
            return 0.0
    
    def _process_event_batch(self, events: List[SimulationEvent], 
                            encoder: DeltaEncoder, bloom: SwarmBloomFilter,
                            aggregator: HierarchicalAggregator) -> Tuple[float, float]:
        """Process a batch of events and return latency + compression ratio"""
        start_time = time.perf_counter()
        
        anomaly_count = 0
        for event in events:
            # Delta encoding
            encoder.ingest(event.value)
            
            # Bloom filter check for anomalies
            if event.metadata and event.metadata.get('source') == 'adversarial':
                sig = f"{event.swarm_id}_{event.metric_type}_{abs(event.value):.2f}"
                if not bloom.check(sig):
                    bloom.add(sig)
                    anomaly_count += 1
            
            # Hierarchical aggregation
            aggregator.ingest(event)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000.0
        
        # Calculate compression ratio
        compression_ratio = encoder.compression_ratio(len(events))
        
        return latency_ms, compression_ratio, anomaly_count
    
    def test_eps_ramp_up(self) -> Dict:
        """Scenario 1: Gradually increase EPS to find breaking point"""
        print("\n" + "="*80)
        print("📈 SCENARIO 1: EPS RAMP-UP TEST")
        print("="*80)
        
        encoder = DeltaEncoder(baseline=50.0)
        bloom = SwarmBloomFilter(size=50000)
        aggregator = HierarchicalAggregator()
        
        results = {
            'scenario': 'eps_ramp_up',
            'steps': []
        }
        
        for step in range(1, self.config.ramp_up_steps + 1):
            eps_target = int(step * self.config.target_eps / self.config.ramp_up_steps)
            duration = self.config.step_duration_seconds
            total_events = int(eps_target * duration)
            
            print(f"\n  Step {step}/{self.config.ramp_up_steps}: Target {eps_target:,} EPS")
            
            # Generate and process events
            batch_size = min(10000, total_events)
            step_start = time.time()
            events_processed = 0
            total_latency = 0.0
            total_anomalies = 0
            
            while events_processed < total_events:
                # Generate batch
                timestamp = time.time()
                batch = [
                    self.generator.generate_baseline_event(
                        f"swarm_{i % 100}", timestamp + (i * 0.0001)
                    )
                    for i in range(batch_size)
                ]
                
                # Process batch
                latency, comp_ratio, anomalies = self._process_event_batch(
                    batch, encoder, bloom, aggregator
                )
                
                total_latency += latency
                total_anomalies += anomalies
                events_processed += len(batch)
                
                # Record metrics
                if self.rng.random() < self.config.metrics_sample_rate:
                    self.metrics.record_event(
                        latency, comp_ratio, self._get_memory_usage_mb(), time.time()
                    )
                
                # Check latency threshold
                if latency > self.config.max_latency_ms:
                    print(f"    ⚠️  LATENCY SPIKE: {latency:.2f}ms (threshold: {self.config.max_latency_ms}ms)")
                    self.metrics.record_error('latency_spike', f'{latency:.2f}ms at {eps_target:,} EPS')
            
            step_duration = time.time() - step_start
            actual_eps = events_processed / step_duration
            
            step_result = {
                'step': step,
                'target_eps': eps_target,
                'actual_eps': actual_eps,
                'avg_latency_ms': total_latency / (events_processed / batch_size),
                'total_anomalies': total_anomalies,
                'success': actual_eps >= eps_target * 0.9
            }
            results['steps'].append(step_result)
            
            print(f"    ✅ Actual: {actual_eps:,.0f} EPS | Avg Latency: {step_result['avg_latency_ms']:.2f}ms")
            
            # Stop if we've exceeded capacity
            if actual_eps < eps_target * 0.5:
                print(f"    🛑 CAPACITY REACHED at {eps_target:,} EPS")
                break
        
        return results
    
    def test_adversarial_flood(self) -> Dict:
        """Scenario 2: Inject burst anomalies at 10x normal rate"""
        print("\n" + "="*80)
        print("⚔️  SCENARIO 2: ADVERSARIAL FLOOD TEST")
        print("="*80)
        
        encoder = DeltaEncoder(baseline=50.0)
        bloom = SwarmBloomFilter(size=100000)
        aggregator = HierarchicalAggregator()
        
        results = {
            'scenario': 'adversarial_flood',
            'flood_events': [],
            'recovery_metrics': {}
        }
        
        print(f"\n  Running baseline for {self.config.flood_interval_seconds}s...")
        baseline_duration = self.config.flood_interval_seconds
        baseline_events = 0
        baseline_start = time.time()
        
        while time.time() - baseline_start < baseline_duration:
            events = [
                self.generator.generate_baseline_event(f"swarm_{i}", time.time())
                for i in range(100)
            ]
            _, _, anomalies = self._process_event_batch(events, encoder, bloom, aggregator)
            baseline_events += len(events)
        
        baseline_rate = baseline_events / baseline_duration
        print(f"    Baseline rate: {baseline_rate:,.0f} events/sec")
        
        # Inject flood
        print(f"\n  💥 INJECTING FLOOD ({self.config.flood_multiplier}x baseline)...")
        flood_start = time.time()
        flood_events = 0
        flood_anomalies = 0
        
        while time.time() - flood_start < self.config.flood_duration_seconds:
            burst_size = int(baseline_rate * self.config.flood_multiplier * 0.1)
            events = self.generator.generate_flood_burst(
                "swarm_flood_target", time.time(), burst_size
            )
            
            latency, comp_ratio, anomalies = self._process_event_batch(
                events, encoder, bloom, aggregator
            )
            
            flood_events += len(events)
            flood_anomalies += anomalies
            
            self.metrics.record_event(
                latency, comp_ratio, self._get_memory_usage_mb(), time.time()
            )
            
            if latency > self.config.max_latency_ms * 2:
                self.metrics.record_error('flood_latency', f'{latency:.2f}ms during flood')
        
        flood_rate = flood_events / self.config.flood_duration_seconds
        print(f"    Flood rate: {flood_rate:,.0f} events/sec")
        print(f"    Anomalies detected: {flood_anomalies}")
        
        results['flood_events'] = {
            'total': flood_events,
            'anomalies': flood_anomalies,
            'rate': flood_rate,
            'duration_sec': self.config.flood_duration_seconds
        }
        
        # Recovery period
        print(f"\n  🔄 Monitoring recovery...")
        recovery_start = time.time()
        recovery_events = 0
        recovery_latencies = []
        
        while time.time() - recovery_start < self.config.flood_interval_seconds:
            events = [
                self.generator.generate_baseline_event(f"swarm_{i}", time.time())
                for i in range(100)
            ]
            latency, _, _ = self._process_event_batch(events, encoder, bloom, aggregator)
            recovery_events += len(events)
            recovery_latencies.append(latency)
        
        avg_recovery_latency = statistics.mean(recovery_latencies) if recovery_latencies else 0
        results['recovery_metrics'] = {
            'time_to_stabilize_sec': self.config.flood_interval_seconds,
            'avg_post_flood_latency_ms': avg_recovery_latency,
            'recovered': avg_recovery_latency < self.config.max_latency_ms
        }
        
        print(f"    Recovery latency: {avg_recovery_latency:.2f}ms")
        print(f"    Status: {'✅ RECOVERED' if avg_recovery_latency < self.config.max_latency_ms else '⚠️ DEGRADED'}")
        
        return results
    
    def test_multi_swarm_concurrency(self) -> Dict:
        """Scenario 3: Simulate 1000+ swarms transmitting simultaneously"""
        print("\n" + "="*80)
        print("🌐 SCENARIO 3: MULTI-SWARM CONCURRENCY TEST")
        print("="*80)
        
        encoder = DeltaEncoder(baseline=50.0)
        bloom = SwarmBloomFilter(size=200000)
        aggregator = HierarchicalAggregator(window_sizes=[0.1, 1.0, 10.0])
        
        results = {
            'scenario': 'multi_swarm_concurrency',
            'swarm_count': self.config.concurrent_swarms,
            'snapshots': []
        }
        
        print(f"\n  Simulating {self.config.concurrent_swarms} concurrent swarms...")
        
        snapshot_count = 10
        for i in range(snapshot_count):
            snapshot_start = time.time()
            
            # Generate multi-swarm snapshot
            events = self.generator.generate_multi_swarm_snapshot(time.time())
            
            # Process
            latency, comp_ratio, anomalies = self._process_event_batch(
                events, encoder, bloom, aggregator
            )
            
            memory_mb = self._get_memory_usage_mb()
            self.metrics.record_event(latency, comp_ratio, memory_mb, time.time())
            self.metrics.record_batch(len(events), anomalies)
            
            snapshot_result = {
                'snapshot': i + 1,
                'events': len(events),
                'latency_ms': latency,
                'compression_ratio': comp_ratio,
                'anomalies': anomalies,
                'memory_mb': memory_mb
            }
            results['snapshots'].append(snapshot_result)
            
            print(f"    Snapshot {i+1}/{snapshot_count}: "
                  f"{len(events):,} events | {latency:.2f}ms | "
                  f"{comp_ratio:.2f}x compression | {anomalies} anomalies")
        
        return results
    
    def test_memory_pressure(self) -> Dict:
        """Scenario 4: Extended duration to test GC and archival"""
        print("\n" + "="*80)
        print("💾 SCENARIO 4: MEMORY PRESSURE TEST")
        print("="*80)
        
        encoder = DeltaEncoder(baseline=50.0)
        bloom = SwarmBloomFilter(size=500000)
        aggregator = HierarchicalAggregator(window_sizes=[1.0, 60.0, 3600.0])
        
        results = {
            'scenario': 'memory_pressure',
            'duration_minutes': self.config.extended_duration_minutes,
            'memory_samples': [],
            'gc_events': []
        }
        
        print(f"\n  Running extended test for {self.config.extended_duration_minutes} minutes...")
        print(f"  (Note: Full test may take time; running shortened demo)")
        
        # Shortened demo version
        demo_duration_sec = 30.0  # Demo: 30 seconds instead of full duration
        start_time = time.time()
        events_total = 0
        sample_interval = self.config.gc_check_interval_seconds
        
        last_gc_check = start_time
        
        while time.time() - start_time < demo_duration_sec:
            # Generate steady stream
            events = [
                self.generator.generate_baseline_event(f"swarm_{i % 100}", time.time())
                for i in range(1000)
            ]
            
            _, comp_ratio, _ = self._process_event_batch(events, encoder, bloom, aggregator)
            events_total += len(events)
            
            current_time = time.time()
            
            # Periodic memory sampling
            if current_time - last_gc_check >= sample_interval or current_time - start_time >= demo_duration_sec - 1:
                memory_mb = self._get_memory_usage_mb()
                elapsed_min = (current_time - start_time) / 60.0
                
                results['memory_samples'].append({
                    'elapsed_min': elapsed_min,
                    'memory_mb': memory_mb,
                    'events_processed': events_total
                })
                
                print(f"    [{elapsed_min:.1f}min] Memory: {memory_mb:.1f}MB | Events: {events_total:,}")
                last_gc_check = current_time
            
            # Small delay to prevent CPU saturation in demo
            time.sleep(0.01)
        
        # Analyze memory trend
        if len(results['memory_samples']) >= 2:
            initial_mem = results['memory_samples'][0]['memory_mb']
            final_mem = results['memory_samples'][-1]['memory_mb']
            memory_growth = final_mem - initial_mem
            
            results['memory_analysis'] = {
                'initial_mb': initial_mem,
                'final_mb': final_mem,
                'growth_mb': memory_growth,
                'growth_rate_mb_per_min': memory_growth / max(0.01, results['memory_samples'][-1]['elapsed_min']),
                'status': 'STABLE' if abs(memory_growth) < 50 else 'GROWING' if memory_growth > 0 else 'SHRINKING'
            }
            
            print(f"\n    Memory Analysis:")
            print(f"      Growth: {memory_growth:+.1f}MB over {results['memory_samples'][-1]['elapsed_min']:.1f}min")
            print(f"      Status: {results['memory_analysis']['status']}")
        
        return results
    
    def test_compression_throughput(self) -> Dict:
        """Scenario 5: Benchmark compression throughput (MB/sec)"""
        print("\n" + "="*80)
        print("⚡ SCENARIO 5: COMPRESSION THROUGHPUT BENCHMARK")
        print("="*80)
        
        encoder = DeltaEncoder(baseline=50.0)
        
        results = {
            'scenario': 'compression_throughput',
            'benchmarks': []
        }
        
        # Test different payload sizes
        payload_sizes = [100, 1000, 10000, 100000, 1000000]
        
        for size in payload_sizes:
            # Generate synthetic data
            values = [50.0 + math.sin(i * 0.01) * 5.0 + random.gauss(0, 1.0) 
                     for i in range(size)]
            
            # Benchmark encoding
            encoder_test = DeltaEncoder(baseline=50.0)
            start_time = time.perf_counter()
            
            for value in values:
                encoder_test.ingest(value)
            
            encode_time = time.perf_counter() - start_time
            encode_throughput = size / encode_time if encode_time > 0 else 0
            
            # Estimate raw vs compressed size (in bytes, assuming 8 bytes per float)
            raw_size_bytes = size * 8
            # Simplified compression estimate
            compression_ratio = encoder_test.compression_ratio(size)
            compressed_size_bytes = raw_size_bytes / compression_ratio
            
            benchmark = {
                'payload_size': size,
                'encode_time_sec': encode_time,
                'throughput_events_per_sec': encode_throughput,
                'raw_size_kb': raw_size_bytes / 1024,
                'compressed_size_kb': compressed_size_bytes / 1024,
                'compression_ratio': compression_ratio,
                'throughput_mb_sec': (raw_size_bytes / 1024 / 1024) / encode_time if encode_time > 0 else 0
            }
            results['benchmarks'].append(benchmark)
            
            print(f"    Payload: {size:>7,} events | "
                  f"Throughput: {encode_throughput:>10,.0f} EPS | "
                  f"Compression: {compression_ratio:>5.2f}x | "
                  f"Speed: {benchmark['throughput_mb_sec']:>8.2f} MB/sec")
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Execute complete load test suite"""
        print("\n" + "🧪"*40)
        print("SYNTHETIC LOAD-TEST SUITE")
        print("Testing Hyper-Simulation Compression Engine")
        print("🧪"*40)
        
        all_results = {
            'test_suite': 'synthetic_load_test',
            'timestamp': time.time(),
            'config': {
                'target_eps': self.config.target_eps,
                'concurrent_swarms': self.config.concurrent_swarms,
                'extended_duration_min': self.config.extended_duration_minutes
            },
            'scenarios': {}
        }
        
        # Run each scenario
        all_results['scenarios']['eps_ramp_up'] = self.test_eps_ramp_up()
        all_results['scenarios']['adversarial_flood'] = self.test_adversarial_flood()
        all_results['scenarios']['multi_swarm'] = self.test_multi_swarm_concurrency()
        all_results['scenarios']['memory_pressure'] = self.test_memory_pressure()
        all_results['scenarios']['throughput'] = self.test_compression_throughput()
        
        # Aggregate summary
        all_results['summary'] = self.metrics.get_summary()
        
        # Save results
        with open(self.config.output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print("\n" + "="*80)
        print("📊 LOAD TEST COMPLETE")
        print("="*80)
        
        summary = all_results['summary']
        print(f"\n  Overall Metrics:")
        if 'latency' in summary:
            print(f"    Avg Latency: {summary['latency']['mean_ms']:.2f}ms")
            print(f"    P95 Latency: {summary['latency']['p95_ms']:.2f}ms")
            print(f"    Avg Compression: {summary['compression']['mean_ratio']:.2f}x")
        print(f"    Total Events: {summary['throughput']['total_events']:,}")
        print(f"    Errors: {summary['errors']['count']}")
        print(f"\n  💾 Results saved to: {self.config.output_file}")
        
        return all_results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    config = LoadTestConfig(
        target_eps=500_000,  # Conservative target for demo
        ramp_up_steps=8,
        concurrent_swarms=500,  # Reduced for demo
        extended_duration_minutes=1,  # Shortened for demo
        metrics_sample_rate=0.05
    )
    
    runner = LoadTestRunner(config)
    results = runner.run_all_tests()
    
    # Print final verdict
    print("\n" + "="*80)
    print("🎯 FINAL VERDICT")
    print("="*80)
    
    errors = results['summary']['errors']['count']
    latency_ok = results['summary']['latency']['p95_ms'] < config.max_latency_ms
    compression_ok = results['summary']['compression']['mean_ratio'] > config.min_compression_ratio
    
    if errors == 0 and latency_ok and compression_ok:
        print("\n  ✅ ALL SYSTEMS NOMINAL")
        print("     • Latency within thresholds")
        print("     • Compression exceeding targets")
        print("     • No critical errors detected")
        print("     • System ready for production adversarial loads")
    elif errors > 10:
        print("\n  ⚠️  CRITICAL ISSUES DETECTED")
        print(f"     • {errors} errors recorded")
        print("     • Review error logs for root cause analysis")
    else:
        print("\n  ⚠️  PERFORMANCE DEGRADATION OBSERVED")
        if not latency_ok:
            print("     • Latency exceeds thresholds under load")
        if not compression_ok:
            print("     • Compression ratio below target")
        print("     • Consider tuning parameters or scaling resources")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
