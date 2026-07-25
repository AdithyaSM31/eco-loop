# Eco-Loop Building Agents 🌍🤖

**Eco-Loop** transforms a building from a passive energy consumer into an active, self-correcting agent capable of continuous, real-time optimization. 

Built for the **Honeywell Hackathon**, this Proof-of-Concept integrates a high-fidelity **EnergyPlus** simulation engine with an open-source **LLM Cognitive Engine** via closed-loop feedback, automating smart building operations to intelligently balance energy efficiency and thermal comfort constraints (PMV).

## System Architecture

Our solution executes an autonomous closed-loop control pipeline:
1. **Simulation Sandbox**: A 5-Zone commercial building running in `PyEnergyPlus` on a tropical Chennai weather dataset.
2. **Cognitive Engine**: An LLM (powered by `gpt-4o-mini` / `llama3`) that acts as the "Brain".
3. **Feedback & Injection**: The PyEnergyPlus API pauses the simulation at each timestep, extracts live data (Zone Temps, PMV, Energy Consumption), passes it to the Agent, and directly injects the LLM's dynamic HVAC setpoints back into the physics engine.
4. **Dashboarding**: A real-time `Streamlit` dashboard plots quantitative energy savings and human thermal comfort (PMV) boundaries.

*See [`docs/System_Architecture.md`](docs/System_Architecture.md) for deeper details on prompt engineering and latency management.*

## Repository Structure

```
eco-loop/
├── backend/
│   ├── simulation.py      # Simulation Orchestrator (PyEnergyPlus wrapper)
│   └── agent.py           # Cognitive LLM Engine & Agentic Tool Logic
├── dashboard/
│   └── app.py             # Streamlit Quantitative Savings Dashboard
├── docs/
│   └── System_Architecture.md # Architecture & Prompting Strategy
├── models/                # EnergyPlus IDF and EPW weather files
└── requirements.txt       # Python dependencies
```

## Quickstart

### Prerequisites
- Python 3.10+
- **EnergyPlus V26.2.0** installed locally (`C:\EnergyPlusV26-2-0`).
- An API Key (or local Ollama instance) configured in a `.env` file.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/AdithyaSM31/eco-loop.git
   cd eco-loop
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Loop

1. **Start the Agentic Simulation**:
   ```bash
   python backend/simulation.py
   ```
   *Watch the console as the LLM begins reasoning over the building physics and injecting dynamic setpoints.*

2. **Launch the Dashboard**:
   Open a new terminal and run:
   ```bash
   streamlit run dashboard/app.py
   ```
   *The dashboard will auto-update, charting the live PMV constraints and total cumulative HVAC Energy savings.*
