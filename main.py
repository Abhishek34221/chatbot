from agents import critic_node, generator_node, retrieval_node, router_node
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from state import AgentState

load_dotenv()


def should_continue(state: AgentState):
  """Determines whether to retry retrieval or proceed to response generation."""
  if state["critique"] == "NEEDS_MORE_DATA":
    print("--- DECISION: Critic requested more data. Retrying retrieval. ---")
    return "retriever"
  return "generator"


def build_graph():
  workflow = StateGraph(AgentState)

  # Register nodes
  workflow.add_node("router", router_node)
  workflow.add_node("retriever", retrieval_node)
  workflow.add_node("critic", critic_node)
  workflow.add_node("generator", generator_node)

  # Define control flow edges
  workflow.set_entry_point("router")
  workflow.add_edge("router", "retriever")
  workflow.add_edge("retriever", "critic")

  # Conditional routing based on Critic evaluation
  workflow.add_conditional_edges(
      "critic",
      should_continue,
      {"retriever": "retriever", "generator": "generator"},
  )

  workflow.add_edge("generator", END)

  return workflow.compile()


if __name__ == "__main__":
  app = build_graph()

  # Test queries
  test_queries = [
      "What is our company's remote work policy?",
      "How much are prescription drug copays for brand name drugs?",
  ]

  for q in test_queries:
    print(f"\n==============================")
    print(f"USER QUERY: {q}")
    print(f"==============================")

    initial_state = {
        "query": q,
        "sub_queries": [],
        "retrieved_docs": [],
        "critique": "",
        "generation": "",
        "loop_code": 0,
    }

    final_state = app.invoke(initial_state)

    print(f"\nFINAL ANSWER:\n{final_state['generation']}")