# DA-Project

This repo presents a heartbeat-based replication coordination system where a central 
coordinator monitors some distributed nodes. Each node gives back a periodic heartbeat 
signal with an availability score representing its current health or performance. The 
coordinator then selects a subset of the nodes as replication targets based on their scores, 
also replicating a shared memory block of data to those targets.
