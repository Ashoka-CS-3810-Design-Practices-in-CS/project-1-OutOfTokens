import heapq # for priority queue
from itertools import count # for tie-breaking in priority queue

from ..network.graph import MetroGraph
from .cost_models import CostModel


def dijkstra(graph: MetroGraph, cost: CostModel, source_station: str, dest_station: str) -> list[str] | None:
    # finds cheapest path from source to destination

    dest_nodes = set(graph.nodes_for_station(dest_station)) # all nodes of the destination station

    best: dict[str, float] = {}               # cheapest cost found so far to each node
    prev: dict[str, tuple[str, str]] = {}     # node -> (node we came from, edge id we used)
    visited: set[str] = set()                 # nodes whose cost is final

    
    heap: list[tuple[float, int, str]] = [] # priority queue of (cost, tie-breaker, node_id)
    counter = count()


    for node_id in graph.nodes_for_station(source_station): #every node of source station at time 0
        best[node_id] = 0.0
        heapq.heappush(heap, (0.0, next(counter), node_id))

    while heap:
        cost_so_far, _, node_id = heapq.heappop(heap) # pop the node with the lowest cost from the priority queue
        
        if node_id in visited:
            continue
        visited.add(node_id) # mark the node as visited so we don't process it again

        #first node finalized that is part of the destination station, we can return the path
        if node_id in dest_nodes: 
            return trace_path(prev, node_id)

        for edge in graph.neighbours(node_id): # for each edge from the current node
            
            if edge.to_node in visited: #if edge leads to a node that has already been finalized, skip it
                continue
            new_cost = cost_so_far + cost.edge_cost(edge) #calculate the cost to reach the neighbor node through this edge

            #if this new cost is cheaper than any previously recorded cost to reach the neighbor node, update the best cost and record the path.
            if edge.to_node not in best or new_cost < best[edge.to_node]:
                best[edge.to_node] = new_cost
                prev[edge.to_node] = (node_id, edge.edge_id)
                heapq.heappush(heap, (new_cost, next(counter), edge.to_node))

    return None


def trace_path(prev: dict[str, tuple[str, str]], end: str) -> list[str]:
    #returns the list of edge ids that form the path from src to dest
    edge_ids = []
    node_id = end
    #start nodes have no entry in prev, which is what ends the loop.
    while node_id in prev:
        node_id, edge_id = prev[node_id]
        edge_ids.append(edge_id)
    edge_ids.reverse()
    return edge_ids
