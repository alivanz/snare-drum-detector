import numpy as np

class HitDetector:
    def __init__(self, threshold: float):
        self.offset = 0
        self.threshold = threshold
        self.high = False
    
    def consume(self, data: np.ndarray):
        out = np.zeros_like(data)
        for i in range(1, len(data)):
            v = data[i]
            state = 0
            if v < self.offset:
                state = -1
                self.offset = v
            elif v > self.offset + self.threshold:
                state = 1
                self.offset = v - self.threshold
            
            if self.high:
                if state == -1:
                    out[i] = 0
                    self.high = False
                else:
                    out[i] = 1
            else:
                if state == 1:
                    out[i] = 1
                    self.high = True
                else:
                    out[i] = 0
        
        return out