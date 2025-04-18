from modules.data_loader import load_data
from modules.data_preprocessor import preprocess_data
from modules.model_trainer import train_model
from modules.model_predictor import load_model, predict
from modules.realtime_data_feeder import RealTimeDataFeeder

import os
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = os.getenv('DATA_PATH')
MODEL_PATH = os.getenv('MODEL_PATH')

# Load and preprocess data
data = load_data(DATA_PATH)
processed_data, X, y, scaler = preprocess_data(data)

# Initialize data feeder
feeder = RealTimeDataFeeder(processed_data, retrain_frequency='daily')

model_path = MODEL_PATH

# Train and save initial model
model = train_model(X, y, model_path)

# Simulate real-time predictions
while feeder.has_next():
    date, next_day_data = feeder.get_next_day()
    prediction = predict(model, next_day_data)
    print(f"Date: {date} | Prediction: {prediction}")

    # Retrain model based on configured frequency
    if feeder.should_retrain():
        model = train_model(X, y, model_path)
        print(f"Model retrained at {date}")