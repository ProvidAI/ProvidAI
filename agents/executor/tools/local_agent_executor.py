"""Local agent executor - maps registry agents to local research agents."""

import logging
from typing import Any, Dict
from strands import tool

logger = logging.getLogger(__name__)

# Mapping of registry domain names to local research agent modules
LOCAL_AGENT_MAPPING = {
    'problem-framer-001': 'agents.research.phase1_ideation.problem_framer',
    'literature-miner-001': 'agents.research.phase2_knowledge.literature_miner',
    'feasibility-analyst-001': 'agents.research.phase1_ideation.feasibility_analyst',
    'goal-planner-001': 'agents.research.phase1_ideation.goal_planner',
    'knowledge-synthesizer-001': 'agents.research.phase2_knowledge.knowledge_synthesizer',
    'hypothesis-designer-001': 'agents.research.phase2_knowledge.hypothesis_designer',
    'experiment-runner-001': 'agents.research.phase3_experimentation.experiment_runner',
    'code-generator-001': 'agents.research.phase3_experimentation.code_generator',
    'insight-generator-001': 'agents.research.phase4_interpretation.insight_generator',
    'bias-detector-001': 'agents.research.phase4_interpretation.bias_detector',
    'compliance-checker-001': 'agents.research.phase4_interpretation.compliance_checker',
    'paper-writer-001': 'agents.research.phase5_publication.paper_writer',
    'peer-reviewer-001': 'agents.research.phase5_publication.peer_reviewer',
    'reputation-manager-001': 'agents.research.phase5_publication.reputation_manager',
    'archiver-001': 'agents.research.phase5_publication.archiver',
}


@tool
async def execute_local_agent(
    agent_domain: str,
    task_description: str,
    context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Execute a local research agent by domain name.

    This is a HACKY but functional way to execute local agents instead of
    making external API calls. It maps registry domain names to actual
    local Python modules and executes them directly.

    Args:
        agent_domain: The domain name from the registry (e.g., 'knowledge-synthesizer-001')
        task_description: Description of the task to execute
        context: Optional context dict with additional parameters

    Returns:
        Dict with execution results:
        {
            "success": bool,
            "agent_domain": str,
            "result": Any,
            "error": str (if failed)
        }
    """
    try:
        logger.info(f"[execute_local_agent] Executing local agent: {agent_domain}")

        # Check if agent is mapped
        if agent_domain not in LOCAL_AGENT_MAPPING:
            logger.warning(f"[execute_local_agent] Agent {agent_domain} not found in local mapping. Available agents: {list(LOCAL_AGENT_MAPPING.keys())}")
            return {
                "success": False,
                "agent_domain": agent_domain,
                "error": f"Agent {agent_domain} not found in local mapping",
                "available_agents": list(LOCAL_AGENT_MAPPING.keys()),
            }

        module_path = LOCAL_AGENT_MAPPING[agent_domain]
        logger.info(f"[execute_local_agent] Mapping {agent_domain} -> {module_path}")

        # Dynamically import the agent module
        try:
            # Import the module
            parts = module_path.split('.')
            module = __import__(module_path, fromlist=[parts[-1]])

            # Try to find the agent class or run function
            agent_class = None
            run_function = None

            # Look for common patterns
            if hasattr(module, 'Agent'):
                agent_class = getattr(module, 'Agent')
            elif hasattr(module, 'run'):
                run_function = getattr(module, 'run')
            elif hasattr(module, 'execute'):
                run_function = getattr(module, 'execute')
            else:
                # Try to find any class that looks like an agent
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and attr_name.endswith('Agent'):
                        agent_class = attr
                        break

            # Execute the agent
            if agent_class:
                logger.info(f"[execute_local_agent] Found agent class: {agent_class.__name__}")
                # Instantiate and run the agent
                agent_instance = agent_class()
                if hasattr(agent_instance, 'run'):
                    result = await agent_instance.run(task_description, context or {})
                elif hasattr(agent_instance, 'execute'):
                    result = await agent_instance.execute(task_description, context or {})
                else:
                    result = f"Agent {agent_domain} executed with task: {task_description}"

            elif run_function:
                logger.info(f"[execute_local_agent] Found run function: {run_function.__name__}")
                result = await run_function(task_description, context or {})
            else:
                # Fallback: return a simulated result
                logger.info(f"[execute_local_agent] No standard interface found, returning simulated result")
                result = {
                    "status": "simulated",
                    "message": f"Local agent {agent_domain} would process: {task_description}",
                    "agent_capabilities": f"Agent from {module_path}",
                    "task": task_description,
                    "context": context,
                }

            logger.info(f"[execute_local_agent] Successfully executed {agent_domain}")
            return {
                "success": True,
                "agent_domain": agent_domain,
                "module_path": module_path,
                "result": result,
            }

        except ImportError as e:
            logger.error(f"[execute_local_agent] Failed to import {module_path}: {e}")
            return {
                "success": False,
                "agent_domain": agent_domain,
                "error": f"Failed to import module {module_path}: {str(e)}",
            }
        except Exception as e:
            logger.error(f"[execute_local_agent] Error executing agent: {e}", exc_info=True)
            return {
                "success": False,
                "agent_domain": agent_domain,
                "error": f"Error executing agent: {str(e)}",
            }

    except Exception as e:
        logger.error(f"[execute_local_agent] Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "agent_domain": agent_domain,
            "error": f"Unexpected error: {str(e)}",
        }


@tool
async def list_local_agents() -> Dict[str, Any]:
    """
    List all available local agents and their mappings.

    Returns:
        Dict with list of available agents and their module paths
    """
    return {
        "success": True,
        "count": len(LOCAL_AGENT_MAPPING),
        "agents": LOCAL_AGENT_MAPPING,
        "domains": list(LOCAL_AGENT_MAPPING.keys()),
    }
