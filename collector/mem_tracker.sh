#!/bin/bash

# Infinite loop to log memory usage every millisecond
while true; do
  echo "$(date +'%Y-%m-%d %H:%M:%S.%3N') - $(free | awk '/Mem:/ {print $3}')" >> memory_usage.log
  sleep 0.001  # Log memory every millisecond
done


