#!/usr/bin/env bash

set -u

# Ensure normal Linux commands can be located
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

GATEWAY="http://127.0.0.1:8000"


if [ -z "${TOKEN:-}" ]; then
    echo
    echo "❌ TOKEN is not configured."
    echo "Run: ssas-login"
    echo
    exit 1
fi


test_endpoint() {
    NAME="$1"
    ENDPOINT="$2"

    TMP_FILE=$(mktemp)

    STATUS=$(curl \
        --silent \
        --show-error \
        --max-time 10 \
        --output "$TMP_FILE" \
        --write-out "%{http_code}" \
        --header "Authorization: Bearer $TOKEN" \
        "$GATEWAY$ENDPOINT"
    )

    CURL_EXIT=$?

    if [ "$CURL_EXIT" -ne 0 ]; then
        echo "❌ $NAME - CONNECTION FAILED"

        rm -f "$TMP_FILE"
        return
    fi

    if [[ "$STATUS" =~ ^2 ]]; then
        echo "✅ $NAME - HTTP $STATUS"
    else
        echo "❌ $NAME - HTTP $STATUS"
        echo "   Endpoint: $ENDPOINT"

        if [ -s "$TMP_FILE" ]; then
            echo "   Response:"
            sed 's/^/   /' "$TMP_FILE"
            echo
        fi
    fi

    rm -f "$TMP_FILE"
}


echo
echo "========================================"
echo "       SSAS INTEGRATION TEST"
echo "========================================"
echo


test_endpoint \
    "Authentication" \
    "/auth/me"


test_endpoint \
    "User Service" \
    "/users/me"


test_endpoint \
    "Dataset Service" \
    "/datasets"


test_endpoint \
    "Statistics Service" \
    "/statistics/tests"


test_endpoint \
    "Machine Learning Service" \
    "/ml/types"


test_endpoint \
    "Visualization Service" \
    "/visualizations/types"


test_endpoint \
    "Report Service" \
    "/reports"


test_endpoint \
    "Notification Service" \
    "/notifications"


test_endpoint \
    "Unread Notifications" \
    "/notifications/unread-count"


test_endpoint \
    "Admin User Statistics" \
    "/users/admin/stats"


echo
echo "========================================"
echo "        TEST COMPLETE"
echo "========================================"
echo
