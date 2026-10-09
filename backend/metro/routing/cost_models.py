from typing import Protocol

from ..network.models import Edge


class CostModel(Protocol):
    #assigns a cost to each edge in the graph

    def edge_cost(self, edge: Edge) -> float: ...


class TimeCost:
    #fastest route, cost is travel time in minutes

    def edge_cost(self, edge: Edge) -> float:
        return edge.travel_min


class InterchangePenaltyCost:
    #fewest line changes: changing line costs so much that travel time only breaks ties

    def edge_cost(self, edge: Edge) -> float:
        if edge.kind == "walk":
            return edge.travel_min + 100000 # interchange is now the last resort 
        return edge.travel_min