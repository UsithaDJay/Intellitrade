from sklearn.ensemble import RandomForestClassifier
import joblib


def train_model(X_train, y_train, model_path):
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    joblib.dump(model, model_path)
    return model