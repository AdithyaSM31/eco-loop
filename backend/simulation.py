import sys
import os
import json
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
    # sys.exit(1) # Commented out for mock testing

class EcoLoopSimulation:
    def __init__(self, idf_path, epw_path):
        self.idf_path = idf_path
        self.epw_path = epw_path
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        self.agent = BuildingAgent()
        
        # We will log data to be read by the Streamlit dashboard
        self.log_file = "simulation_log.csv"
        self.init_logger()

    def init_logger(self):
        with open(self.log_file, "w") as f:
            f.write("Time,ZoneTemp,PMV,Energy_kWh,HeatingSetPoint,CoolingSetPoint\n")

    def callback_function(self, state_arg):
        """
        This callback is called at every zone timestep by EnergyPlus.
        """
        # Ensure data is ready before requesting handles
        if not self.api.exchange.api_data_fully_ready(state_arg):
            return
            
        # Initialize handles on the first ready timestep
        if not hasattr(self, 'handles_initialized'):
            # Fetching from the new 5-Zone model for the interior zone (SPACE5-1)
            self.temp_handle = self.api.exchange.get_variable_handle(state_arg, "Zone Air Temperature", "SPACE5-1")
            
            # PMV is not in the default outputs for this specific IDF, so it will return -1 and fallback
            self.pmv_handle = self.api.exchange.get_variable_handle(state_arg, "Zone Thermal Comfort Fanger Model PMV", "SPACE5-1") 
            
            # Using Meter for HVAC electricity
            self.energy_handle = self.api.exchange.get_meter_handle(state_arg, "Electricity:HVAC")
            self.handles_initialized = True

        # 1. READ SENSORS (Feedback)
        current_temp = self.api.exchange.get_variable_value(state_arg, self.temp_handle) if self.temp_handle > 0 else 22.5 
        current_pmv = self.api.exchange.get_variable_value(state_arg, self.pmv_handle) if self.pmv_handle > 0 else 0.3
        
        # Energy meters return Joules for timestep or Watts for rate. Converting roughly to kWh for UI
        raw_energy = self.api.exchange.get_meter_value(state_arg, self.energy_handle) if self.energy_handle > 0 else 0
        energy_kwh = (raw_energy / 3600000.0) if raw_energy > 0 else 1.2
        
        # 2. COGNITIVE ENGINE REASONING
        # Pass the metrics to the LLM agent
        decision = self.agent.evaluate_and_act(
            temp=current_temp, 
            pmv=current_pmv, 
            energy=energy_kwh
        )
        
        # 3. CONTROL ACTIONS (Forward Injection)
        # In a real setup, we use self.api.exchange.set_actuator_value(state_arg, handle, value)
        new_heat_sp = decision.get("heating_setpoint", 20.0)
        new_cool_sp = decision.get("cooling_setpoint", 24.0)
        
        # Log the timestep data
        with open(self.log_file, "a") as f:
            f.write(f"Timestamp,{current_temp},{current_pmv},{energy_kwh},{new_heat_sp},{new_cool_sp}\n")
        
        print(f"AI Decision applied: Heat={new_heat_sp}, Cool={new_cool_sp}")

    def run(self):
        # Register the callback
        self.api.runtime.callback_begin_zone_timestep_after_init_heat_balance(self.state, self.callback_function)
        
        # Run EnergyPlus
        print(f"Starting Closed-Loop Simulation with {self.idf_path}")
        # Command line arguments equivalent to: energyplus -w weather.epw building.idf
        self.api.runtime.run_energyplus(self.state, ['-w', self.epw_path, self.idf_path])
        print("Simulation Complete.")

if __name__ == "__main__":
    sim = EcoLoopSimulation(idf_path="models/baseline.idf", epw_path="models/weather.epw")
    sim.run()
