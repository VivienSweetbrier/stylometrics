# Load necessary libraries

library(dplyr)
library(tidyr)

cat("Bypassing devtools to avoid compiler errors...\n")
cat("Downloading raw dataset directly from GitHub...\n")

# Download the raw .rda data file directly
rda_path <- "C:/Users/Vivian/Desktop/Synoptics/data/raw/gospel_parallels.rda"
download.file("https://raw.githubusercontent.com/daranzolin/ggtextparallels/master/data/gospel_parallels.rda", rda_path, mode="wb")

# Load the dataset into the R environment
load(rda_path)

cat("Dataset loaded. Formatting for the Graph-Engineered Pipeline...\n")

# Format the dataset to match our Python schema:
# pericope_id, title, tradition_type, mat_refs, mrk_refs, luk_refs
df_formatted <- gospel_parallels %>%
  transmute(
    pericope_id = as.integer(No.),
    title = Pericope,
    tradition_type = "Mapped", # Default fallback
    mat_refs = Matthew,
    mrk_refs = Mark,
    luk_refs = Luke,
    jhn_refs = John
  )

csv_path <- "C:/Users/Vivian/Desktop/Synoptics/data/raw/gospel_parallels.csv"
write.csv(df_formatted, csv_path, row.names = FALSE, na = "")

cat(sprintf("✅ Successfully exported to %s!\n", csv_path))
cat("You can now run: python src/data_loader/import_parallels.py\n")

