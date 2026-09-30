from typing import List, TypedDict


class AgentState(TypedDict):
  query: str
  sub_queries: List[str]
  retrieved_docs: List[str]
  critique: str
  generation: str
  loop_count: int