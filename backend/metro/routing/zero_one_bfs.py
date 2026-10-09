from collections import deque # a queue that lets you add to the front or the back

from ..network.graph import MetroGraph
from .dijkstra import trace_path


def zero_one_bfs(graph: MetroGraph, source_station: str, dest_station: str) -> list[str] | None:
    # finds the route that passes through the fewest stations

    dest_nodes = set(graph.nodes_for_station(dest_station)) # all nodes of the destination station

    best: dict[str, int] = {}                 # fewest train rides found so far to reach each node
    prev: dict[str, tuple[str, str]] = {}     # node -> (node we came from, edge id we used)

    queue: deque[str] = deque() # nodes waiting to be looked at

    for node_id in graph.nodes_for_station(source_station): #every node of source station starts at 0 rides
        best[node_id] = 0
        queue.append(node_id)

    while queue:
        node_id = queue.popleft() # take the node at the front of the queue

        #first node of the destination station to reach the front, we can return the path
        if node_id in dest_nodes:
            return trace_path(prev, node_id)

        for edge in graph.neighbours(node_id): # for each edge from the current node

            step= 1 if edge.kind == "ride" else 0
            new_count = best[node_id] + step # rides needed to reach the neighbour through this edge

            #if we already know a way to the neighbour that is just as good, skip it
            if edge.to_node in best and best[edge.to_node] <= new_count:
                continue
            best[edge.to_node] = new_count
            prev[edge.to_node] = (node_id, edge.edge_id)

            if edge.kind == "walk":
                queue.appendleft(edge.to_node)
            else:
                queue.append(edge.to_node)
    return None