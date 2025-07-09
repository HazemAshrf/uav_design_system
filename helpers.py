"""Utility functions for the UAV design system."""

from state import GlobalState


def print_final_design(state: GlobalState):
    """Print only the final design outputs."""
    print("=== FINAL UAV DESIGN ===")
    
    if state.mission_planner_outputs:
        latest = state.mission_planner_outputs[max(state.mission_planner_outputs.keys())]
        print(f"Mission: MTOW={latest.mtow}kg, Range={latest.range_km}km, Payload={latest.payload_kg}kg")
    
    if state.aerodynamics_outputs:
        latest = state.aerodynamics_outputs[max(state.aerodynamics_outputs.keys())]
        print(f"Aerodynamics: Wing={latest.wing_area_m2}m², AR={latest.aspect_ratio}, L/D={latest.lift_to_drag_ratio}")
    
    if state.propulsion_outputs:
        latest = state.propulsion_outputs[max(state.propulsion_outputs.keys())]
        print(f"Propulsion: {latest.engine_power_kw}kW {latest.engine_type}, {latest.thrust_n}N thrust")
    
    if state.structures_outputs:
        latest = state.structures_outputs[max(state.structures_outputs.keys())]
        print(f"Structure: {latest.structural_weight_kg}kg {latest.wing_spar_material}")
    
    if state.manufacturing_outputs:
        latest = state.manufacturing_outputs[max(state.manufacturing_outputs.keys())]
        print(f"Manufacturing: ${latest.total_cost_usd}, Feasibility={latest.feasibility_score}")


def print_iteration_summary(state: GlobalState):
    """Print a summary of all iterations."""
    print("\n=== ITERATION SUMMARY ===")
    for iteration in range(state.current_iteration + 1):
        agents_active = []
        if iteration in state.mission_planner_outputs:
            agents_active.append("Mission")
        if iteration in state.aerodynamics_outputs:
            agents_active.append("Aero")
        if iteration in state.propulsion_outputs:
            agents_active.append("Prop")
        if iteration in state.structures_outputs:
            agents_active.append("Struct")
        if iteration in state.manufacturing_outputs:
            agents_active.append("Mfg")
        
        if agents_active:
            print(f"Iteration {iteration}: {', '.join(agents_active)}")


def get_project_statistics(state: GlobalState) -> dict:
    """Get project completion statistics."""
    total_messages = sum(len(mailbox.messages) for mailbox in state.mailboxes.values())
    
    agents_completed = sum(1 for outputs in [
        state.mission_planner_outputs,
        state.aerodynamics_outputs,
        state.propulsion_outputs,
        state.structures_outputs,
        state.manufacturing_outputs
    ] if outputs)
    
    return {
        "total_iterations": state.current_iteration,
        "total_messages": total_messages,
        "agents_completed": agents_completed,
        "project_complete": state.project_complete
    }