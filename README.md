# FluentCRM CLI - Complete Testing Guide

This document provides a sequential test plan to verify every single command in the FluentCRM CLI tool.

## Getting Started

### Download the Docker Image

First, pull the latest FluentCRM CLI tool from Docker Hub:

```bash
docker pull cyberniolo/fluentcrm-cli-tool:latest
```

### Quick Start from Terminal

Once you have the image, you can run commands directly:

```bash
# Basic usage example
docker run --rm cyberniolo/fluentcrm-cli-tool:latest --help

# Run with environment variables
docker run --rm \
  -e FLUENT_URL="https://your-site.com" \
  -e FLUENT_USER="your-api-user" \
  -e FLUENT_PASSWORD="your-api-password" \
  cyberniolo/fluentcrm-cli-tool:latest get-tags
```

## Test Setup

### Prerequisites
- Docker installed and running
- The `cyberniolo/fluentcrm-cli-tool:latest` image downloaded from Docker Hub
- `jq` command-line JSON processor installed (recommended for parsing results)

### Environment Setup

**1. Create `fluent.env` file:**
Create a file named `fluent.env` in your current directory. This file will store your credentials securely.
```
# Replace with your actual FluentCRM credentials
FLUENT_URL=https://your-site.com
FLUENT_USER=your-api-user
FLUENT_PASSWORD=your-api-password
```

**2. Set the Docker Image Variable:**
Set the DOCKER_IMAGE environment variable in your terminal session:
```bash
# Set the Docker image to use
export DOCKER_IMAGE="cyberniolo/fluentcrm-cli-tool:latest"

# Or if using a locally built image:
# export DOCKER_IMAGE="fluent-crm-cli:local-test"
```

## Accessing Built-in Documentation

The `cyberniolo/fluentcrm-cli-tool` Docker image includes its documentation inside the container in the `/docs/` directory.

Because the image has a default `ENTRYPOINT` that runs the Python script, you must override it to run other commands like `ls` or `cat`.

**List all documentation files:**
```bash
docker run --rm --entrypoint ls cyberniolo/fluentcrm-cli-tool:latest /docs/
```

**View a specific documentation file:**
```bash
docker run --rm --entrypoint cat cyberniolo/fluentcrm-cli-tool:latest /docs/README.md
```

**Copy all documentation to your local machine:**
```bash
# Create a temporary container
ID=$(docker create cyberniolo/fluentcrm-cli-tool:latest)

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
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-tags > existing_tags.csv

echo "✓ Exported existing tags to existing_tags.csv"
echo "Tag count: $(wc -l < existing_tags.csv)"
```

#### 1.2 Create Multiple Test Tags
```bash
# Create Tag 1
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-tag \
    --title "Test Tag Alpha" \
    --slug "test-tag-alpha" \
    --description "This is the first test tag."

# Create Tag 2
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-tag \
    --title "Test Tag Beta" \
    --slug "test-tag-beta" \
    --description "This is the second test tag."

# Create Tag 3
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-tag \
    --title "Test Tag Gamma" \
    --slug "test-tag-gamma" \
    --description "This is the third test tag."
```

#### 1.3 Get Tags Again to Find Our Test Tags
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-tags > all_tags_after_create.csv

# Extract our test tag IDs
TAG_ID_1=$(grep "test-tag-alpha" all_tags_after_create.csv | cut -d',' -f1)
TAG_ID_2=$(grep "test-tag-beta" all_tags_after_create.csv | cut -d',' -f1)
TAG_ID_3=$(grep "test-tag-gamma" all_tags_after_create.csv | cut -d',' -f1)

echo "Created tags with IDs: $TAG_ID_1, $TAG_ID_2, $TAG_ID_3"
```

### Phase 2: List Management Testing

#### 2.1 Get All Existing Lists
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-lists > existing_lists.csv

echo "✓ Exported existing lists to existing_lists.csv"
```

#### 2.2 Create Multiple Test Lists
```bash
# Create List 1
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-list \
    --title "Test List Primary" \
    --slug "test-list-primary"

# Create List 2
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-list \
    --title "Test List Secondary" \
    --slug "test-list-secondary"
```

#### 2.3 Get Lists to Find Our Test List IDs
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-lists > all_lists_after_create.csv

# Extract our test list IDs
LIST_ID_1=$(grep "test-list-primary" all_lists_after_create.csv | cut -d',' -f1)
LIST_ID_2=$(grep "test-list-secondary" all_lists_after_create.csv | cut -d',' -f1)

echo "Created lists with IDs: $LIST_ID_1, $LIST_ID_2"
```

#### 2.4 Update a List
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-list \
    --id "$LIST_ID_1" \
    --title "Updated Test List Primary"
```

### Phase 3: Contact Management Testing

#### 3.1 Create Multiple Test Contacts
```bash
# Contact 1: With tags and lists
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-contact \
    --email "test.contact.1@example.com" \
    --first-name "Test" \
    --last-name "Contact One" \
    --tags "$TAG_ID_1,$TAG_ID_2" \
    --lists "$LIST_ID_1"

# Contact 2: With only lists
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-contact \
    --email "test.contact.2@example.com" \
    --first-name "Test" \
    --last-name "Contact Two" \
    --lists "$LIST_ID_2"

# Contact 3: Plain contact (no tags or lists)
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" create-contact \
    --email "test.contact.3@example.com" \
    --first-name "Test" \
    --last-name "Contact Three"
```

#### 3.2 Get Contact by Email
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact \
    --email "test.contact.1@example.com"
```

#### 3.3 Get Contact by ID
```bash
# First, get the contact to find its ID
CONTACT_INFO=$(docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact --email "test.contact.2@example.com")

# Use jq to reliably parse the ID
CONTACT_ID=$(echo "$CONTACT_INFO" | jq '.id')

# Now get by ID
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact --id "$CONTACT_ID"
```

#### 3.4 Update Contact Tags - Replace Mode
```bash
# Replace all tags with just TAG_ID_3
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-tags \
    --email "test.contact.1@example.com" \
    --tags "$TAG_ID_3"
```

#### 3.5 Update Contact Tags - Append Mode
```bash
# Add TAG_ID_1 back without removing TAG_ID_3
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-tags \
    --email "test.contact.1@example.com" \
    --tags "$TAG_ID_1" \
    --append
```

#### 3.6 Update Contact Lists - Replace Mode
```bash
# Replace all lists with LIST_ID_2
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-lists \
    --email "test.contact.1@example.com" \
    --lists "$LIST_ID_2"
```

#### 3.7 Update Contact Lists - Append Mode
```bash
# Add LIST_ID_1 back
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" update-contact-lists \
    --email "test.contact.1@example.com" \
    --lists "$LIST_ID_1" \
    --append
```

### Phase 4: Deletion Testing

#### 4.1 Delete Contact by Email
```bash
docker run --rm --env-file fluent.env "$DOCKER_IMAGE" delete-contact \
    --email "test.contact.1@example.com"
```

#### 4.2 Delete Contact by ID
```bash
# Get contact 2's ID first
CONTACT_2_INFO=$(docker run --rm --env-file fluent.env "$DOCKER_IMAGE" get-contact --email "test.contact.2@example.com")
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
    --email "test.contact.3@example.com"
```
