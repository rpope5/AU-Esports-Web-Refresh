$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBdURldiIsInJvbGUiOiJBRE1JTiIsImlhdCI6MTc3NTE5Mzk2OCwiZXhwIjoxNzc1MjAxMTY4fQ.DBRNmb8YoGg2-juhuSnk8F1JNsqX7PdONkg99-rHfDY"

python offline_training_analysis.py `
  --api-base-url http://localhost:8000 `
  --token $token `
  --run-logistic `
  --output-json report.json