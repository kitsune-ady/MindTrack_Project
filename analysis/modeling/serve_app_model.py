"""Local HTTP prediction service for the MindTrack Android lecturer demo."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "best_compact_app_ready_depression_model.joblib"
HOST = "0.0.0.0"
PORT = 8765
FIELDS = [
    "Department", "SES", "Living_Arrangement", "Residence_Area", "Areas_Use",
    "Type_MD", "Phone_Related_Arguments", "Time_First_Cellphone",
    "TMD_Total_Recomputed", "Using_social media_Apps",
    "Using_Ttime-management_Apps",
]
APP_FLAGS = ["Using_social media_Apps", "Using_Ttime-management_Apps"]
MODEL = None


class AppFieldSelector(BaseEstimator, TransformerMixin):
    """Compatibility class for the selector embedded in the saved joblib model.

    The model was serialized while this class lived in the training script's
    __main__ module. Defining the same class name here lets joblib resolve that
    older artifact. Its fitted preprocessing and selected fields are restored
    from the model file; prediction uses those saved attributes.
    """
    def transform(self, X):
        missing = [field for field in self.selected_fields_ if field not in X.columns]
        if missing:
            raise ValueError(f"Missing selected app fields at prediction time: {missing}")
        return self.preprocessor_.transform(X[self.selected_fields_])

    def get_feature_names_out(self, input_features=None):
        return self.encoded_feature_names_


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == "/health":
            self.respond(200, {"status": "ready"})
        else:
            self.respond(404, {"error": "Endpoint not found"})

    def do_POST(self):
        if self.path != "/predict":
            self.respond(404, {"error": "Endpoint not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 200_000:
                raise ValueError("Request body is missing or too large")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            missing = [field for field in FIELDS if field not in payload]
            extra = [field for field in payload if field not in FIELDS]
            if missing or extra:
                raise ValueError(f"Expected the compact model fields; missing={missing}, extra={extra}")
            row = {field: payload[field] for field in FIELDS}
            for field in FIELDS:
                if isinstance(row[field], bool):
                    raise ValueError(f"{field} must be a numeric code, not true/false")
                row[field] = float(row[field])
            if not 0 <= row["TMD_Total_Recomputed"] <= 88:
                raise ValueError("TMD total must be between 0 and 88")
            for field in APP_FLAGS:
                if row[field] not in (1, 2):
                    raise ValueError(f"{field} must be 1 (No) or 2 (Yes)")
                row[field] = {1: 0, 2: 1}[int(row[field])]
            prediction = int(MODEL.predict(pd.DataFrame([row]))[0])
            label = "Estimated Beck score below 11" if prediction == 0 else "Estimated Beck score 11 or higher"
            self.respond(200, {
                "predicted_class": prediction,
                "label": label,
                "notice": "Research estimate from questionnaire data; not a clinical diagnosis.",
            })
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self.respond(400, {"error": str(error)})
        except Exception:
            self.respond(500, {"error": "The model could not produce a result"})

    def log_message(self, format, *args):
        # Avoid writing participant answers to the terminal log.
        if self.path != "/predict":
            super().log_message(format, *args)


def main():
    global MODEL
    if not MODEL_PATH.exists():
        raise SystemExit(f"Compact model not found: {MODEL_PATH}. Run run_app_ready_models.py first.")
    MODEL = joblib.load(MODEL_PATH)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"MindTrack demo model ready on http://{HOST}:{PORT}")
    print("POST /predict; GET /health. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping prediction service")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
