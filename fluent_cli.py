#!/usr/bin/env python3
"""
A standalone, multi-function CLI tool for managing FluentCRM (v1.2).
Reads credentials from environment variables for security.
"""
import os
import sys
import json
import argparse
import requests
import base64
import csv

class FluentCRMClient:
    """A simple client to interact with the FluentCRM REST API."""
    def __init__(self):
        base_url = os.getenv("FLUENT_URL")
        username = os.getenv("FLUENT_USER")
        password = os.getenv("FLUENT_PASSWORD")

        if not all([base_url, username, password]):
            print("Error: Please set FLUENT_URL, FLUENT_USER, and FLUENT_PASSWORD env vars.", file=sys.stderr)
            sys.exit(1)

        self.api_url = f"{base_url.rstrip('/')}/wp-json/fluent-crm/v2"
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        self.headers = {"Authorization": f"Basic {encoded_credentials}"}

    def _request(self, method, endpoint, data=None):
        """Helper method to make API requests."""
        try:
            response = requests.request(method, f"{self.api_url}/{endpoint}", headers=self.headers, json=data)
            response.raise_for_status()
            if response.status_code == 204:
                return {"message": "Operation successful, no content returned."}
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}", file=sys.stderr)
            if e.response:
                print(f"Response Body: {e.response.text}", file=sys.stderr)
            sys.exit(1)

    # --- Contact Management ---
    def get_contact(self, email=None, contact_id=None):
        """Gets a single contact by email or ID."""
        if email:
            response = self._request("GET", f"subscribers/0?get_by_email={email}")
            return response.get('subscriber')
        elif contact_id:
            response = self._request("GET", f"subscribers/{contact_id}")
            return response.get('subscriber')
        return None

    def create_contact(self, email, first_name, last_name, tags, lists):
        """Create a contact with optional tags and lists."""
        data = {"email": email, "first_name": first_name, "last_name": last_name, "status": "subscribed"}
        if tags:
            data["tags"] = [int(t) for t in tags.split(',')]
        if lists:
            data["lists"] = [int(l) for l in lists.split(',')]
        return self._request("POST", "subscribers", data=data)

    def delete_contact(self, email=None, contact_id=None):
        """Delete a contact by email or ID."""
        contact = self.get_contact(email=email, contact_id=contact_id)
        if not contact or 'id' not in contact:
             search_term = email or contact_id
             print(f"Error: Contact '{search_term}' not found.", file=sys.stderr)
             sys.exit(1)
        
        final_contact_id = contact['id']
        print(f"Found contact ID: {final_contact_id}. Proceeding with deletion...", file=sys.stderr)
        return self._request("DELETE", f"subscribers/{final_contact_id}")

    # --- Tag & List Subscriptions ---
    def update_contact_tags(self, email, tags, append=False):
        """Update the tags for an existing contact."""
        contact = self.get_contact(email=email)
        if not contact or 'id' not in contact:
             print(f"Error: Contact with email '{email}' not found.", file=sys.stderr)
             sys.exit(1)
        
        contact_id = contact['id']
        new_tag_ids = [int(tag_id) for tag_id in tags.split(',')]
        data = {}
        if append:
            data["attach_tags"] = new_tag_ids
        else:
            existing_tag_ids = [tag['id'] for tag in contact.get('tags', [])]
            if existing_tag_ids:
                data["detach_tags"] = existing_tag_ids
            if new_tag_ids:
                data["attach_tags"] = new_tag_ids
        return self._request("PUT", f"subscribers/{contact_id}", data=data)

    def update_contact_lists(self, email, lists, append=False):
        """Update the lists for an existing contact."""
        contact = self.get_contact(email=email)
        if not contact or 'id' not in contact:
             print(f"Error: Contact with email '{email}' not found.", file=sys.stderr)
             sys.exit(1)
        
        contact_id = contact['id']
        new_list_ids = [int(list_id) for list_id in lists.split(',')]
        data = {}
        if append:
            data["attach_lists"] = new_list_ids
        else:
            existing_list_ids = [l['id'] for l in contact.get('lists', [])]
            if existing_list_ids:
                data["detach_lists"] = existing_list_ids
            if new_list_ids:
                data["attach_lists"] = new_list_ids
        return self._request("PUT", f"subscribers/{contact_id}", data=data)

    # --- Tag Management ---
    def get_tags(self):
        """Retrieve ALL tags by handling both paginated and simple list responses, then print as CSV."""
        response = self._request("GET", "tags")

        if not isinstance(response, dict) or "tags" not in response:
            print(f"Error: Unexpected API response format for tags.", file=sys.stderr)
            print(f"Response: {json.dumps(response)}", file=sys.stderr)
            return

        tags_data = response["tags"]
        all_tags = []

        if isinstance(tags_data, list):
            # It's a simple, unpaginated list of tags.
            print("Unpaginated tag list found.", file=sys.stderr)
            all_tags = tags_data
        elif isinstance(tags_data, dict) and "data" in tags_data:
            # It's a paginated response.
            print("Paginated tag response detected. Fetching all pages...", file=sys.stderr)
            all_tags.extend(tags_data.get("data", []))
            page = 2
            next_page_url = tags_data.get("next_page_url")
            while next_page_url:
                print(f"Fetching page {page} of tags...", file=sys.stderr)
                # Pass the full URL for the next page request
                endpoint = next_page_url.split('/wp-json/fluent-crm/v2/')[-1]
                paged_response = self._request("GET", endpoint)
                
                if not isinstance(paged_response, dict) or "tags" not in paged_response or "data" not in paged_response["tags"]:
                    print(f"Error: Unexpected API response format on page {page}.", file=sys.stderr)
                    break
                
                tags_page_data = paged_response["tags"]
                all_tags.extend(tags_page_data.get("data", []))
                next_page_url = tags_page_data.get("next_page_url")
                page += 1
        else:
            print(f"Error: Unrecognized format for 'tags' data.", file=sys.stderr)
            print(f"Data: {json.dumps(tags_data)}", file=sys.stderr)
            return

        if all_tags:
            fieldnames = all_tags[0].keys()
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_tags)
        else:
            print("id,title,slug,created_at,updated_at", file=sys.stdout)

    def create_tag(self, title, slug):
        """Create a new tag."""
        return self._request("POST", "tags", data={"title": title, "slug": slug})

    def delete_tag(self, tag_id):
        """Delete a tag by its ID."""
        return self._request("DELETE", f"tags/{tag_id}")

    # --- List Management ---
    def get_lists(self):
        """Retrieve ALL lists by handling both paginated and simple list responses, then print as CSV."""
        response = self._request("GET", "lists")

        if not isinstance(response, dict) or "lists" not in response:
            print(f"Error: Unexpected API response format for lists.", file=sys.stderr)
            print(f"Response: {json.dumps(response)}", file=sys.stderr)
            return

        lists_data = response["lists"]
        all_lists = []

        if isinstance(lists_data, list):
            # It's a simple, unpaginated list of lists.
            print("Unpaginated list found.", file=sys.stderr)
            all_lists = lists_data
        elif isinstance(lists_data, dict) and "data" in lists_data:
            # It's a paginated response.
            print("Paginated list response detected. Fetching all pages...", file=sys.stderr)
            all_lists.extend(lists_data.get("data", []))
            page = 2
            next_page_url = lists_data.get("next_page_url")
            while next_page_url:
                print(f"Fetching page {page} of lists...", file=sys.stderr)
                # Pass the full URL for the next page request
                endpoint = next_page_url.split('/wp-json/fluent-crm/v2/')[-1]
                paged_response = self._request("GET", endpoint)

                if not isinstance(paged_response, dict) or "lists" not in paged_response or "data" not in paged_response["lists"]:
                    print(f"Error: Unexpected API response format on page {page}.", file=sys.stderr)
                    break
                
                lists_page_data = paged_response["lists"]
                all_lists.extend(lists_page_data.get("data", []))
                next_page_url = lists_page_data.get("next_page_url")
                page += 1
        else:
            print(f"Error: Unrecognized format for 'lists' data.", file=sys.stderr)
            print(f"Data: {json.dumps(lists_data)}", file=sys.stderr)
            return

        if all_lists:
            fieldnames = all_lists[0].keys()
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_lists)
        else:
            print("id,title,slug,created_at,updated_at", file=sys.stdout)

    def create_list(self, title, slug):
        """Create a new list."""
        return self._request("POST", "lists", data={"title": title, "slug": slug})

    def update_list(self, list_id, title=None, slug=None):
        """Update an existing list's title or slug."""
        data = {}
        if title:
            data['title'] = title
        if slug:
            data['slug'] = slug
        if not data:
            print("Error: You must provide a new --title or --slug to update.", file=sys.stderr)
            sys.exit(1)
        return self._request("PUT", f"lists/{list_id}", data=data)

    def delete_list(self, list_id):
        """Delete a list by its ID."""
        return self._request("DELETE", f"lists/{list_id}")


