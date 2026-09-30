import os
from sentence_transformers import SentenceTransformer

def download_and_save_model():
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "models", model_name)
    
    print(f"Downloading {model_name} to {model_dir}")
    os.makedirs(model_dir, exist_ok=True)
    
    # This downloads and loads the model from HF
    model = SentenceTransformer(model_name)
    
    # Save it locally so it can be loaded offline
    model.save(model_dir)
    print("Download complete and saved to local directory.")

if __name__ == "__main__":
    download_and_save_model()
