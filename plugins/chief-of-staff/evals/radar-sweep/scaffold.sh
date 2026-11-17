#!/bin/bash
# Copy the fixture registry and sources into the run's working directory.
set -e
cp -R "$(cd "$(dirname "$0")" && pwd)/fixtures/." .
