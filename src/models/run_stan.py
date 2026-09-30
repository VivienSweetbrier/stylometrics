import os
import json
from pathlib import Path

try:
    from cmdstanpy import CmdStanModel
except ImportError:
    print("cmdstanpy is not installed in this Python environment.")
    print("Please run the Quarto notebook in RStudio (using cmdstanr), or install cmdstanpy to run from terminal.")
    exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAN_FILE = BASE_DIR / "src" / "models" / "fatigue.stan"
DATA_FILE = BASE_DIR / "data" / "processed" / "stan_fatigue_data.json"

def run_mcmc():
    print(f"Compiling Stan model: {STAN_FILE}")
    try:
        model = CmdStanModel(stan_file=str(STAN_FILE))
    except Exception as e:
        print(f"Failed to compile Stan model. Is CmdStan installed? Error: {e}")
        return

    print("Starting Hamiltonian Monte Carlo (HMC) sampling...")
    fit = model.sample(data=str(DATA_FILE), 
                       iter_warmup=1000, 
                       iter_sampling=2000, 
                       chains=4, 
                       show_progress=False)
    
    print("\nSampling completed successfully!")
    print(fit.summary())

if __name__ == "__main__":
    run_mcmc()
