# FluentCRM CLI v1.2 - Complete Testing Guide.

This document provides a sequential test plan to verify every single command in the FluentCRM CLI tool.

## Test Setup

### Prerequisites
- Docker installed and running.
- The `fluent-crm-cli:v1.2` image is built and available locally.
- `jq` command-line JSON processor installed (recommended for parsing results).

### Environment Setup

**1. Create `fluent.env` file:**
Create a file named `fluent.env` in your current directory. This file will store your credentials securely.
```
# Replace with your actual FluentCRM credentials
FLUENT_URL=https://your-site.com
FLUENT_USER=your-api-user
FLUENT_PASSWORD=your-api-password
```

**2. Set Other Environment Variables:**
Set the following environment variables in your terminal. These will be used by the test script.
```bash
# This is the name of the local Docker image you built
export DOCKER_IMAGE="fluent-crm-cli:v1.2"
export TIMESTAMP=$(date +%s)
```

## Accessing Built-in Documentation

The `fluent-crm-cli` Docker image includes its documentation inside the container in the `/docs/` directory.

Because the image has a default `ENTRYPOINT` that runs the Python script, you must override it to run other commands like `ls` or `cat`.

**List all documentation files:**
```bash
docker run --rm --entrypoint ls fluent-crm-cli:v1.2 /docs/
```

**View a specific documentation file:**
```bash
docker run --rm --entrypoint cat fluent-crm-cli:v1.2 /docs/README.md
```

**Copy all documentation to your local machine:**
```bash
# Create a temporary container
ID=$(docker create fluent-crm-cli:v1.2)

# Copy the /docs directory from the container to your current location
docker cp "$ID:/docs" .

# Remove the temporary container
docker rm -v "$ID"
```

## Complete Test Sequence
All commands below will use the `fluent.env` file for credentials, keeping the commands clean.

### Phase 1: Tag Management Testing

#### 1.1 Get All Existing Tags (Export to CSV)
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-tags > existing_tags_$TIMESTAMP.csv

echo "✓ Exported existing tags to existing_tags_$TIMESTAMP.csv"
echo "Tag count: $(wc -l < existing_tags_$TIMESTAMP.csv)"
```

#### 1.2 Create Multiple Test Tags
```bash
# Create Tag 1
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-tag \
    --title "Test Tag Alpha $TIMESTAMP" \
    --slug "test-tag-alpha-$TIMESTAMP"

# Create Tag 2
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-tag \
    --title "Test Tag Beta $TIMESTAMP" \
    --slug "test-tag-beta-$TIMESTAMP"

# Create Tag 3
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-tag \
    --title "Test Tag Gamma $TIMESTAMP" \
    --slug "test-tag-gamma-$TIMESTAMP"
```

#### 1.3 Get Tags Again to Find Our Test Tags
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-tags > all_tags_after_create_$TIMESTAMP.csv

# Extract our test tag IDs
TAG_ID_1=$(grep "test-tag-alpha-$TIMESTAMP" all_tags_after_create_$TIMESTAMP.csv | cut -d',' -f1)
TAG_ID_2=$(grep "test-tag-beta-$TIMESTAMP" all_tags_after_create_$TIMESTAMP.csv | cut -d',' -f1)
TAG_ID_3=$(grep "test-tag-gamma-$TIMESTAMP" all_tags_after_create_$TIMESTAMP.csv | cut -d',' -f1)

echo "Created tags with IDs: $TAG_ID_1, $TAG_ID_2, $TAG_ID_3"
```

### Phase 2: List Management Testing

#### 2.1 Get All Existing Lists
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-lists > existing_lists_$TIMESTAMP.csv

echo "✓ Exported existing lists to existing_lists_$TIMESTAMP.csv"
```

#### 2.2 Create Multiple Test Lists
```bash
# Create List 1
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-list \
    --title "Test List Primary $TIMESTAMP" \
    --slug "test-list-primary-$TIMESTAMP"

# Create List 2
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-list \
    --title "Test List Secondary $TIMESTAMP" \
    --slug "test-list-secondary-$TIMESTAMP"