def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="A CLI tool to manage FluentCRM (v1.2).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Contact Commands ---
    get_contact_parser = subparsers.add_parser("get-contact", help="Retrieve a contact's details.")
    get_group = get_contact_parser.add_mutually_exclusive_group(required=True)
    get_group.add_argument("--email", help="The contact's email address.")
    get_group.add_argument("--id", type=int, help="The contact's numerical ID.")

    create_contact_parser = subparsers.add_parser("create-contact", help="Create a new contact.")
    create_contact_parser.add_argument("--email", required=True)
    create_contact_parser.add_argument("--first-name", required=True)
    create_contact_parser.add_argument("--last-name", required=True)
    create_contact_parser.add_argument("--tags", help="Comma-separated list of tag IDs to attach.")
    create_contact_parser.add_argument("--lists", help="Comma-separated list of list IDs to attach.")

    delete_contact_parser = subparsers.add_parser("delete-contact", help="Delete a contact.")
    delete_group = delete_contact_parser.add_mutually_exclusive_group(required=True)
    delete_group.add_argument("--email")
    delete_group.add_argument("--id", type=int)

    update_tags_parser = subparsers.add_parser("update-contact-tags", help="Update a contact's tags.")
    update_tags_parser.add_argument("--email", required=True)
    update_tags_parser.add_argument("--tags", required=True, help="Comma-separated list of tag IDs.")
    update_tags_parser.add_argument("--append", action="store_true", help="Append tags instead of replacing.")

    update_lists_parser = subparsers.add_parser("update-contact-lists", help="Update a contact's lists.")
    update_lists_parser.add_argument("--email", required=True)
    update_lists_parser.add_argument("--lists", required=True, help="Comma-separated list of list IDs.")
    update_lists_parser.add_argument("--append", action="store_true", help="Append lists instead of replacing.")

    # --- Tag Commands ---
    subparsers.add_parser("get-tags", help="Retrieve all tags as a CSV.")
    create_tag_parser = subparsers.add_parser("create-tag", help="Create a new tag.")
    create_tag_parser.add_argument("--title", required=True)
    create_tag_parser.add_argument("--slug", required=True)
    delete_tag_parser = subparsers.add_parser("delete-tag", help="Delete a tag.")
    delete_tag_parser.add_argument("--id", required=True, type=int)

    # --- List Commands ---
    subparsers.add_parser("get-lists", help="Retrieve all lists as a CSV.")
    create_list_parser = subparsers.add_parser("create-list", help="Create a new list.")
    create_list_parser.add_argument("--title", required=True)
    create_list_parser.add_argument("--slug", required=True)
    update_list_parser = subparsers.add_parser("update-list", help="Update a list's title or slug.")
    update_list_parser.add_argument("--id", required=True, type=int)
    update_list_parser.add_argument("--title")
    update_list_parser.add_argument("--slug")
    delete_list_parser = subparsers.add_parser("delete-list", help="Delete a list.")
    delete_list_parser.add_argument("--id", required=True, type=int)

    args = parser.parse_args()
    client = FluentCRMClient()
    result = None

    # Execute command
    if args.command == "get-contact":
        result = client.get_contact(email=args.email, contact_id=args.id)
    elif args.command == "create-contact":
        result = client.create_contact(args.email, args.first_name, args.last_name, args.tags, args.lists)
    elif args.command == "delete-contact":
        result = client.delete_contact(email=args.email, contact_id=args.id)
    elif args.command == "update-contact-tags":
        result = client.update_contact_tags(args.email, args.tags, args.append)
    elif args.command == "update-contact-lists":
        result = client.update_contact_lists(args.email, args.lists, args.append)
    elif args.command == "get-tags":
        client.get_tags()
    elif args.command == "create-tag":
        result = client.create_tag(args.title, args.slug)
    elif args.command == "delete-tag":
        result = client.delete_tag(args.id)
    elif args.command == "get-lists":
        client.get_lists()
    elif args.command == "create-list":
        result = client.create_list(args.title, args.slug)
    elif args.command == "update-list":
        result = client.update_list(args.id, args.title, args.slug)
    elif args.command == "delete-list":
        result = client.delete_list(args.id)

    if result:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()