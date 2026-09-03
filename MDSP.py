import networkx as nx
import random
from IPython.display import display
from collections import Counter

class MDSP:
    def __init__(self, G, beta=0.1, delta_max=100):
        """
        Initializes the algorithm with the graph and parameters.
        - G: networkx graph
        - beta: % of nodes to remove during destruction
        - delta_max: stopping criterion (max iterations without improvement)
        """
        self.G = G
        self.nodes = list(self.G.nodes())

        self.beta = beta
        self.delta_max = delta_max

        # Pre-identify Leaf (L) and Support Vertices (SV) to optimize search
        self.L = {v for v in self.nodes if self.G.degree(v) == 1}
        self.SV = {list(self.G[v])[0] for v in self.L}

    def random_max(self, iterable, key_func):
        """
        Returns a random element of an iterable which attains a maximum
        with respect to a key function.
        """
        max_val = float('-inf')
        candidates = []

        for item in iterable:
            val = key_func(item)
            if val > max_val:
                max_val = val
                candidates = [item]
            elif val == max_val:
                candidates.append(item)

        return random.choice(candidates)

    # the following functions are modified from the source:
    # https://networkx.org/documentation/stable/_modules/networkx/algorithms/approximation/dominating_set.html

    def gip(self, node_and_neighborhood, dom_set):
        """
        Returns the greedy function (GIP) value of a given node.

        `node_and_neighborhood` is a two-tuple comprising a node and its
        closed neighborhood.
        """
        v, neighborhood = node_and_neighborhood
        return len(neighborhood - dom_set)

    def check_p(self, dom_set):
        """
        Checking Procedure (CheckP): Ensures the dominating set is minimal
        by removing redundant vertices.
        """
        # 1. Create a static list to shuffle and iterate over safely
        nodes_to_check = list(dom_set)
        random.shuffle(nodes_to_check)

        # 2. Pre-calculate coverage for the entire graph
        # Only nodes in the neighborhood of D matter, but a dict for all is safer.
        coverage = {node: 0 for node in self.nodes}
        for node in nodes_to_check:
            coverage[node] += 1
            for nbr in self.G[node]:
                coverage[nbr] += 1

        # current_D starts as a copy of the input set
        current_D = dom_set.copy()

        # 3. Process each node in the shuffled list
        for node in nodes_to_check:
            # A node v is redundant if every node in its closed neighborhood N[v]
            # is covered by at least 2 nodes (itself and at least one other in D).

            # Check v itself first
            if coverage[node] < 2:
                continue

            # Check all neighbors of v
            is_redundant = True
            for nbr in self.G[node]:
                if coverage[nbr] < 2:
                    is_redundant = False
                    break

            if is_redundant:
                current_D.remove(node)
                # Update coverage counts since v is no longer in the dominating set
                coverage[node] -= 1
                for nbr in self.G[node]:
                    coverage[nbr] -= 1

        return current_D

    def initial_solution(self):
        """
        Greedy Insertion Procedure (GIP): Starts with Support Vertices
        and builds a feasible minimal dominating set.
        """
        dom_set = self.SV.copy()
        covered_by_dom_set = self.SV.copy()
        for v in dom_set:
            nbrs = set(self.G[v])
            covered_by_dom_set.update(nbrs)

        # This is a set of all vertices not already covered by the
        # dominating set.
        vertices = set(self.G) - covered_by_dom_set
        candidates = set(self.G) - dom_set - self.L
        
        # This is a dictionary mapping each candidate to its closed neighborhood
        neighborhoods = {v: {v} | set(self.G[v]) for v in candidates}

        while vertices:
            # Choose a candidate with maximum GIP value, along with its
            # closed neighborhood.
            dom_node, max_set = self.random_max(
                neighborhoods.items(),
                key_func=lambda x: self.gip(x, dom_set)
            )

            # Add the node to the dominating set and reduce the remaining
            # set of nodes to cover.
            dom_set.add(dom_node)
            del neighborhoods[dom_node]
            vertices -= max_set

        return self.check_p(dom_set)

    def local_improvement(self, dom_set):
        """
        Performs swaps to obtain a smaller dominating set.
        """
        coverage = {node: 0 for node in self.nodes}
        for node in dom_set:
            coverage[node] += 1
            for nbr in self.G[node]:
                coverage[nbr] += 1
        
        dom_list = list(dom_set)
        random.shuffle(dom_list)

        for u in dom_list:
            # 1. Find critical nodes (those only covered by u)
            # u's closed neighborhood: N[u]
            u_nbrs = list(self.G[u]) + [u]
            critical_w = [w for w in u_nbrs if coverage[w] == 1]

            # 2. Find a replacement v
            # v MUST be in the intersection of N[w] for all w in critical_w
            if not critical_w:
                # If no critical nodes, u is already redundant!
                candidates = [v for v in self.nodes if v not in dom_set]
            else:
                # Any candidate v MUST cover the first critical node
                first_w = critical_w[0]
                potential_vs = (set(self.G[first_w]) | {first_w}) - dom_set

                # Further filter: v must cover ALL other critical nodes
                candidates = []
                for v in potential_vs:
                    v_nbrs = set(self.G[v]) | {v}
                    if all(w in v_nbrs for w in critical_w[1:]):
                        candidates.append(v)

            random.shuffle(candidates)

            for v in candidates:
                # Predict feasibility: If u is replaced by v,
                # we then check if check_p can reduce the size.
                temp_set = (dom_set - {u}) | {v}
                improved_set = self.check_p(temp_set)

                if len(improved_set) < len(dom_set):
                    return improved_set
        return dom_set

    def run(self, D=None):
        """Main Iterated Greedy Loop."""

        # Step 1: Initialization
        if not D:
            D = self.initial_solution()
        print(f"Initial solution size  = {len(D)}")
        # Save the initial solution
        initial_D = D.copy()

        # Step 2: First Local Improvement
        D_b = self.local_improvement(D)
        # Save the first local improvement
        first_local_improvement_D = D_b.copy()

        # Step 3: Construction
        progress = display("", display_id=True)
        improv, delta = 0, 0
        while delta < self.delta_max:
            msg = f"Improvement #{improv}, size = {len(D_b)}, Delta #{delta}"
            if progress is not None:
                # Jupyter Notebook environment
                progress.update(msg)
            else:
                # Terminal script environment
                print(msg, end="\r")

            # Step 5: Destruction
            num_remove = max(1, int(self.beta * len(D_b)))
            D_d = set(random.sample(list(D_b), len(D_b) - num_remove))

            # Step 6: Reconstruction
            D_r = D_d.copy()
            covered_by_D_r = D_d.copy()
            for v in D_d:
                nbrs = set(self.G[v])
                covered_by_D_r.update(nbrs)
    
            # This is a set of all vertices not already covered by the
            # dominating set.
            vertices = set(self.G) - covered_by_D_r
            candidates = set(self.G) - D_r - self.L
    
            # This is a dictionary mapping each node to the closed neighborhood
            # of that node.
            neighborhoods = {v: {v} | set(self.G[v]) for v in candidates}
    
            while vertices:
                # Choose a node with maximum GIP value, along with its
                # closed neighborhood.
                dom_node, max_set = self.random_max(
                    neighborhoods.items(),
                    key_func=lambda x: self.gip(x, D_r)
                )
    
                # Add the node to the dominating set and reduce the remaining
                # set of nodes to cover.
                D_r.add(dom_node)
                del neighborhoods[dom_node]
                vertices -= max_set

            # Step 7: Local Improvement on reconstructed set
            D_i = self.local_improvement(D_r)

            # Steps 8-12: Acceptance and Update
            if len(D_i) < len(D_b):
                D_b = D_i
                delta = 0
                improv += 1
            else:
                delta += 1
        print("\nConstruction complete!")
        print(f"Final length: {len(D_b)}")
        
        return initial_D, first_local_improvement_D, D_b # Step 15