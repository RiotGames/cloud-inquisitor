#!/bin/bash -e
# Run protractor end-to-end test to verify:
# - Angular UI frontend is working
# - Backend API is running (login failure message)

# Xvfb should already be running per install_dev_dependencies.sh
# Xvfb -ac :99 -screen 0 1280x1024x16
export DISPLAY=:99

# Assumes we are running from tests directory

echo 'Updating webdriver to get chrome plugin...'
../node_modules/protractor/bin/webdriver-manager update --quiet > /dev/null

set +e
echo 'Starting protractor tests...'
# Parameters are optional: --params.auditsUrl=https://yourhost.yourdomain.com
../node_modules/protractor/bin/protractor ./protractor.conf.js --params.auditsUrl=https://localhost
test_code=$?
set -e
echo "Exiting with test result code: ${test_code}"
exit ${test_code}
