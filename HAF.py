import threading
import time
import random
from queue import Queue

class Node(threading.Thread):
    def __init__(self, node_id, heartbeat_queue):
        super().__init__()
        self.node_id = node_id
        self.heartbeat_queue = heartbeat_queue
        self.running = True

    def run(self):
        while self.running:
            # The scores are randomly generated between 0.7 and 1.0
            availability = round(random.uniform(0.7, 1.0), 2)
            self.heartbeat_queue.put((self.node_id, availability))
            # We want to simulate real world delay
            time.sleep(random.uniform(1, 2))

    def stop(self):
        self.running = False

class Coordinator(threading.Thread):
    def __init__(self, heartbeat_queue, num_nodes, replication_factor=2):
        super().__init__()
        self.heartbeat_queue = heartbeat_queue
        self.node_scores = {}
        self.replication_factor = replication_factor
        self.num_nodes = num_nodes
        self.running = True

    def run(self):
        while self.running:
            while not self.heartbeat_queue.empty():
                # We send the heartbeat with the node ID and its score
                node_id, score = self.heartbeat_queue.get()
                self.node_scores[node_id] = score
                # Display each node with its availability score
                print(f"[Heartbeat] Node {node_id} -> Availability: {score}")

            if len(self.node_scores) == self.num_nodes:
                self.assign_replication_task()
                # Wait 5 seconds before next assigment cycle
                time.sleep(5)

    def assign_replication_task(self):
        # Sorts scores in descending order
        sorted_nodes = sorted(self.node_scores.items(), key=lambda x: x[1], reverse=True)
        targets = [node_id for node_id, _ in sorted_nodes[:self.replication_factor]]
        print(f"[Coordinator] Assigning replication to: {targets}")

    def stop(self):
        self.running = False

# Setup
num_nodes = 4
heartbeat_queue = Queue()
nodes = [Node(f'Node-{i}', heartbeat_queue) for i in range(1, num_nodes + 1)]
coordinator = Coordinator(heartbeat_queue, num_nodes)

# Start simulation
for node in nodes:
    node.start()
coordinator.start()

# Run for 15 seconds
time.sleep(15)

# Stop
for node in nodes:
    node.stop()
coordinator.stop()

for node in nodes:
    node.join()
coordinator.join()
