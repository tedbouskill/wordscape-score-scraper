import logging
import time

from datetime import datetime

class MetricsTrackerSingleton:
    """A singleton class to track processing statistics (rows, files, etc.)."""
    
    _instance = None
    
    def __new__(cls):
        """
        Override __new__ to ensure only one instance (singleton).
        """
        if cls._instance is None:
            cls._instance = super(MetricsTrackerSingleton, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Actual initialization only runs once, regardless of how many times
        StatsTracker() is called.
        """
        if not self._initialized:
            self._initialized = True
            self.reset()

    def reset(self):
        """Reset counters and time tracking."""
        self.start_time = None
        self.end_time = None
        
        self.total_to_process = 0
        self.processed_count = 0
        
        self.error_count = 0
        self.failed_count = 0
        
        self.object_name = ""
        
        # Dictionaries to track which items had errors/failures and how many
        self.errors_dict = {}   # {item_identifier: count_of_errors}
        self.failures_dict = {} # {item_identifier: failure_reason or count_of_failures}

    def start(self, object_name="item", total_to_process=None):
        """
        Record the start time and optionally the total items (rows/files)
        to process.
        """
        self.reset()
        self.object_name = object_name
        self.start_time = datetime.now()
        
        if total_to_process is not None:
            self.total_to_process = total_to_process
        
        # Print starting info
        if self.total_to_process:
            print(f"Start time: {self.start_time}")
            print(f"Total {self.object_name}s to be processed: {self.total_to_process}")
        else:
            print(f"Start time: {self.start_time}")
            print(f"Processing all {self.object_name}s found (no limit).")

    def end(self):
        """Record the end time, calculate durations, and print statistics."""
        self.end_time = datetime.now()
        total_time = (self.end_time - self.start_time).total_seconds()
        
        items_processed = self.processed_count + self.error_count + self.failed_count
        if items_processed == 0:
            # Edge case: if nothing was processed
            print(f"No {self.object_name}s were actually processed.")
            return
        
        # Print how many items processed in total
        print(f"\n--- Summary of {self.object_name} processing ---")
        print(f"\tTotal {self.object_name}s processed: {items_processed} with {self.processed_count} successful.")
        print(f"\tTotal {self.object_name}s not processed: {self.total_to_process - self.processed_count + self.failed_count}")
        
        # Per-item statistics
        time_per_item = total_time / items_processed
        print(f"\tTime per {self.object_name}: {time_per_item:.2f} seconds")
        
        # If total time > 2 minutes, show approximate items per minute
        if total_time > 120:
            ipm = items_processed / (total_time / 60.0)
            print(f"\tApprox {ipm:.0f} {self.object_name} processed per minute.")
        
        # Print errors/failures if any
        if self.error_count:
            print(f"\tTotal {self.object_name} errors: {self.error_count}")
        if self.failed_count:
            print(f"\tTotal {self.object_name} failed: {self.failed_count}")
        
        # Print total runtime
        minutes, seconds = divmod(total_time, 60)
        if minutes:
            print(f"\tTotal processing time: {int(minutes)} minute(s) {seconds:.2f} seconds.")
        else:
            print(f"\tTotal processing time: {seconds:.2f} seconds.")

        # Print out error details if any
        if self.errors_dict:
            logging.error("Items with errors:")
            for item, err_count in self.errors_dict.items():
                logging.error(f"{item}: {err_count} error(s)")
        
        # Print out failure details if any
        if self.failures_dict:
            logging.critical("Items that failed completely:")
            for item, reason_or_count in self.failures_dict.items():
                logging.critical(f"{item}: {reason_or_count}")

        print("--- End of Summary ---\n")

    # Methods to increment counters
    def increment_processed(self):
        """Increment the count for successfully processed items."""
        self.processed_count += 1

    def increment_error(self, item_identifier=None, increment=1):
        """
        Increment the count for items processed with (recoverable) errors.
        Optionally, track which item had an error.
        """
        self.error_count += increment
        
        if item_identifier:
            if item_identifier not in self.errors_dict:
                self.errors_dict[item_identifier] = 0
            self.errors_dict[item_identifier] += increment

    def increment_failed(self, item_identifier=None, failure_info=None):
        """
        Increment the count for items that failed completely.
        You can store a reason or exception message in failures_dict.
        """
        self.failed_count += 1
        
        if item_identifier:
            # You could store just a count or a reason.
            # For demonstration, let's store the reason or a default message.
            self.failures_dict[item_identifier] = (
                failure_info if failure_info else "Unknown failure"
            )

def main():
    # Set up root logger configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    """Main function."""
    # Create a singleton instance
    metrics_tracker = MetricsTrackerSingleton()
    
    # Start processing
    metrics_tracker.start(object_name="file", total_to_process=10)
    
    # Simulate processing
    for i in range(10):
        time.sleep(0.1)
        if i % 3 == 0:
            metrics_tracker.increment_error(item_identifier=f"file_{i}")
        elif i % 4 == 0:
            metrics_tracker.increment_failed(item_identifier=f"file_{i}", failure_info="File not found")
        else:
            metrics_tracker.increment_processed()
    
    # End processing
    metrics_tracker.end()

if __name__ == '__main__':
    main()
