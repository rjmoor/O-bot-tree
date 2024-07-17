import time
from control_system import ControlSystem
import logging
from backend.utils.utility import configure_logging

configure_logging("upload_data")

def update_data():
    control_system = ControlSystem()
    while True:
        try:
            instruments = control_system.get_instruments()
            for instrument in instruments:
                control_system.update_tables(instrument, 'D')
                control_system.update_tables(instrument, 'M')
                control_system.update_tables(instrument, 'M1')
            logging.info("Data updated successfully.")
        except Exception as e:
            logging.error(f"Error updating data: {e}")
        time.sleep(3600)  # Update data every hour

if __name__ == "__main__":
    update_data()
