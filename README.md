# EBC Studio: Entropy-Bounded Control

<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

## Overview

A formal engineering framework for deterministic admission systems. Implements entropy-bounded execution to render failure operationally irrelevant through proactive state preemption.

This system demonstrates the architectural differential between:
- **Reactive-Failure Logic**: Traditional exception handling that identifies corruption after execution
- **Entropy-Bounded Logic**: Deterministic admission control that preempts failures before state transitions

## Key Concepts

### Syntropy (Φ)
Index of internal order vs entropy. Higher values indicate better system coherence and invariant health.

### Operational Multiplier
Efficiency gain compared to reactive systems. Shows how much more work gets done with bounded control.

### State Coverage
Percentage of operational state space that has been mapped and bounded by invariants.

### Containment Proof
Percentage of potential failures successfully preempted through admission control.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EBC Orchestration                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Control    │  │   Domain     │  │   Safety     │      │
│  │    Loop      │  │   Selector   │  │   Bounds     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           KPI Dashboard (Real-time Metrics)           │   │
│  │   Syntropy | Coverage | Admissions | Efficiency       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Operational Trajectory Visualization          │   │
│  │              Φ vs Entropy over Time                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        Architectural Differential Analysis            │   │
│  │         Reactive vs Bounded Comparison                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Deterministic Event Manifold Log             │   │
│  │         Preemptions | Failures | Completions          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐                                            │
│  │   Spec       │  AI-powered formal invariant extraction    │
│  │   Extraction │                                            │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Node.js (v18 or higher recommended)
- Gemini API Key (for AI-powered spec formalization)

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env.local` file in the root directory:

```bash
GEMINI_API_KEY=your_api_key_here
```

Get your API key from: https://aistudio.google.com/app/apikey

### 3. Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

### 5. Preview Production Build

```bash
npm run preview
```

## Usage

### Control Modes

1. **Reactive Mode**: Traditional error handling - allows work through and catches failures
2. **Bounded Mode**: Entropy-bounded control - preempts work that would violate invariants

### Operation Domains

Select different domains to see how safety bounds adapt:
- **GENERAL**: Standard operating parameters
- **MEDICAL_ROBOTICS**: Stricter bounds (load: 40%, entropy: 5%)
- **AEROSPACE**: Enhanced safety margins (load: 55%, entropy: 8%)
- **FINTECH**: Balanced compliance bounds (load: 70%, entropy: 10%)

### Automation Controls

- **Start/Halt Admission**: Toggle automated work generation
- **Stress Test**: Increase load and failure probability
- **Pulse**: Manual single work unit injection

### Formal Spec Extraction

Enter a system description in natural language and click "Extract Invariants" to generate:
- TLA+ style formal logic
- Safety-critical invariants
- Preemption strategies

Example input:
> "Air traffic collision avoidance system with minimum separation distance invariant"

## Project Structure

```
/workspace
├── App.tsx                 # Main application component
├── index.tsx               # React entry point
├── types.ts                # TypeScript type definitions
├── components/
│   ├── SystemVisualizer.tsx    # Real-time metrics chart
│   ├── KpiPanel.tsx            # KPI dashboard cards
│   ├── RefusalLog.tsx          # Event manifold log
│   └── AnalysisPanel.tsx       # Architecture comparison
├── services/
│   └── geminiService.ts        # AI integration for spec formalization
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── vite.config.ts          # Vite bundler configuration
└── .env.local              # Environment variables (gitignored)
```

## Technical Details

### Invariant Monitoring

The system tracks two core invariants:
1. **Capacity Envelope (L < B_load)**: Work queue load percentage
2. **Entropy Boundary (E < B_entropy)**: System entropy gradient

Status indicators:
- 🟢 **STABLE**: Below 75% of limit
- 🟡 **WARNING**: 75-100% of limit
- 🔴 **VIOLATED**: At or above limit

### Metrics Calculation

**Syntropy (Φ)**:
```
Φ = (PreemptionEfficiency × InvariantHealth) / (1 + EntropyGradient)
```

**Operational Multiplier**:
```
OpMultiplier = 1 + (Φ × 1.5)  // in Bounded mode
OpMultiplier = 1.0            // in Reactive mode
```

**Containment Proof**:
```
ContainmentProof = (PreemptedCount / TotalProcessed) × 100
```

## Deployment

### Local Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview
```

### Docker (Optional)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## License

MIT

## Credits

Built with:
- React 19
- TypeScript
- Vite
- Recharts
- Lucide Icons
- Google Gemini AI
