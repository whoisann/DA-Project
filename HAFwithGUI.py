
import threading
import time
import random
from queue import Queue, Empty
import tkinter as tk
from tkinter import ttk

class Node(threading.Thread):
    def __init__(self, node_id, heartbeat_queue):
        super().__init__()
        self.node_id = node_id
        self.heartbeat_queue = heartbeat_queue
        self.running = True
        # We have shared Data now
        self.replicated_memory = None

    def run(self):
        while self.running:
            if random.random() < 0.05:
                time.sleep(2)
                continue
            # The scores are randomly generated between 0.1 and 1.0 to add diversity
            availability = round(random.uniform(0.1, 1.0), 2)
            self.heartbeat_queue.put((self.node_id, availability))
            # We want to simulate real world delay
            time.sleep(random.uniform(1, 2))

    def receive_replication(self, memory):
        self.replicated_memory = memory

    def stop(self):
        self.running = False

class Coordinator(threading.Thread):
    def __init__(self, heartbeat_queue, num_nodes, node_threads, replication_factor=2, gui_callback=None):
        super().__init__()
        self.heartbeat_queue = heartbeat_queue
        self.node_scores = {}
        self.replication_factor = replication_factor
        self.num_nodes = num_nodes
        self.running = True
        self.gui_callback = gui_callback
        self.node_threads = node_threads
        # Data that we want to replicate
        self.memory_state = "Replication Data"

    def run(self):
        while self.running:
            try:
                # We send the heartbeat with the node ID and its score
                node_id, score = self.heartbeat_queue.get(timeout=1)
                self.node_scores[node_id] = score
                if self.gui_callback:
                    self.gui_callback(self.node_scores, None, self.node_threads)

                if len(self.node_scores) == self.num_nodes:
                    self.assign_replication_task()
                    # Wait 5 seconds before next assigment cycle
                    time.sleep(5)
            except Empty:
                continue

    def assign_replication_task(self):
        # Sorts scores in descending order
        sorted_nodes = sorted(self.node_scores.items(), key=lambda x: x[1], reverse=True)
        targets = [node_id for node_id, _ in sorted_nodes[:self.replication_factor]]

        # Sends the shared memory to the nodes selected
        for node_id in targets:
            if node_id in self.node_threads:
                self.node_threads[node_id].receive_replication(self.memory_state)

        # Update the GUI
        if self.gui_callback:
            self.gui_callback(self.node_scores, targets, self.node_threads)

    def stop(self):
        self.running = False

class Dashboard:
    def __init__(self, root, node_ids):
        self.root = root
        self.root.title("Heartbeat Dashboard")
        self.labels = {}
        self.replication_label = tk.Label(self.root, text="Replication Targets: -", font=("Arial", 12))
        self.replication_label.pack(pady=5)

        for node_id in node_ids:
            frame = ttk.Frame(self.root)
            frame.pack(fill="x", padx=10, pady=2)
            label = ttk.Label(frame, text=f"{node_id}: -", font=("Arial", 10), justify="left")
            label.pack(side="left")
            self.labels[node_id] = label

        self.canvas = tk.Canvas(self.root, width=500, height=300, bg="white")
        self.canvas.pack(pady=10)

        self.node_positions = {
            node_id: (100 + i * 100, 200) for i, node_id in enumerate(node_ids)
        }

        self.canvas.create_oval(230, 20, 270, 60, fill="lightblue", tags="static")
        self.canvas.create_text(250, 40, text="Coordinator", font=("Arial", 8), tags="static")

    def update(self, node_scores, replication_targets, node_threads):
        for node_id, label in self.labels.items():
            score = node_scores.get(node_id, "N/A")
            memory = getattr(node_threads[node_id], 'replicated_memory', None)
            memory_text = memory if memory else "None"
            label.config(text=f"{node_id}: {score}\nMemory: {memory_text}")

            # Display different color nodes based on scores
            if node_id in (replication_targets or []):
                label.config(foreground='green')
            elif isinstance(score, float) and score < 0.5:
                label.config(foreground='red')
            elif isinstance(score, float) and score < 0.8:
                label.config(foreground='orange')
            else:
                label.config(foreground='black')

        if replication_targets:
            self.replication_label.config(text=f"Replication Targets: {', '.join(replication_targets)}")

        self.canvas.delete("nodes")

        for node_id, (x, y) in self.node_positions.items():
            color = self._get_node_color(node_id, node_scores, replication_targets)
            self.canvas.create_oval(x-20, y-20, x+20, y+20, fill=color, tags="nodes")
            self.canvas.create_text(x, y, text=node_id, fill="black", tags="nodes")

        for target in (replication_targets or []):
            if target in self.node_positions:
                tx, ty = self.node_positions[target]
                self.canvas.create_line(250, 60, tx, ty-20, arrow=tk.LAST, fill="blue", width=2, tags="nodes")

    # Display different color nodes based on scores
    def _get_node_color(self, node_id, node_scores, replication_targets):
        score = node_scores.get(node_id, 0)
        if node_id in (replication_targets or []):
            return 'green'
        elif isinstance(score, float) and score < 0.5:
            return 'red'
        elif isinstance(score, float) and score < 0.8:
            return 'orange'
        return 'gray'

# Setup
if __name__ == "__main__":
    num_nodes = 4
    node_ids = [f'Node-{i}' for i in range(1, num_nodes + 1)]
    heartbeat_queue = Queue()

    root = tk.Tk()
    dashboard = Dashboard(root, node_ids)

    nodes = {node_id: Node(node_id, heartbeat_queue) for node_id in node_ids}
    coordinator = Coordinator(heartbeat_queue, num_nodes, nodes, gui_callback=lambda s, t, nt: root.after(0, dashboard.update, s, t, nt))

    for node in nodes.values():
        node.start()
    coordinator.start()

    try:
        root.mainloop()
    finally:
        for node in nodes.values():
            node.stop()
        coordinator.stop()
        for node in nodes.values():
            node.join()
        coordinator.join()
