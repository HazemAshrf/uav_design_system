"""Main entry point for the UAV Design Agent Coordination System."""

import asyncio
from dotenv import load_dotenv

from state import GlobalState
from workflow import create_uav_design_workflow
from helpers import print_final_design, print_iteration_summary, get_project_statistics

# Load environment variables
load_dotenv()


async def run_uav_design_project(requirements: str) -> GlobalState:
    """Run the UAV design project with the given requirements."""
    initial_state = GlobalState(
        user_requirements=requirements,
        current_iteration=0
    )
    
    workflow = create_uav_design_workflow()
    return await workflow.ainvoke(initial_state)


async def main():
    """Main execution function with example UAV design project."""
    # Example requirements for surveillance UAV
    requirements = """
    Design a surveillance UAV with these requirements:
    - Range: 50 km
    - Payload: 2 kg camera system  
    - Flight time: 1.5 hours
    - Altitude: 1000-2000 m
    - Budget: $25,000
    - Must be manufacturable and cost-effective
    - Weather resistance for light rain
    - Autonomous operation capability
    """
    
    print("🚁 UAV Design Agent Coordination System")
    print("=" * 60)
    print("Starting UAV Design Project...")
    print(f"Requirements: {requirements.strip()}")
    print("=" * 60)
    
    try:
        # Run the design project
        final_state = await run_uav_design_project(requirements)
        
        # Print results
        print(f"\n✅ Project completed after {final_state.current_iteration} iterations")
        
        # Print final design
        print_final_design(final_state)
        
        # Print iteration summary
        print_iteration_summary(final_state)
        
        # Print statistics
        stats = get_project_statistics(final_state)
        print(f"\n📊 Project Statistics:")
        print(f"   Total Iterations: {stats['total_iterations']}")
        print(f"   Total Messages: {stats['total_messages']}")
        print(f"   Agents Completed: {stats['agents_completed']}/5")
        print(f"   Project Status: {'✅ Complete' if stats['project_complete'] else '❌ Incomplete'}")
        
        # Print completion reason if available
        if final_state.coordinator_outputs:
            latest_coord = final_state.coordinator_outputs[max(final_state.coordinator_outputs.keys())]
            print(f"\n📝 Completion Reason: {latest_coord.completion_reason}")
        
    except Exception as e:
        print(f"❌ Error running UAV design project: {e}")
        import traceback
        traceback.print_exc()


async def run_custom_project():
    """Run a custom UAV design project with user input."""
    print("🚁 Custom UAV Design Project")
    print("=" * 40)
    
    requirements = input("Enter your UAV design requirements:\n")
    
    if not requirements.strip():
        print("No requirements provided. Using default example.")
        await main()
        return
    
    try:
        final_state = await run_uav_design_project(requirements)
        
        print(f"\n✅ Custom project completed after {final_state.current_iteration} iterations")
        print_final_design(final_state)
        
        stats = get_project_statistics(final_state)
        print(f"\n📊 Project completed with {stats['total_messages']} total messages exchanged")
        
    except Exception as e:
        print(f"❌ Error running custom project: {e}")


if __name__ == "__main__":
    print("UAV Design Agent Coordination System - Structured Architecture")
    print("Features:")
    print("✅ Modular file structure with clear separation of concerns")
    print("✅ Async agent coordination with dependency checking")
    print("✅ LLM-generated outputs in Pydantic format") 
    print("✅ Real tool calling with domain-specific tools")
    print("✅ Agent-decided messaging system")
    print("✅ Coordinator task assignment and completion evaluation")
    print("✅ Stability-based iteration control")
    print("✅ Comprehensive logging and statistics")
    print("\nOptions:")
    print("1. Run example surveillance UAV project: python main.py")
    print("2. Run custom project (interactive): Uncomment run_custom_project() below")
    print("\nMake sure to set OPENROUTER_API_KEY in your .env file!")
    print("=" * 80)
    
    # Run the example project
    asyncio.run(main())
    
    # Uncomment the line below to run custom project instead
    # asyncio.run(run_custom_project())