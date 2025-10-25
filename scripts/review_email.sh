#!/bin/bash

echo "=================================================="
echo "Staging: Starting DOI review email $(date)"
echo

source $HOME/pds-doi-service/bin/activate

pds-doi-cmd list --status review | mail -s 'DOI daily review on pdscloud-gamma' pdsen-doi-prod@jpl.nasa.gov

echo "DOI review email complete"
echo

exit 0
