# In your main_app.py or other module

import detector

# ... your code ...

print("Question: Do you want to proceed?")
user_answer = detector.get_input() # This line will pause and wait

if user_answer == "yes":
    print("User answered YES. Proceeding...")
    # ... code to run for 'yes' ...
elif user_answer == "no":
    print("User answered NO. Aborting...")
    # ... code to run for 'no' ...
else:
    print("No valid input was received.")

# ... rest of your code ...