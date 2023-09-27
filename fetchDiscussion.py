import requests
import json
import os
import shutil


# Your GitHub personal access token with 'repo' and 'read:discussion' scopes
access_token = ""
if access_token == "":
  print("The access_token is empty. Please set the GitHub personal access token.")
  exit()

output_folder = 'output_folder'
# Check if the directory already exists
if os.path.exists(output_folder):
    # If it exists, delete it and its contents
    print('output folder already exits, deleting output folder...')
    shutil.rmtree(output_folder)

os.makedirs(output_folder, exist_ok=True)
print('Creating output folder...')

json_file_path = 'discussions_data.json'
with open(json_file_path, 'r') as file:
    data = json.load(file)

for item in data:
    owner = item['owner']
    repository_name = item['repository_name']
    discussion_categoryId = item['discussion_categoryId']
    categoryName = item['category_name']
    export_file_name = owner + "_" + categoryName + "_github_discussions.txt"

    # Define the GraphQL query to fetch discussions with pagination
    newquery = '''
    query($repositoryOwner: String!, $repositoryName: String!, $discussionCategoryId: ID!, $cursor: String) {
      repository(owner: $repositoryOwner, name: $repositoryName) {
        discussions(first: 5, categoryId: $discussionCategoryId, after: $cursor) {
          edges {
            node {
              title
              body
              createdAt
              answerChosenAt
              url
              comments(first: 30) {
                nodes {
                  body
                  createdAt
                  replies(first: 30) {
                    nodes {
                      body
                      createdAt
                    }
                  }
                }
              }
            }
          }
          pageInfo {
            endCursor
            hasNextPage
          }
        }
      }
    }
    '''

    # GitHub GraphQL API endpoint
    url = 'https://api.github.com/graphql'

    # Initialize variables for pagination
    has_next_page = True
    end_cursor = None
    fetchedDiscussions = []

    while has_next_page:
      variables = {
        'repositoryOwner': owner,
        'repositoryName': repository_name,
        'cursor': end_cursor,
        'discussionCategoryId': discussion_categoryId
      }

      # Set up the headers with the access token
      headers = {
        'Authorization': f'Bearer {access_token}',
      }
      # Make the GraphQL API request
      response = requests.post(
        'https://api.github.com/graphql',
        json={'query': newquery, 'variables': variables},
        headers=headers,
      )
      if response.status_code == 200:
        data = response.json()
        discussion_edges = data['data']['repository']['discussions']['edges']
        fetchedDiscussions += discussion_edges
        print(f'{len(fetchedDiscussions)} discussions fetched for {categoryName} category of {owner}')
        has_next_page = data['data']['repository']['discussions']['pageInfo']['hasNextPage']
        end_cursor = data['data']['repository']['discussions']['pageInfo']['endCursor']
      else:
        print(f'Error: {response.status_code}')
        break

    # Now you have all the discussions in the `fetchedDiscussions` list
    print(f'Total numbers of discussions in category {categoryName} of {owner} is {len(fetchedDiscussions)}')
    output_file_path = os.path.join(output_folder, export_file_name)
    # Open a text file to write the discussions and comments
    with open(output_file_path, 'w', encoding='utf-8') as file:
      for discussion in fetchedDiscussions:
        file.write(f"Discussion Title: {discussion['node']['title']}\n")
        file.write(f"Discussion URL: {discussion['node']['url']}\n")
        file.write(f"Discussion Created At: {discussion['node']['createdAt']}\n")
        file.write(f"Discussion Body:\n{discussion['node']['body']}\n")
        if discussion['node']['answerChosenAt'] is None:
          file.write(f"\nIs Discussion answered: This discussion is not answered yet\n")
          file.write("\n--------------------------------------------------------------------\n\n")
        else:
          file.write(f"Is Discussion answered: Yes,This discussion is answered at- {discussion['node']['answerChosenAt']}\n")
          if 'comments' in discussion['node'] and discussion['node']['comments'] and 'nodes' in discussion['node']['comments']:
              file.write("Comments:\n")
              for comment in discussion['node']['comments']['nodes']:
                  file.write(f"-Comment Body: {comment['body']}\n")
                  file.write(f"-Comment Created At: {comment['createdAt']}\n")
                  file.write("Replies:\n")
                  if 'replies' in comment and comment['replies'] and 'nodes' in comment['replies']:
                      for reply in comment['replies']['nodes']:
                          file.write(f"-Reply Body: {reply['body']}\n")
                          file.write(f"-Reply Created At: {reply['createdAt']}\n")
                  file.write("\n--------------------------------------------------------------------\n\n")

      print(f"Data has been written to: {export_file_name} in {output_folder} folder")
      print('------------------------------------------------------------------------------------------------')