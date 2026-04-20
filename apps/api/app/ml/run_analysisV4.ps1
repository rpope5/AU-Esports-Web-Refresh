$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBdURldiIsInJvbGUiOiJBRE1JTiIsImlhdCI6MTc3NTYwOTc2NCwiZXhwIjoxNzc1NjE2OTY0fQ.-ncMLP97h_BlVnXYKAAAAqtw0OljSm8-GnHq4PNgt-0"

python offline_training_analysis.py `
  --api-base-url http://localhost:8000 `
  --token $token `
  --target-mode triage_positive `
  --run-logistic `
  --output-json report.json