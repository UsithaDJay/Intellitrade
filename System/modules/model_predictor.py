import joblib


def load_model(model_path):
    return joblib.load(model_path)


def predict(model, input_data):
    prediction = model.predict(input_data)
    return prediction[0]