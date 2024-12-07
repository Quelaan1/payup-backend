#!/bin/sh
# Run repair
flyway repair
# Run Flyway migrate
flyway migrate
# Check the status
flyway info
# Add any additional commands here
