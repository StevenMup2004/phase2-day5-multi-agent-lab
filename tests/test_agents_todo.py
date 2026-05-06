from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_initially() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state = SupervisorAgent(max_iterations=3).run(state)
    assert state.route_history[-1] == "researcher"
    assert state.iteration == 1
