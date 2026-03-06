# Import the tools we need
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import pickle

print("Starting the training process...")

# --- Step 1: Load Your Data ---
# We tell pandas to read your CSV files.
try:
    train_df = pd.read_csv('Training.csv')
    test_df = pd.read_csv('Testing.csv')
    print("Successfully loaded Training.csv and Testing.csv!")
except FileNotFoundError:
    print("Error: Make sure 'Training.csv' and 'Testing.csv' are in the same folder!")
    exit()

# --- Step 2: Prepare The Data ---
# The 'prognosis' column (the disease) is what we want to predict.
# The other columns (symptoms) are the clues.
X_train = train_df.drop('prognosis', axis=1) # All columns EXCEPT prognosis
y_train = train_df['prognosis']             # ONLY the prognosis column

# --- Step 3: Teach the Model ---
# We use a Decision Tree, which is like a flowchart for making decisions.
# It learns the patterns between symptoms and diseases.
model = DecisionTreeClassifier(random_state=42)
model.fit(X_train.values, y_train) # The .values is important here!
print("Model has been trained!")

# --- Step 4: Save the "Brain" ---
# We save our trained model so the website can use it later.
# 'wb' means 'write binary', which is how we save model files.
with open('disease_model.pkl', 'wb') as model_file:
    pickle.dump(model, model_file)
print("Trained model saved as 'disease_model.pkl'")

# We also need to save the list of symptoms in the exact order the model expects them.
symptoms = X_train.columns.tolist()
with open('symptoms_list.pkl', 'wb') as symptoms_file:
    pickle.dump(symptoms, symptoms_file)
print("Symptom list saved as 'symptoms_list.pkl'")

print("\nAll done! The 'brain' is ready. You can now create the website file.")
