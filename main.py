import time
import os


class WaterIntakeTracker:
    """
    Represents Water Tracker Object
    """
    # TODO: Implement Data Log/Entry object
    def __init__(self):
        self.daily_intake_oz = 0.0
        self.history = []

    def add_water_log(self, amount, unit=1):
        """
        Logs the specified amount of water in liters to the daily intake.
        """
        try:
            if amount < 0:
                raise ValueError
            if unit == 1:  # Ounces
                self.daily_intake_oz += amount
            elif unit == 2:  # Liters
                self.daily_intake_oz += amount * 33.814  # Convert liters to ounces
            elif unit == 3:  # Cups
                self.daily_intake_oz += amount * 8  # Convert cups to ounces
            self.history.append((amount, unit))  # Keep track of what was added
            print(f"Added {amount} unit(s). Current total: {self.daily_intake_oz} oz.")
            print("Awesome!")
        except ValueError:
            print("Please try again. Invalid number or unit.")
            time.sleep(2)

    def undo_last_log(self):
        """
        Undo the last water log entry and removes from history
        """
        # TODO: IMPLEMENT UNIT CONVERSION MICROSERVICE TO SIMPLIFY MATH
        if self.history:
            last_amount, last_unit = self.history.pop()
            if last_unit == 1:  # Ounces
                self.daily_intake_oz -= last_amount
            elif last_unit == 2:  # Liters
                self.daily_intake_oz -= last_amount * 33.814  # Convert liters to ounces
            elif last_unit == 3:  # Cups
                self.daily_intake_oz -= last_amount * 8  # Convert cups to ounces
            print(f"Undo the last entry. New total: {self.daily_intake_oz} oz.")
        else:
            print(f"No actions to undo.")
        time.sleep(2)

    def view_summary(self):
        """
        Displays a hydration summary
        """
        cups = self.daily_intake_oz / 8
        percent_hydration = (cups / 8) * 100

        options_main = [f"{percent_hydration:.2f}% daily hydration", f"{self.daily_intake_oz:.2f}(oz) / 64oz", f"{cups:.2f}(cups) / 8 cups"]
        print(f"Here is your water hydration summary:")
        print(*options_main, sep="\n")



    def reset_intake(self):
        """
        Resets the daily water intake
        """
        self.daily_intake_oz = 0.0
        print("All water records have been reset. Returning to main screen")

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
    print('...')
    time.sleep(.5)
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
        print(f"Main Screen: {tracker.get_intake_oz()/8:.2f} cups / 8 cups.\n")
        print(f"Water Hydration Tracker - Choose an option:")
        options_main = ["1. Add Water", "2. View Summary", "3. Undo Last Water Log", "4. Reset Water Logs", "0. Exit"]
        print(*options_main, sep="\n")
        choice_main = input("Enter your choice (1-4): ")

        # CHOICE: ADD WATER
        if choice_main == '1':
            clear_screen()
            print(f"Add Water Screen\n")
            print(f"Water Hydration Tracker - Select a unit:")
            options_unit = ["1. Ounces (oz)", "2. Liters (L)", "3. Cups (c)", "0. Cancel"]
            print(*options_unit, sep="\n")
            choice_unit = int(input("Enter your choice: "))
            if choice_unit == 0:
                continue  # Return to main menu if canceled
            clear_screen()
            print(f"Add Water Screen\n")
            print(f"Water Hydration Tracker - Enter an amount (0. Cancel):")
            try:
                amount = float(input("Enter amount: "))
                if amount == 0:
                    continue  # Return to main menu if canceled
                tracker.add_water_log(amount, choice_unit)
                time.sleep(2)
            except ValueError:
                print("Please enter a valid amount.")
                time.sleep(2)

        # CHOICE: VIEW SUMMARY
        elif choice_main == '2':
            while True:
                clear_screen()
                print(f"Hydration Summary Screen\n")
                tracker.view_summary()

                print("\nPress 0 to go back to the main menu.")
                back_choice = input("Enter your choice: ")
                if back_choice == '0':
                    break
        # CHOICE: UNDO LAST WATER LOG
        elif choice_main == '3':
            clear_screen()
            # Display undo warning popup
            print(f"Undo Water Pop-up Screen\n")
            print(f"Undoes the last water log entry. \n"
                  f"All actions cannot be undone and will permanently change your current progress.")
            print(f"Do you wish to proceed?")
            options_unit = ["1. Yes", "2. No"]
            print(*options_unit, sep="\n")
            # Receive input
            choice_reset = input("Enter your choice: ")
            if choice_reset == '1':  # Undo Last Water Log
                tracker.undo_last_log()
                time.sleep(2)
            else:  # Cancel
                print("Canceled undo.")
                time.sleep(2)
        # CHOICE: RESET WATER LOGS
        elif choice_main == '4':
            clear_screen()
            # Display reset warning popup
            print(f"Reset Water Pop-up Screen\n")
            print(f"All actions cannot be undone and will permanently change your current progress.")
            print(f"Do you wish to proceed?")
            options_unit = ["1. Yes", "2. No"]
            print(*options_unit, sep="\n")
            # Receive input
            choice_reset = input("Enter your choice: ")
            if choice_reset == '1':  # Reset Water Logs
                tracker.reset_intake()
                time.sleep(2)
            else:  # Cancel
                print("Canceled reset.")
                time.sleep(2)
        # CHOICE: EXIT
        elif choice_main == '0':
            print("Exiting Water Hydration Tracker. Stay hydrated!")
            break

        else:
            print("Invalid option. Please choose again.")



if __name__ == "__main__":
    splash()
    main()
