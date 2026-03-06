# Import Flask for the website and other tools
from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import google.generativeai as genai
import os

# --- Configure the Gemini API ---
# Get API key from environment variable for better security
try:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        # Fallback to hardcoded key (not recommended for production)
        api_key = "Your_Api_Key"
    
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini API configured successfully!")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    gemini_model = None

# Create the web application
app = Flask(__name__)

# --- Load the "Brain" and other saved files ---
model = pickle.load(open('disease_model.pkl', 'rb'))
symptoms_list = pickle.load(open('symptoms_list.pkl', 'rb'))

# --- Define a dictionary for precautions (the cures) ---
disease_precautions = {
    'Fungal infection': ['Bathe regularly', 'Use anti-fungal shampoo', 'Wear loose-fitting clothes'],
    'Allergy': ['Avoid allergens', 'Use air purifiers', 'Consult an allergist'],
    'GERD': ['Avoid spicy and fatty foods', 'Do not lie down after eating', 'Elevate head while sleeping'],
    'Drug Reaction': ['Stop taking the suspected drug', 'Consult your doctor immediately', 'Take antihistamines'],
    'Jaundice': ['Rest', 'Stay hydrated', 'Follow a healthy diet', 'Avoid alcohol'],
    'Malaria': ['Take anti-malarial drugs', 'Use mosquito nets', 'Seek medical help'],
    'Chicken pox': ['Keep skin clean', 'Use calamine lotion', 'Avoid scratching'],
    'Dengue': ['Rest and stay hydrated', 'Take fever reducers', 'Monitor for warning signs'],
    'Typhoid': ['Get vaccinated', 'Drink clean water', 'Take antibiotics'],
    'hepatitis A': ['Get vaccinated', 'Practice good hygiene', 'Rest and recover'],
    'Hepatitis B': ['Get vaccinated', 'Practice safe sex', 'Do not share needles'],
    'Hepatitis C': ['Avoid sharing needles', 'Take antiviral medications', 'Get regular liver check-ups'],
    'Hepatitis D': ['Get Hepatitis B vaccine', 'Avoid risk factors', 'Follow medical advice'],
    'Hepatitis E': ['Drink safe water', 'Cook food thoroughly', 'Practice good hygiene'],
    'Alcoholic hepatitis': ['Stop drinking alcohol', 'Follow a nutritious diet', 'Seek counseling'],
    'Tuberculosis': ['Take antibiotics for the full course', 'Cover mouth when coughing', 'Ensure good ventilation'],
    'Common Cold': ['Rest', 'Drink plenty of fluids', 'Use over-the-counter remedies'],
    'Pneumonia': ['Take antibiotics as prescribed', 'Rest and drink fluids', 'Get vaccinated'],
    'Dimorphic hemmorhoids(piles)': ['Eat a high-fiber diet', 'Drink plenty of water', 'Avoid straining'],
    'Heart attack': ['Call emergency services immediately', 'Chew aspirin if recommended', 'Rest'],
    'Varicose veins': ['Elevate legs', 'Wear compression stockings', 'Exercise regularly'],
    'Hypothyroidism': ['Take thyroid hormone medication', 'Get regular blood tests', 'Maintain a healthy diet'],
    'Hyperthyroidism': ['Take antithyroid medications', 'Manage symptoms', 'Get regular check-ups'],
    'Hypoglycemia': ['Consume fast-acting carbs', 'Monitor blood sugar', 'Eat regular meals'],
    'Osteoarthristis': ['Stay active', 'Maintain a healthy weight', 'Use pain relief medication'],
    'Arthritis': ['Engage in joint-friendly exercises', 'Manage weight', 'Use hot and cold therapy'],
    '(vertigo) Paroymsal  Positional Vertigo': ['Perform canalith repositioning procedures', 'Avoid sudden head movements', 'Sit down during dizzy spells'],
    'Acne': ['Keep skin clean', 'Use non-comedogenic products', 'Consult a dermatologist'],
    'Urinary tract infection': ['Drink plenty of water', 'Take antibiotics as prescribed', 'Wipe from front to back'],
    'Psoriasis': ['Moisturize skin regularly', 'Avoid triggers', 'Use prescribed treatments'],
    'Impetigo': ['Keep sores clean and covered', 'Take antibiotics as prescribed', 'Wash hands frequently'],
}

