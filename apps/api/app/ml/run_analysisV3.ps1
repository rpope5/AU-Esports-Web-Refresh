$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBdURldiIsInJvbGUiOiJBRE1JTiIsImlhdCI6MTc3NTU3NTE5NywiZXhwIjoxNzc1NTgyMzk3fQ.6d92rOS6yNm5AiwJ6B0MclxU0pWzhXDjrA5R-FZdR30"

python offline_training_analysis.py `
  --api-base-url http://localhost:8000 `
  --token $token `
  --limit 5000 `
  --weak-game-count 3 `
  --output-json report.json