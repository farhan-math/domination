from IPython.display import clear_output
from MDSP import MDSP
import pickle

def generate_mds(key_name, graph):
    solver = MDSP(graph, beta=0.1, delta_max=100)

    mds_list = {}
    for bundle in range(1,5):
        mds_list[bundle] = []

        no_of_iterations = 500
        for i in range(no_of_iterations):
            clear_output(wait=True)
            print(f"Bundle: {bundle}")
            print(f"Iteration: {i+1}/{no_of_iterations} \n")
            mds = solver.run()
            mds_list[bundle].append(mds[2])
        
        print("Done!")
        
        with open(f"{key_name}_{solver.beta}_{solver.delta_max}_{bundle}.txt", "w") as f:
            f.write(str(mds_list[bundle]))
        
        with open(f'{key_name}_{solver.beta}_{solver.delta_max}_{bundle}.pkl', 'wb') as f:
            pickle.dump(mds_list[bundle], f)