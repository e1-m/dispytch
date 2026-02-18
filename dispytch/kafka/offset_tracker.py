class OffsetTracker:
    def __init__(self, starting_offset: int):
        self.next_expected_offset = starting_offset
        self.last_committed = starting_offset - 1
        self.completed_pool = set()

    def mark_processed(self, offset: int):
        if offset < self.next_expected_offset:
            return None

        self.completed_pool.add(offset)

        if offset != self.next_expected_offset:
            return None

        while self.next_expected_offset in self.completed_pool:
            self.completed_pool.remove(self.next_expected_offset)

            self.last_committed = self.next_expected_offset
            self.next_expected_offset += 1

        return self.last_committed