# --- Define the main page of the website ---
@app.route('/')
def home():
    formatted_symptoms = [s.replace('_', ' ').title() for s in symptoms_list]
    symptom_options = zip(symptoms_list, formatted_symptoms)
    return render_template('index.html', symptoms=symptom_options)

# --- Define the prediction page ---
@app.route('/predict', methods=['POST'])
def predict():
    selected_symptoms = request.form.getlist('symptoms')
    
    if not selected_symptoms:
        return jsonify({'error': 'Please select at least one symptom.'}), 400
    
    input_vector = np.zeros(len(symptoms_list))
    for symptom in selected_symptoms:
        if symptom in symptoms_list:
            input_vector[symptoms_list.index(symptom)] = 1
    
    # Get prediction and probability scores
    prediction = model.predict([input_vector])[0]
    probabilities = model.predict_proba([input_vector])[0]
    
    # Get top 3 predictions with probabilities
    disease_classes = model.classes_
    top_indices = np.argsort(probabilities)[-3:][::-1]  # Top 3 in descending order
    
    top_predictions = []
    for idx in top_indices:
        disease = disease_classes[idx]
        probability = probabilities[idx] * 100
        if probability > 5:  # Only include if probability > 5%
            top_predictions.append({
                'disease': disease,
                'probability': round(probability, 1)
            })
    
    # Use the top prediction as main result
    main_prediction = prediction
    main_probability = round(probabilities[list(disease_classes).index(prediction)] * 100, 1)
    
    precautions = disease_precautions.get(main_prediction, ['Consult a doctor for advice.'])
    
    # Enhanced Gemini prompt with more comprehensive information
    description = "Could not retrieve information from the AI model. Please consult a doctor."
    if gemini_model:
        try:
            # Create a more detailed prompt
            symptoms_text = ", ".join([s.replace('_', ' ') for s in selected_symptoms])
            prompt = f"""
            Based on these symptoms: {symptoms_text}
            
            The AI model predicted: {main_prediction} with {main_probability}% confidence.
            
            Please provide:
            1. A brief, patient-friendly explanation of {main_prediction} (40-50 words)
            2. What type of specialist doctor should be consulted
            3. Urgency level (routine, urgent, or emergency)
            4. One key warning sign to watch for
            
            Keep the response clear, concise, and reassuring while being medically accurate.
            """
            response = gemini_model.generate_content(prompt)
            description = response.text
        except Exception as e:
            print(f"Gemini API call failed: {e}")
    
    # Determine risk level based on disease type and symptoms
    risk_level = calculate_risk_level(main_prediction, selected_symptoms)
    
    return jsonify({
        'disease': main_prediction,
        'confidence': main_probability,
        'alternative_predictions': top_predictions[1:] if len(top_predictions) > 1 else [],
        'precautions': precautions,
        'description': description,
        'risk_level': risk_level,
        'selected_symptoms': [s.replace('_', ' ').title() for s in selected_symptoms]
    })

def calculate_risk_level(disease, symptoms):
    """Calculate risk level based on disease and symptoms"""
    emergency_diseases = ['heart attack', 'stroke', 'drug reaction']
    high_risk_diseases = ['tuberculosis', 'hepatitis', 'pneumonia', 'malaria', 'dengue']
    moderate_risk_diseases = ['jaundice', 'typhoid', 'chicken pox']
    
    disease_lower = disease.lower()
    
    # Check for emergency symptoms
    emergency_symptoms = ['chest_pain', 'breathlessness', 'altered_sensorium', 'fast_heart_rate']
    has_emergency_symptoms = any(symptom in symptoms for symptom in emergency_symptoms)
    
    if any(ed in disease_lower for ed in emergency_diseases) or has_emergency_symptoms:
        return 'critical'
    elif any(hrd in disease_lower for hrd in high_risk_diseases):
        return 'high'
    elif any(mrd in disease_lower for mrd in moderate_risk_diseases):
        return 'moderate'
    else:
        return 'low'

# --- Run the application ---
if __name__ == '__main__':
    app.run(debug=True)
