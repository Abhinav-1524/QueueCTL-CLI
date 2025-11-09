#!/bin/bash
for t in tests/test_*.sh; do
  echo -e "\n──────────────────────────────────────"
  echo "Running: $t"
  echo "──────────────────────────────────────"
  bash "$t" || exit 1
done

echo -e "\n🎉 All tests passed successfully!"
