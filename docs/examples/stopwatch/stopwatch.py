class Stopwatch:
    def __init__(self):
        self.elapsed_time = 0
        self.split_time = 0
        self.is_split = False
        self.running = False

    def start(self):
        # Start internal timer
        self.running = True

    def stop(self):
        # Stop internal timer
        self.running = False

    def reset(self):
        # Reset internal timer
        self.elapsed_time = 0

    def split(self):
        # Split time
        if not self.is_split:
            self.is_split = True
            self.split_time = self.elapsed_time

    def unsplit(self):
        # Unsplit time
        if self.is_split:
            self.is_split = False

    def display(self):
        # Return the value to display
        if self.is_split:
            return int(self.split_time)
        else:
            return int(self.elapsed_time)

    def update(self, delta):
        # Update internal timer of ``delta`` seconds
        if self.running:
            self.elapsed_time += delta
