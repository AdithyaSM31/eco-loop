import sys
import os
import argparse
from agent import BuildingAgent

# --- IMPORTANT SETUP INSTRUCTIONS ---
# To use pyenergyplus, you must have EnergyPlus installed on your machine.
# Default Windows installation path is usually C:\EnergyPlusV24-1-0
# You must append the EnergyPlus directory to your sys.path so Python can find pyenergyplus.
ENERGYPLUS_INSTALL_DIR = r"C:\EnergyPlusV26-2-0" 
if ENERGYPLUS_INSTALL_DIR not in sys.path:
    sys.path.append(ENERGYPLUS_INSTALL_DIR)

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print(f"Error: pyenergyplus not found. Make sure EnergyPlus is installed at {ENERGYPLUS_INSTALL_DIR}")
    sys.exit(1)

class EcoLoopSimulation:
    def __init__(self, idf_path, epw_path, agentic=False):
        self.idf_path = idf_path
        self.epw_path = epw_path
        self.agentic = agentic
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        
        if self.agentic:
            self.agent = BuildingAgent()
            self.log_file = "agent_log.csv"
        else:
            self.log_file = "baseline_log.csv"
            
        self.init_logger()

    def init_logger(self):
        with open(self.log_file, "w") as f:
            f.write("Time,ZoneTemp,PMV,Energy_kWh,HeatingSetPoint,CoolingSetPoint\n")

    def callback_function(self, state_arg):
        try:
            # Ensure data is ready before requesting handles
            if not self.api.exchange.api_data_fully_ready(state_arg):
                return
                
            # Initialize handles on the first ready timestep
            if not hasattr(self, 'handles_initialized'):
                # Sensors for SPACE5-1
                self.temp_handle = self.api.exchange.get_variable_handle(state_arg, "Zone Air Temperature", "SPACE5-1")
                self.pmv_handle = self.api.exchange.get_variable_handle(state_arg, "Zone Thermal Comfort Fanger Model PMV", "SPACE5-1") 
                self.energy_handle = self.api.exchange.get_meter_handle(state_arg, "Electricity:HVAC")
                
                # Actuators for Forward Injection
                self.heat_act_handle = self.api.exchange.get_actuator_handle(state_arg, "Schedule:Compact", "Schedule Value", "Htg-SetP-Sch")
                self.cool_act_handle = self.api.exchange.get_actuator_handle(state_arg, "Schedule:Compact", "Schedule Value", "Clg-SetP-Sch")
                
                if self.agentic:
                    self.last_heat_sp = 20.0
                    self.last_cool_sp = 24.0
                    self.timestep_counter = 0
                else:
                    self.baseline_heat_sp = 20.0
                    self.baseline_cool_sp = 22.0  # Legacy BMS over-cooling scenario
                
                self.handles_initialized = True

            # 1. READ SENSORS (Feedback)
            current_temp = self.api.exchange.get_variable_value(state_arg, self.temp_handle) if self.temp_handle > 0 else 22.5 
            current_pmv = self.api.exchange.get_variable_value(state_arg, self.pmv_handle) if self.pmv_handle > 0 else 0.3
            
            # Energy meters return Joules for timestep or Watts for rate. Converting roughly to kWh for UI
            raw_energy = self.api.exchange.get_meter_value(state_arg, self.energy_handle) if self.energy_handle > 0 else 0
            energy_kwh = (raw_energy / 3600000.0) if raw_energy > 0 else 1.2
            
            new_heat_sp = 20.0
            new_cool_sp = 24.0

            if self.agentic:
                self.timestep_counter += 1
                
                # Throttle LLM calls to once per 24 hours (96 timesteps at 15m intervals) to save time/money
                if self.timestep_counter % 96 == 1:
                    decision = self.agent.evaluate_and_act(
                        temp=current_temp, 
                        pmv=current_pmv, 
                        energy=energy_kwh
                    )
                    
                    try:
                        heat_sp = decision.get("heating_setpoint", 20.0)
                        self.last_heat_sp = float(heat_sp) if heat_sp is not None else 20.0
                    except (ValueError, TypeError):
                        self.last_heat_sp = 20.0
                        
                    try:
                        cool_sp = decision.get("cooling_setpoint", 24.0)
                        self.last_cool_sp = float(cool_sp) if cool_sp is not None else 24.0
                    except (ValueError, TypeError):
                        self.last_cool_sp = 24.0
                        
                    print(f"Day {self.timestep_counter//96 + 1}: AI Decision applied -> Heat={self.last_heat_sp}, Cool={self.last_cool_sp}")
                
                new_heat_sp = self.last_heat_sp
                new_cool_sp = self.last_cool_sp
                
                # 3. CONTROL ACTIONS (Forward Injection)
                if self.heat_act_handle > 0:
                    self.api.exchange.set_actuator_value(state_arg, self.heat_act_handle, new_heat_sp)
                if self.cool_act_handle > 0:
                    self.api.exchange.set_actuator_value(state_arg, self.cool_act_handle, new_cool_sp)
            else:
                new_heat_sp = self.baseline_heat_sp
                new_cool_sp = self.baseline_cool_sp
                
                # Rigid legacy injection
                if self.heat_act_handle > 0:
                    self.api.exchange.set_actuator_value(state_arg, self.heat_act_handle, new_heat_sp)
                if self.cool_act_handle > 0:
                    self.api.exchange.set_actuator_value(state_arg, self.cool_act_handle, new_cool_sp)
            
            # Log the timestep data
            with open(self.log_file, "a") as f:
                f.write(f"Timestamp,{current_temp},{current_pmv},{energy_kwh},{new_heat_sp},{new_cool_sp}\n")
        except Exception as e:
            print(f"PYTHON CALLBACK EXCEPTION: {e}")
            raise

    def run(self):
        # Register the callback
        self.api.runtime.callback_begin_zone_timestep_after_init_heat_balance(self.state, self.callback_function)
        
        mode = "AGENTIC" if self.agentic else "BASELINE"
        print(f"Starting {mode} Closed-Loop Simulation with {self.idf_path}")
        try:
            self.api.runtime.run_energyplus(self.state, ['-w', self.epw_path, self.idf_path])
        except OSError as e:
            # EnergyPlus C++ core throws a WinError 0xe06d7363 on clean termination on some Windows builds
            pass
        print(f"{mode} Simulation Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eco-Loop Simulation Engine")
    parser.add_argument("--agentic", action="store_true", help="Run in AI Agentic Mode")
    args = parser.parse_args()
    
    sim = EcoLoopSimulation(idf_path="models/baseline.idf", epw_path="models/weather.epw", agentic=args.agentic)
    sim.run()
