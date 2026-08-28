import time, numpy as np, sys, os
from hive.gcc_phat_sync import GCCPHATSync
from hive.beamformer import DelayAndSumBeamformer
from hive.position_estimator import PositionEstimator
from hive.clash_detector import ClashDetector
class Band_analyser:
    def __init__(self,GCCPHATSync: GCCPHATSync, PositionEstimator: PositionEstimator, DelayAndSumBeamformer: DelayAndSumBeamformer):
        self.GCCPHATSync = GCCPHATSync
        self.PositionEstimator = PositionEstimator
        self.DelayAndSumBeamformer = DelayAndSumBeamformer

    def analyse(self,nodes):     ### the main analysing function that will be called by the main loop
        # Placeholder for analysis logic
        print("Analyzing band...")
        sync= self.GCCPHATSync.sync_all_nodes(nodes)
        positions = self.PositionEstimator.estimate_all_positions(sync)
        if not node:
            return empty_result
        
        
        
        