#!/command/with-contenv sh

# Convert one parameter to uppercase
to_uppercase() {
    echo "${1}" | tr '[:lower:]' '[:upper:]'
}

# Check if the parameter is string True/False and return it as success/failure
is_enabled() {
    _UPPER_VALUE=$(to_uppercase "${1}")
    if [ "${_UPPER_VALUE}" = "TRUE" ]; then
        return 0
    fi

    return 1
}

cd "${BACKEND_ROOT:-/var/www/redirect/backend}" || exit 1

echo "Waiting for the database to be ready"
python3 manage.py wait_for_db

echo "Running Django self-checks"
python3 manage.py check

# Run the database migrations
if is_enabled "${RUN_MIGRATIONS}"; then
    echo "Migrating database"
    python3 manage.py migrate --run-syncdb
    python3 manage.py createcachetable
fi

# Compile the translation messages
if is_enabled "${RUN_COMPILE_MESSAGES}"; then
    echo "Compiling translation messages"
    python3 manage.py compilemessages
fi

# Collect the static files
if is_enabled "${RUN_COLLECT_STATIC}"; then
    echo "Collecting static files"
    mkdir -p static
    python3 manage.py collectstatic --noinput
fi

# Create the Django Admin super user
if is_enabled "${RUN_CREATE_SUPER_USER:-False}"; then
    echo "Running the superuser seed script"

    python3 manage.py seed_superuser \
        --first_name "${DJANGO_ADMIN_FIRST_NAME}" \
        --last_name "${DJANGO_ADMIN_LAST_NAME}"
fi

if is_enabled "${RUN_SEED_GROUPS:-False}"; then
    echo "Running the test user seed script"

    python3 manage.py seed_groups
fi

# Start the session clean-up schedule
echo "Starting the session clean-up schedule that runs around 5:30 AM every day"
python3 manage.py schedule_session_cleanup
