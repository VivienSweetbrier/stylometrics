import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS

def quotation_misuse_model(
    doc_idx, 
    cosine_distance, 
    topological_edit_distance, 
    logical_contradiction, 
    structural_edit_count, 
    num_docs,
    y=None
):
    """
    Bayesian hierarchical logistic regression for quote misuse detection.
    Maps to the SynthesisNodeInput JSON schema.
    """
    # Hierarchical intercept for document or author-level baseline variance
    mu_alpha = numpyro.sample("mu_alpha", dist.Normal(0, 1.5))
    sigma_alpha = numpyro.sample("sigma_alpha", dist.HalfNormal(1.0))
    
    with numpyro.plate("docs", num_docs):
        alpha = numpyro.sample("alpha", dist.Normal(mu_alpha, sigma_alpha))

    # Parameter Priors
    beta_S = numpyro.sample("beta_S", dist.Normal(0, 1.0))
    beta_C = numpyro.sample("beta_C", dist.Normal(0, 1.0))
    # High prior mean for logical contradiction from SMT solver
    beta_F = numpyro.sample("beta_F", dist.Normal(2.5, 1.0))
    beta_E = numpyro.sample("beta_E", dist.Normal(0.5, 0.5))
    beta_SC = numpyro.sample("beta_SC", dist.Normal(0, 1.0))

    # Linear predictor with semantic-causal interaction term
    logit_p = (
        alpha[doc_idx] +
        beta_S * cosine_distance +
        beta_C * topological_edit_distance +
        beta_F * logical_contradiction +
        beta_E * structural_edit_count +
        beta_SC * (cosine_distance * topological_edit_distance)
    )

    # Likelihood function
    with numpyro.plate("data", len(cosine_distance)):
        numpyro.sample("obs", dist.Bernoulli(logits=logit_p), obs=y)

def parse_synthesis_payloads(json_payloads):
    """
    Extracts JSON arrays into JAX tensors and computes the variance ratio (c)
    for subsequent replication success evaluation.
    """
    N = len(json_payloads)
    
    cosine_distance = jnp.zeros(N)
    topological_edit_distance = jnp.zeros(N)
    logical_contradiction = jnp.zeros(N)
    structural_edit_count = jnp.zeros(N)
    variance_ratio_c = jnp.zeros(N)
    
    for i, payload in enumerate(json_payloads):
        sem = payload.get("semantic_evaluation") or {}
        caus = payload.get("causal_evaluation") or {}
        form = payload.get("formal_evaluation") or {}
        meta = payload.get("orchestrator_metadata") or {}
        
        cosine_distance = cosine_distance.at[i].set(sem.get("cosine_distance", 0.0))
        topological_edit_distance = topological_edit_distance.at[i].set(caus.get("topological_edit_distance", 0.0))
        logical_contradiction = logical_contradiction.at[i].set(float(form.get("logical_contradiction", False)))
        structural_edit_count = structural_edit_count.at[i].set(meta.get("structural_edit_count", 0))
        
        variance_ratio_c = variance_ratio_c.at[i].set(
            sem.get("destination_variance", 0.0) / (sem.get("source_variance", 0.0) + 1e-8)
        )
        
    return {
        "cosine_distance": cosine_distance,
        "topological_edit_distance": topological_edit_distance,
        "logical_contradiction": logical_contradiction,
        "structural_edit_count": structural_edit_count,
        "variance_ratio_c": variance_ratio_c
    }

def execute_inference(data_dict, num_docs, num_samples=2000, num_warmup=1000):
    """
    Executes Hamiltonian Monte Carlo sampling using NUTS.
    """
    nuts_kernel = NUTS(quotation_misuse_model)
    mcmc = MCMC(nuts_kernel, num_warmup=num_warmup, num_samples=num_samples, num_chains=4)
    
    mcmc.run(
        numpyro.prng_key(0),
        doc_idx=jnp.zeros(len(data_dict["cosine_distance"]), dtype=jnp.int32),
        cosine_distance=data_dict["cosine_distance"],
        topological_edit_distance=data_dict["topological_edit_distance"],
        logical_contradiction=data_dict["logical_contradiction"],
        structural_edit_count=data_dict["structural_edit_count"],
        num_docs=num_docs
    )
    
    return mcmc.get_samples()
