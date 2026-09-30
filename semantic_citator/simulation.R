library(SimDesign)
library(ReplicationSuccess)
library(rstream)

Design <- createDesign(
  semantic_drift_mu = c(0.0, 0.5, 1.2),
  causal_edit_dist = c(0, 1, 3),
  variance_ratio_c = c(0.5, 1.0, 2.5),
  formal_logic_flag = c(0, 1),
  sample_size = c(500, 2000)
)

Generate <- function(condition, fixed_objects = NULL) {
  stream <- new("rstream.mrg32k3a")
  
  N <- condition$sample_size
  c_ratio <- condition$variance_ratio_c
  
  se_o <- rstream.sample(stream, N) * 0.5 + 0.1
  z_o <- rnorm(N, mean = 2.5, sd = 1) 
  
  degradation_factor <- (condition$semantic_drift_mu + condition$causal_edit_dist) / 4
  true_zr_mean <- 2.5 * (1 - degradation_factor)
  
  se_r <- se_o / sqrt(c_ratio)
  
  if (condition$formal_logic_flag == 1) {
    true_zr_mean <- -1.0 
  }
  
  z_r <- rnorm(N, mean = true_zr_mean, sd = 1)
  
  is_valid_usage <- ifelse(degradation_factor < 0.5 & condition$formal_logic_flag == 0, 1, 0)
  
  dat <- data.frame(
    z_o = z_o,
    z_r = z_r,
    se_o = se_o,
    se_r = se_r,
    c = c_ratio,
    true_valid = is_valid_usage
  )
  return(dat)
}

Analyze <- function(condition, dat, fixed_objects = NULL) {
  p_sceptical <- pSceptical(
    zo = dat$z_o, 
    zr = dat$z_r, 
    c = dat$c, 
    alternative = "one.sided",
    type = "golden"
  )
  
  predicted_misuse <- ifelse(p_sceptical >= 0.025, 1, 0)
  true_misuse <- ifelse(dat$true_valid == 1, 0, 1)
  
  true_positives <- sum(predicted_misuse == 1 & true_misuse == 1)
  false_positives <- sum(predicted_misuse == 1 & true_misuse == 0)
  true_negatives <- sum(predicted_misuse == 0 & true_misuse == 0)
  false_negatives <- sum(predicted_misuse == 0 & true_misuse == 1)
  
  power <- true_positives / (true_positives + false_negatives)
  type_I_error <- false_positives / (false_positives + true_negatives)
  
  ret <- c(
    power = power,
    type_I_error = type_I_error,
    mean_p_sceptical = mean(p_sceptical, na.rm = TRUE)
  )
  return(ret)
}

Summarize <- function(condition, results, fixed_objects = NULL) {
  ret <- c(
    Power = mean(results[, 'power'], na.rm = TRUE),
    Type_I_Error_Rate = mean(results[, 'type_I_error'], na.rm = TRUE),
    Mean_p_Sceptical = mean(results[, 'mean_p_sceptical'], na.rm = TRUE)
  )
  return(ret)
}

res <- runSimulation(
  design = Design, 
  replications = 1000, 
  generate = Generate, 
  analyze = Analyze, 
  summarize = Summarize, 
  parallel = TRUE,
  packages = c("ReplicationSuccess", "rstream")
)

print(res)
