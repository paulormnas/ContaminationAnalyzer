# coding=utf-8
from graph_tool.all import *
import SpreadModels
import SaveData

class CSER:
    """This class is responsible for implement the Scheduling by Edge Reversal algorithm and control the simulation."""

    def __init__(self):
        self.sm = SpreadModels.CSIR()
        self.sinks = []
        self.iterations = 0
        self.vertex_states = {}
        self.sv = SaveData.CSaveData()

    def get_iterations_number(self):
        return self.iterations

    def run(self, g, is_forward, go):
        """Verify if is a forward or backward step and revert the edges accordingly to each movement"""
        if is_forward:
            self.concurrency_measure(g)
            self.save_vertex_state(graph=g)
            self.iterations += 1
        elif self.iterations > 0:
            self.identify_last_sinks(g)
            self.iterations -= 1

        self.revert_edge(graph=g, is_forward=is_forward)
        self.spread_infection(graph=g, is_forward=is_forward, group_observed=go)
        return g

    def reset(self, g, go):
        """Runs the SER algorithm backwards until it reaches the initial state"""
        while self.iterations:
            g = self.run(g=g, is_forward=False, go=go)
        return g

    def save_vertex_state(self, graph):
        states = {}
        for v in graph.vertices():
            states[graph.vertex_index[v]] = list(graph.vertex_properties.state[v])
        self.vertex_states[self.iterations] = states

    def concurrency_measure(self, graph):
        """Identify the vertices that are sink in this moment and create a list with they indexes."""
        self.sinks = []
        for v in graph.vertices():
            if (v.in_degree() > 0) and (v.out_degree() == 0):
                self.sinks.append(graph.vertex_index[v])

    def identify_last_sinks(self, graph):
        """Identify the vertices that operated in the last iteration and create a list with they indexes."""
        self.sinks = []
        for v in graph.vertices():
            if (v.out_degree() > 0) and (v.in_degree() == 0):
                self.sinks.append(graph.vertex_index[v])

    def revert_edge(self, graph, is_forward):
        """Revert all edges of all vertices in self.sinks list, regarding as a step forward or backward"""
        for sink in self.sinks:
            if is_forward:
                neighbors_list = graph.get_in_neighbors(sink)
            else:
                neighbors_list = graph.get_out_neighbors(sink)

            for neighbor in neighbors_list:
                if is_forward:
                    old_edge = graph.edge(neighbor, sink)
                    new_edge = graph.add_edge(sink, neighbor)
                else:
                    old_edge = graph.edge(sink, neighbor)
                    new_edge = graph.add_edge(neighbor, sink)

                # eprop_criterio = graph.edge_properties["contaminationCriteria"]
                # eprop_criterio[(new_edge.source(), new_edge.target())] = eprop_criterio[(old_edge.source(), old_edge.target())]
                # graph.edge_properties["contaminationCriteria"] = eprop_criterio
                graph.remove_edge(old_edge)

    def random_infect_specie(self, graph, group):
        """
        Infect random species inserted on simulation graph by changing it's state.

        :param graph: Graph that handle the species on simulation
        :type graph: graph_tool.Graph
        :param group: Tc group selected on the combobox by user
        :type group: str
        :return: None
        :rtype: None
        """
        self.sm.random_infect(g=graph, grp=group)

    def spread_infection(self, graph, is_forward, group_observed):
        """
        Spread the infection from source vertices to their neighbors after revert the edges using SER algorithm
        :param graph: Graph that handle the species on simulation
        :type graph: graph_tool.Graph
        :param is_forward: Define if the simulation is running a step forward or backward
        :type is_forward: bool
        :param group_observed: Tc group that is being observed by the user
        :type str
        :return: None
        :rtype: None
        """
        for source in self.sinks:  # After revert edges the sinks become sources
            count = len(graph.vertex_properties.group[source])
            for index in range(0, count):
                self.sm.infect(graph=graph,
                               group_observed=group_observed,
                               index=index,
                               source=source,
                               is_forward=is_forward,
                               vertex_states=self.vertex_states,
                               iteration=self.iterations)
