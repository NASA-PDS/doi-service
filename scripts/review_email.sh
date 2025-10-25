#!/bin/bash

echo "=================================================="
echo "pdscloud-gamma: Starting DOI review email $(date)"
echo

source /home/pds4/pds-doi-service/bin/activate

pds-doi-cmd list --status review | mail -s 'DOI daily review on pdscloud-gamma' pdsen-operator@jpl.nasa.gov,ronald.joyner@jpl.nasa.gov

echo "DOI review email complete"
echo

exit 0
