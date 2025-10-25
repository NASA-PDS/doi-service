#!/bin/bash

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      echo "sync_dois.sh [-h|--help] [-p|--prefix <doi_prefix>] [-s|--submitter <submitter email>]"
      exit 0
      ;;
    -p|--prefix)
      PREFIX="$2"
      shift
      shift
      ;;
    -s|--submitter)
      SUBMITTER="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

if [[ -z ${PREFIX} ]]; then
  PREFIX="10.17189"
fi

if [[ -z ${SUBMITTER} ]]; then
  SUBMITTER="pds-operator@jpl.nasa.gov"
fi

echo "=================================================="
echo "Starting DOI sync for $(date)"
echo
echo "PREFIX=${PREFIX}"
echo "SUBMITTER=${SUBMITTER}"

source $HOME/pds-doi-service/bin/activate

pds-doi-init --service datacite --prefix ${PREFIX} --submitter ${SUBMITTER}

echo "Sync complete"
echo

exit 0
