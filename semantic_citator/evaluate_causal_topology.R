suppressMessages(library(dagitty))
suppressMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop(toJSON(list(error = "No JSON payload provided"), auto_unbox = TRUE))
}

payload <- fromJSON(args[1])

triples_to_dagitty_str <- function(triples_df) {
  if (is.null(triples_df) || nrow(triples_df) == 0) {
    return("dag {}")
  }
  edges <- paste(triples_df$subject, "->", triples_df$object)
  dag_str <- paste0("dag {\n", paste(edges, collapse = "\n"), "\n}")
  return(dag_str)
}

source_dag_str <- triples_to_dagitty_str(payload$source)
dest_dag_str <- triples_to_dagitty_str(payload$destination)

evaluate_causal_topology <- function(source_str, dest_str) {
  g_source <- dagitty(source_str)
  g_dest <- dagitty(dest_str)
  
  edges_source <- edges(g_source)
  edges_dest <- edges(g_dest)
  
  format_edge <- function(df) {
    if(nrow(df) == 0) return(character(0))
    paste0(df$v, df$e, df$w)
  }
  
  src_edge_set <- format_edge(edges_source)
  dst_edge_set <- format_edge(edges_dest)
  
  added_edges <- setdiff(dst_edge_set, src_edge_set)
  dropped_edges <- setdiff(src_edge_set, dst_edge_set)
  topological_edit_distance <- length(added_edges) + length(dropped_edges)
  
  reversed_count <- 0
  if (nrow(edges_source) > 0 && nrow(edges_dest) > 0) {
    src_directed <- edges_source[edges_source$e == "->", ]
    if(nrow(src_directed) > 0) {
      for (i in seq_len(nrow(src_directed))) {
        flipped <- paste0(src_directed$w[i], "->", src_directed$v[i])
        if (flipped %in% dst_edge_set) reversed_count <- reversed_count + 1
      }
    }
  }
  
  source_vars <- names(g_source)
  dest_vars <- names(g_dest)
  omitted_confounders_count <- length(setdiff(source_vars, dest_vars))
  
  list(
    topological_edit_distance = as.numeric(topological_edit_distance),
    omitted_confounders = as.integer(omitted_confounders_count),
    reversed_edges = as.integer(reversed_count)
  )
}

tryCatch({
  result <- evaluate_causal_topology(source_dag_str, dest_dag_str)
  cat(toJSON(result, auto_unbox = TRUE))
}, error = function(e) {
  error_payload <- list(
    error = "R_subprocess_failure",
    message = e$message
  )
  cat(toJSON(error_payload, auto_unbox = TRUE))
  quit(status = 1)
})
