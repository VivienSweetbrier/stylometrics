# ==============================================================================
# Bayesian Inference Node (rstanarm)
# Purpose: Tests for "Performance Fatigue" within a single Latent Bard
# ==============================================================================

# Load necessary libraries (using rstanarm to skip local C++ compilation)
suppressPackageStartupMessages(library(rstanarm))
suppressPackageStartupMessages(library(jsonlite))

# 1. Load the DAG data exported from Python
cat("Loading sequential data for Bard_1...\n")
raw_data <- fromJSON("../../data/processed/stan_homer_fatigue.json")

# Convert to an R DataFrame
df <- data.frame(
  Y_formulaic = raw_data$Y_formulaic,
  text_position = as.numeric(raw_data$position_index),
  book = as.factor(raw_data$book)
)

# 2. Run the Bayesian Logistic Regression
# Hypothesis: As `text_position` increases, the Bard fatigues and relies more 
# heavily on highly-repeated stock formulas (Y_formulaic = 1).
cat("Compiling Hamiltonian Monte Carlo (HMC) chains...\n")
fit <- stan_glm(
  formula = Y_formulaic ~ text_position,
  data = df,
  family = binomial(link = "logit"),
  seed = 123,
  chains = 2,
  iter = 2000,
  cores = 1,
  refresh = 0 # Suppress spammy HMC sampling output
)

# 3. Output the Results
cat("\n=== BAYESIAN FATIGUE RESULTS ===\n")
print(summary(fit, digits = 4))

# 4. Save the model for further investigation
saveRDS(fit, "../../data/processed/homer_fatigue_model.rds")
cat("\nSuccess! Bayesian model saved to data/processed/homer_fatigue_model.rds\n")
