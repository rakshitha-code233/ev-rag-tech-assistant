# Bugfix Requirements Document

## Introduction

When a user clicks a conversation item on the Chat History page, the app navigates to the generic `/chat` route instead of loading that specific conversation's messages. The result is that the user lands on a blank EV Assistant page with no messages, making the history feature non-functional. The fix must route the user to the correct conversation and display its messages, while leaving all other navigation and new-chat flows unchanged.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user clicks a conversation item in the Chat History list THEN the system navigates to `/chat` without passing any conversation identifier

1.2 WHEN the Chat page is reached via a history item click THEN the system renders an empty chat state (EmptyState component) instead of the selected conversation's messages

### Expected Behavior (Correct)

2.1 WHEN a user clicks a conversation item in the Chat History list THEN the system SHALL navigate to a route that includes the conversation's unique identifier (e.g. `/chat/:id`)

2.2 WHEN the Chat page is loaded with a conversation identifier in the URL THEN the system SHALL fetch and display the messages belonging to that conversation

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user navigates to `/chat` without a conversation identifier THEN the system SHALL CONTINUE TO display the empty EV Assistant state ready for a new conversation

3.2 WHEN a user sends a new message in a fresh chat session THEN the system SHALL CONTINUE TO submit the message and display the assistant's response

3.3 WHEN a user navigates to the Chat History page THEN the system SHALL CONTINUE TO display the full list of past conversations with their titles and timestamps

3.4 WHEN a user searches for conversations on the History page THEN the system SHALL CONTINUE TO filter the list by the search query
