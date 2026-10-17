from collections import defaultdict, deque

class Defense:
    def __init__(self, cfg):
        self.cfg = cfg
        self.windows = defaultdict(deque)

    def decide(self, c, now_ms):
        payload = bytes.fromhex(c.payload_hex)
        if c.operation != 'ECHO': return 'BLOCK', 'invalid_type'
        if c.declared_length < 0 or c.declared_length > self.cfg['max_payload']:
            return 'BLOCK', 'length_range'
        if c.declared_length != len(payload): return 'BLOCK', 'length_mismatch'
        if c.offset < 0 or c.offset > len(payload): return 'BLOCK', 'offset_range'
        if c.flags != 0: return 'BLOCK', 'unsupported_flags'
        # SEC-04 / user decision 2026-10-17: count forwarded valid requests only.
        # Rejected arrivals do not consume a slot or prolong the window.
        q = self.windows[c.session_id]
        while q and q[0] <= now_ms - self.cfg['window_ms']: q.popleft()
        if len(q) >= self.cfg['max_requests_per_window']:
            return 'RATE_LIMIT', 'session_window'
        q.append(now_ms)
        return 'ALLOW', 'valid'
