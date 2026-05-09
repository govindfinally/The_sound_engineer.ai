# GCC-PHAT(τ) = IFFT [ X₁(f) · X₂*(f) / |X₁(f) · X₂*(f)| ] the formula for GCC-PHAT, where X₁ and X₂ are the FFTs of the two signals, and * denotes complex conjugation.
from ast import Return
from itertools import combinations
from typing import List, Dict
import sys
import numpy as np
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from quantitative_analyzer import compute_fft

class GCCPHATSync:
    def __init__(self, sample_rate=44100):
        self.sample_rate= sample_rate
        self.pcm_bytes = {} # phoneID → PCM bytes buffer
        
    def compute_delay(self, fft1, fft2) -> dict:
        # Returns: {delay_samples, delay_seconds, distance_m, confidence}
        x1= fft1
        x2= fft2
        R = x1 * np.conj(x2) # Cross-power spectrum
        R_phat = R / (np.abs(R) + 1e-10) # GCC-PHAT
        corr = np.fft.irfft(R_phat)
        delay_samples = np.argmax(np.abs(corr)) # find peak
        N=len(corr)
        if delay_samples> N//2:
            delay_samples -= N # handle wrap-around
        delay_seconds = delay_samples/self.sample_rate
        distance_meters = delay_seconds * 343 
        correlation_peak = np.max(np.abs(corr))
        confidence =correlation_peak
        return {delay_samples, delay_seconds, distance_meters, confidence}  
        
        
    def sync_all_nodes(self, nodes: list) -> dict:
        # Computes delay between every pair of nodes
        # Returns: {(phone1_id, phone2_id): delay_dict}\
        phone_ids = [node.phoneID for node in nodes]
        delays = {}
        for phone1, phone2 in combinations(phone_ids, 2):
            fft1 = compute_fft(self.pcm_bytes[phone1])
            fft2 = compute_fft(self.pcm_bytes[phone2])
            delay_info = self.compute_delay(fft1, fft2)
            delays[(phone1, phone2)] = delay_info
        return delays
        
    
        
    def get_delay_matrix(self, nodes: list) -> np.ndarray:
        # N×N matrix of delays — used by beamformer
        phone_ids = [node.phoneID for node in nodes]
        N = len(phone_ids)
        delay_matrix = np.zeros((N, N))
        return delay_matrix
if __name__ == "__main__":
    # Example usage
    sync = GCCPHATSync(sample_rate=44100)
    # Simulate two audio buffers (sine waves with a delay)
    fs = 44100
    t = np.linspace(0, 1, fs)
    signal1 = np.sin(2 * np.pi * 440 * t) # A4 note
    delay_samples = 1000 # ~22.7ms delay
    signal2 = np.concatenate((np.zeros(delay_samples), signal1[:-delay_samples]))
    sync.pcm_bytes['phone1'] = signal1
    sync.pcm_bytes['phone2'] = signal2
    fft1 = compute_fft(signal1,sync.sample_rate)
    fft2 = compute_fft(signal2,sync.sample_rate)
    
    delay_info = sync.compute_delay(fft1, fft2)
    print(delay_info)