```

#### 2.3 Get Lists to Find Our Test List IDs
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-lists > all_lists_after_create_$TIMESTAMP.csv

# Extract our test list IDs
LIST_ID_1=$(grep "test-list-primary-$TIMESTAMP" all_lists_after_create_$TIMESTAMP.csv | cut -d',' -f1)
LIST_ID_2=$(grep "test-list-secondary-$TIMESTAMP" all_lists_after_create_$TIMESTAMP.csv | cut -d',' -f1)

echo "Created lists with IDs: $LIST_ID_1, $LIST_ID_2"
```

#### 2.4 Update a List
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-list \
    --id "$LIST_ID_1" \
    --title "Updated Test List Primary $TIMESTAMP"
```

### Phase 3: Contact Management Testing

#### 3.1 Create Multiple Test Contacts
```bash
# Contact 1: With tags and lists
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-contact \
    --email "test.contact.1.$TIMESTAMP@example.com" \
    --first-name "Test" \
    --last-name "Contact One" \
    --tags "$TAG_ID_1,$TAG_ID_2" \
    --lists "$LIST_ID_1"

# Contact 2: With only lists
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-contact \
    --email "test.contact.2.$TIMESTAMP@example.com" \
    --first-name "Test" \
    --last-name "Contact Two" \
    --lists "$LIST_ID_2"

# Contact 3: Plain contact (no tags or lists)
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-contact \
    --email "test.contact.3.$TIMESTAMP@example.com" \
    --first-name "Test" \
    --last-name "Contact Three"
```

#### 3.2 Get Contact by Email
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact \
    --email "test.contact.1.$TIMESTAMP@example.com"
```

#### 3.3 Get Contact by ID
```bash
# First, get the contact to find its ID
CONTACT_INFO=$(docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact --email "test.contact.2.$TIMESTAMP@example.com")

# Use jq to reliably parse the ID
CONTACT_ID=$(echo "$CONTACT_INFO" | jq '.id')

# Now get by ID
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact --id "$CONTACT_ID"
```

#### 3.4 Update Contact Tags - Replace Mode
```bash
# Replace all tags with just TAG_ID_3
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-tags \
    --email "test.contact.1.$TIMESTAMP@example.com" \
    --tags "$TAG_ID_3"
```

#### 3.5 Update Contact Tags - Append Mode
```bash
# Add TAG_ID_1 back without removing TAG_ID_3
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-tags \
    --email "test.contact.1.$TIMESTAMP@example.com" \
    --tags "$TAG_ID_1" \
    --append
```

#### 3.6 Update Contact Lists - Replace Mode
```bash
# Replace all lists with LIST_ID_2
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-lists \
    --email "test.contact.1.$TIMESTAMP@example.com" \
    --lists "$LIST_ID_2"
```

#### 3.7 Update Contact Lists - Append Mode
```bash
# Add LIST_ID_1 back
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-lists \
    --email "test.contact.1.$TIMESTAMP@example.com" \
    --lists "$LIST_ID_1" \
    --append
```

### Phase 4: Deletion Testing

#### 4.1 Delete Contact by Email
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-contact \
    --email "test.contact.1.$TIMESTAMP@example.com"
```

#### 4.2 Delete Contact by ID
```bash
# Get contact 2's ID first
CONTACT_2_INFO=$(docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact --email "test.contact.2.$TIMESTAMP@example.com")
CONTACT_2_ID=$(echo "$CONTACT_2_INFO" | jq '.id')

# Delete by ID
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-contact --id "$CONTACT_2_ID"
```

#### 4.3 Delete Tags
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-tag --id "$TAG_ID_1"
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-tag --id "$TAG_ID_2"
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-tag --id "$TAG_ID_3"
```

#### 4.4 Delete Lists
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-list --id "$LIST_ID_1"
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-list --id "$LIST_ID_2"
```

#### 4.5 Cleanup Remaining Test Contact
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-contact \
    --email "test.contact.3.$TIMESTAMP@example.com"
```
