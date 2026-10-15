class SimulationTarget:
    """Known-bad mathematical model. Fault is a returned event, not a process crash."""
    def send(self, c):
        if c.declared_length > 64:
            return {'target_outcome':'SIMULATED_FAULT','return_code':None,'response_length':0}
        if (c.operation != 'ECHO' or c.declared_length != len(bytes.fromhex(c.payload_hex))
                or c.offset < 0 or c.offset > len(bytes.fromhex(c.payload_hex)) or c.flags != 0):
            return {'target_outcome':'ERROR_REPLY','return_code':22,'response_length':0}
        return {'target_outcome':'REPLY','return_code':0,'response_length':c.declared_length}

class QnxTransport:
    def send(self, c):
        raise NotImplementedError('Native QNX transport is not implemented or validated; no simulated fallback')
