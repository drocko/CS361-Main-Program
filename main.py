import zmq
import time
import os
import requests
from datetime import datetime


class WaterIntakeTracker:
    """
    Represents Water Tracker Object
    """
    def __init__(self):
        self.daily_intake_oz = 0.0
        self.history = []

        self.unit_list = {"oz": 64, "L": 1.89, "cups": 8}
        self.unit_preference = "oz"  # Default Unit

        # ZeroMQ client setup
        self.context = zmq.Context()
        self.socket_microservice_c = self.context.socket(zmq.REQ)
        self.socket_microservice_c.connect("tcp://localhost:5555")  # Connect to the Microservice C server

        self.socket_microservice_d = self.context.socket(zmq.REQ)
        self.socket_microservice_d.connect("tcp://localhost:4444")  # Connect to the Microservice D server

    def fetch_microservice_b_quote(self):
        percent_real = self.get_percentage_progress()

        if percent_real <= 25:
            percent_approximate = "0%"
        elif percent_real <= 75:
            percent_approximate = "50%"
        else:
            percent_approximate = "100%"

        # Make a request to the microservice
        response = requests.get(
            "http://localhost:5000/api/quote",
            params={"user_id": 1, "progress_level": percent_approximate}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"QUOTE OF THE DAY: {data['quote']}\n")
        else:
            print(f"Error: {response.status_code}, {response.text}")

    def fetch_microservice_c_sheet_data(self): #
        """Requests and returns data from the Google Sheets via microservice C."""
        try:
            # Request to read entries from Google Sheets
            request_data = {
                "action": "read",  # Action to read from Google Sheets
                "data": {}
            }
            self.socket_microservice_c.send_json(request_data)  # Send request to microservice C
            response = self.socket_microservice_c.recv_json()  # Receive the response

            if response.get("status") == "success":
                return response["data"]  # Return the data from Google Sheets
            else:
                print(f"Error: {response.get('message', 'Failed to fetch data')}")
                return None  # Return None in case of failure
        except Exception as e:
            print(f"Error retrieving Google Sheets data: {e}")
            return None  # Return None if an exception occurs

    def sync_with_server_microservice_c(self, timestamp, amount, unit):
        """Sync water log with the ZeroMQ server and Google Sheets"""
        try:
            data = {
                "action": "create",
                "data": {
                    "timestamp": timestamp,  # Include the full timestamp
                    "amount": amount,
                    "unit": unit
                }
            }
            self.socket_microservice_c.send_json(data)  # Send data to the server
            response = self.socket_microservice_c.recv_json()  # Get response from the server
            # print(f"Server Response: {response}")
        except Exception as e:
            print(f"Failed to sync with server: {e}")

    def fetch_microservice_d_total(self):
        """
        Fetches a summary of total hydration converted to the specified unit (oz, L, cups)
        """
        try:
            # Send a request to Microservice D to calculate hydration total
            sheet_json = self.fetch_microservice_c_sheet_data()
            target_unit = self.get_unit_preference()
            request_data = {
                "action": "calculate",  # 'calculate' action to request a total hydration calculation
                "data": sheet_json,  # The sheet data (list of records)
                "unit": target_unit  # The target unit (oz, L, cups)
            }
            self.socket_microservice_d.send_json(request_data)

            # Receive the response from Microservice D
            response = self.socket_microservice_d.recv_json()

            if response["status"] == "success":
                total = response["total"]
                unit = target_unit
                # print(f"Total hydration: {total:.2f} {unit}")
                return {"total": total, "unit": unit}
            else:
                print(f"Error fetching hydration total: {response['message']}")
                return None

        except Exception as e:
            print(f"Failed to fetch hydration summary: {e}")
            return None

    def fetch_microservice_d_logs(self):
        """
        Fetches hydration logs from Microservice D
        """
        try:
            # Request to fetch hydration records from the microservice
            sheet_json = self.fetch_microservice_c_sheet_data()
            request_data = {
                "action": "get_records",  # Action to get the records
                "data": sheet_json
            }
            self.socket_microservice_d.send_json(request_data)

            # Receive the response from Microservice D
            response = self.socket_microservice_d.recv_json()

            if response["status"] == "success":
                logs = response["records"]
                return logs  # Return the list of hydration logs
            else:
                print(f"Error fetching hydration logs: {response['message']}")
                return None

        except Exception as e:
            print(f"Failed to fetch hydration logs: {e}")
            return None

    def get_unit_preference(self):
        """Returns the current unit preference."""
        return self.unit_preference

    def get_unit_list(self):
        """Returns list of available units"""
        return self.unit_list

    def set_unit_preference(self, unit):
        """Sets the unit preference for display."""
        if unit in self.unit_list.keys():
            self.unit_preference = unit
            print(f"Unit preference set to {unit}.")
        else:
            print("Invalid unit preference. Please choose from 'oz', 'L', or 'cups'.")

    def get_progress(self):
        """Get basic progress based on units"""
        total, unit = self.get_total()
        goal = self.unit_list.get(unit, 64)  # Default goal to 64 if not found

        progress = f"{total:.2f} {unit} / {goal} {unit}"
        return progress

    def get_percentage_progress(self):
        """Returns the percentage of the daily hydration goal achieved"""
        total, unit = self.get_total()
        goal = self.unit_list.get(unit, 64)  # Default goal to 64 if not found
        progress_percentage = (total / goal) * 100
        return progress_percentage

    def get_total(self):
        """Returns tuple of total amount and its unit."""
        total_dict = self.fetch_microservice_d_total()
        return total_dict["total"], total_dict["unit"]

    def display_total(self):
        """Prints total hydration and unit"""
        total, unit = self.get_total()
        percentage = self.get_percentage_progress()
        print(f"Total Hydration ({percentage:.0f}%): {total} {unit}")

    def display_logs(self):
        """
        Displays a hydration logs
        """
        try:
            # Get the hydration logs from Microservice D
            logs = self.fetch_microservice_d_logs()
            if logs:
                for log in logs:
                    timestamp = log.get("Timestamp")
                    amount = log.get("Amount")
                    unit = log.get("Unit")
                    print(f"> Timestamp: {timestamp}, Amount: {amount} {unit}")
            else:
                print("No hydration logs available.")

        except Exception as e:
            print(f"Error displaying summary: {e}")

    def add_water_log(self, amount, unit=1):
        """
        Logs the specified amount of water in liters to the daily intake.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Full timestamp (date + time)
        try:
            self.history.append((timestamp, amount, unit))  # Keep track of what was added
            self.sync_with_server_microservice_c(timestamp, amount, unit)
            total, unit = self.get_total()
            print(f"Added {amount} unit(s). Current total: {total:.2f} {unit}.")
        except ValueError:
            print("Please try again. Invalid number or unit.")
            # time.sleep(1)

    def undo_last_log(self):
        """
        Undo the last water log entry by asking Microservice C to delete the last entry from the sheet.
        """
        try:
            # Send request to Microservice C to delete the last entry
            request_data = {
                "action": "undo",  # 'undo' action to request last entry deletion
                "data": {}
            }
            self.socket_microservice_c.send_json(request_data)

            # Receive response from Microservice C
            response = self.socket_microservice_c.recv_json()

            if response["status"] == "success":
                # Extract the data of the removed entry from the response
                removed_data = response.get("data", None)
                if removed_data:
                    print(f"Undo last entry. Removed data: {removed_data}")
                else:
                    print("No data was removed.")
            else:
                print(f"Failed to undo: {response.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"Error during undo: {e}")

        time.sleep(2)

    def reset_intake(self):
        """
        Sends a reset command to the server to reset all data in the Google Sheet.
        """
        try:
            # Send 'reset' action request to the server
            request_data = {
                "action": "reset",
                "data": {}
            }
            self.socket_microservice_c.send_json(request_data)  # Send the reset request

            # Wait for the server's response
            response = self.socket_microservice_c.recv_json()

            if response["status"] == "success":
                print("All data has been reset in the Google Sheet.")
                # Reset local data in the tracker
                self.daily_intake_oz = 0.0
                self.history.clear()
                print("Local data has also been reset.")
            else:
                print(f"Error resetting data: {response['message']}")
        except Exception as e:
            print(f"Failed to reset data: {e}")

    def get_intake_oz(self):
        """
        Gets value of daily intake
        """
        return self.daily_intake_oz


def splash():
    water_bottle_art = r"""
            _________
           |_-_-_-_-_|
           |_________|
            )_______(
           (_________)
           |Derick Do|
           /         \
          /           \
         /             \
        /               \
       /                 \
      /                   \
     (_____________________)
      )___________________(
     (_____________________)
     |                     |
     |Track Daily Hydration|
     |                     |
      )___________________(
     |_____________________|
      )___________________(
     |                     |
     |                     |
     \_____________________/
    """
    print(water_bottle_art)
    print('Keep yourself hydrated!')
    print('...')
    time.sleep(4)
    clear_screen()


def clear_screen():
    if os.name == 'nt':  # For Windows
        os.system('cls')
    else:  # For MacOS and Linux
        os.system('clear')


def main():
    tracker = WaterIntakeTracker()
    while True:
        clear_screen()
        print(f"Main Screen: {tracker.get_progress()}\n")
        print(f"Water Hydration Tracker - Choose an option:")

        options_main = [
            "1. Add Water",
            "2. View Summary",
            "3. Undo Last Water Log",
            "4. Reset Water Logs",
            "5. Change Unit Preference",
            "0. Exit"]
        print(*options_main, sep="\n")

        choice_main = int(input("\nEnter your choice (1-5): "))

        # CHOICE: ADD WATER
        if choice_main == 1:
            clear_screen()
            # STEP 1: SELECT UNIT
            print(f"Add Water Screen\n")
            print(f"Water Hydration Tracker - Select a unit:")

            options_unit = [
                "1. Ounces (oz)",
                "2. Liters (L)",
                "3. Cups (c)",
                "0. Cancel"]
            print(*options_unit, sep="\n")

            choice_unit = int(input("Enter your choice: "))

            if choice_unit == 0:
                continue  # Return to main menu if canceled

            clear_screen()

            # STEP 2: INPUT AMOUNT
            print(f"Add Water Screen\n")
            print(f"Water Hydration Tracker - Enter an amount (0. Cancel):")

            # STEP 3: SEE RESULT
            try:
                amount = float(input("\nEnter amount: "))
                if amount == 0:
                    continue  # Return to main menu if canceled
                clear_screen()

                print(f"Add Water Screen\n")
                print(f"Water Hydration Tracker - Nice!\n")

                tracker.add_water_log(amount, choice_unit)
                percentage = tracker.get_percentage_progress()
                print(f"You're at about {percentage:.0f}%...")
                tracker.fetch_microservice_b_quote()

                #STEP 4: EXIT
                choice_unit = int(input("Enter 0 to return to main menu: "))

                if choice_unit == 0:
                    continue  # Return to main menu if canceled

            except ValueError:
                print("Please enter a valid amount.")
                time.sleep(2)

        # CHOICE: VIEW SUMMARY
        elif choice_main == 2:
            while True:
                clear_screen()
                # STEP 1: DISPLAY SCREEN
                print(f"Hydration Summary Screen\n")
                tracker.display_total()
                tracker.display_logs()

                back_choice = input("\nEnter 0 to return to main menu: ")
                # STEP 2: EXIT
                if back_choice == '0':
                    break

        # CHOICE: UNDO LAST WATER LOG
        elif choice_main == 3:
            clear_screen()
            # STEP 1: WARNING
            print(f"Undo Last Entry Pop-up Screen\n")
            print(f"All actions cannot be undone and will permanently change your current progress.")
            print(f"Do you wish to proceed?")
            options_unit = ["1. Yes", "2. No"]
            print(*options_unit, sep="\n")

            choice_reset = input("Enter your choice: ")
            # STEP 2: EXECUTE/PASS
            if choice_reset == '1':
                tracker.undo_last_log()
                # STEP 3: EXIT
                choice_unit = int(input("Enter 0 to return to main menu: "))

                if choice_unit == 0:
                    continue  # Return to main menu if canceled
            else:  # Cancel
                print("Canceled undo.")
                time.sleep(1)

        # CHOICE: RESET WATER LOGS
        elif choice_main == 4:
            clear_screen()
            # STEP 1: WARNING
            print(f"Reset Water Pop-up Screen\n")
            print(f"All actions cannot be undone and will permanently change your current progress.")
            print(f"Do you wish to proceed?")
            options_unit = ["1. Yes", "2. No"]
            print(*options_unit, sep="\n")

            choice_reset = input("Enter your choice: ")
            # STEP 2: EXECUTE/PASS
            if choice_reset == '1':
                tracker.reset_intake()
                time.sleep(2)
            else:  # Cancel
                print("Canceled reset.")
                time.sleep(1)

        # CHOICE: CHANGE UNIT PREFERENCE
        elif choice_main == 5:
            clear_screen()
            # STEP 1: SELECT UNIT
            print(f"Change Unit Preference Screen\n")
            print(f"Water Hydration Tracker - Select a unit:")
            options_unit = ["1. Ounces (oz)", "2. Liters (L)", "3. Cups (c)", "0. Cancel"]
            print(*options_unit, sep="\n")
            choice_unit = int(input("Enter your choice: "))
            if choice_unit == 0:
                continue  # Return to main menu if canceled

            if choice_unit == 1:
                tracker.set_unit_preference("oz")
            elif choice_unit == 2:
                tracker.set_unit_preference("L")
            elif choice_unit == 3:
                tracker.set_unit_preference("cups")
            else:
                print("Invalid option, please try again.")

        # CHOICE: EXIT
        elif choice_main == 0:
            print("Exiting Water Hydration Tracker. Stay hydrated!")
            break
        else:
            print("Invalid option. Please choose again.")


if __name__ == "__main__":
    splash()
    main()
