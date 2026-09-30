# Load without extra libraries to avoid permission issues
rda_path <- "C:/Users/Vivian/Desktop/Synoptics/data/raw/gospel_parallels.rda"
load(rda_path)

df <- data.frame(
  pericope_id = as.integer(gospel_parallels$No.),
  title = gospel_parallels$Pericope,
  tradition_type = "Mapped",
  mat_refs = gospel_parallels$Matthew,
  mrk_refs = gospel_parallels$Mark,
  luk_refs = gospel_parallels$Luke,
  jhn_refs = gospel_parallels$John,
  stringsAsFactors = FALSE
)

csv_path <- "C:/Users/Vivian/Desktop/Synoptics/data/raw/gospel_parallels.csv"
write.csv(df, csv_path, row.names = FALSE, na = "")
