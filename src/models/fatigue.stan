data {
    int<lower=0> N;                 
    array[N] int<lower=0,upper=1> Y_lexical; 
    vector[N] text_position;        
    array[N] int<lower=1> pericope; 
    int<lower=1> J;                 
}
parameters {
    real alpha;                     // intercept
    real beta;                      // fatigue parameter (slope)
    vector[J] u;                    // pericope random effects
    real<lower=0> sigma_u;
}
model {
    alpha ~ normal(0, 1.5);
    beta ~ normal(0, 1.5);
    sigma_u ~ exponential(1);
    u ~ normal(0, sigma_u);

    // Logistic regression: log-odds of verbatim copying
    for (n in 1:N) {
        Y_lexical[n] ~ bernoulli_logit(alpha + beta * text_position[n] + u[pericope[n]]);
    }
}
